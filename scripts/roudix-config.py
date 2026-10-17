#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (ps: [ ps.textual ])"
"""roudix-config — add Umbriel window rules without writing Nix.

What it does
  * makes sure modules/home/umbriel-custom.nix exists (copies the .example if
    not) and imports umbriel-managed.nix;
  * lets you pick an app among the windows open right now (`umbriel windows
    --json`, i.e. the REAL app_id) or the installed .desktop apps, then choose
    output / workspace / placement / blur / opacity from menus;
  * stores the rules in modules/home/umbriel-managed.json (gitignored), which
    umbriel-managed.nix turns into window rules. It never edits your own Nix.

Run it inside your Umbriel session so the window and output lists are live:
    scripts/roudix-config.py            # TUI
    scripts/roudix-config.py --list     # print the managed rules
    scripts/roudix-config.py --bootstrap-only

Then rebuild (`rebuild`) and reload the config (Mod+Shift+R).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMPOSITOR = "umbriel"  # niri / mango later


# ───────────────────────── paths & bootstrap ─────────────────────────

def repo_root() -> Path:
    env = os.environ.get("ROUDIX_DIR")
    return Path(env).expanduser() if env else Path(__file__).resolve().parent.parent


def home_dir() -> Path:
    return repo_root() / "modules" / "home"


def custom_path() -> Path:
    return home_dir() / f"{COMPOSITOR}-custom.nix"


def managed_json_path() -> Path:
    return home_dir() / f"{COMPOSITOR}-managed.json"


IMPORT_LINE = f"  imports = [ ./{COMPOSITOR}-managed.nix ]; # added by roudix-config\n"


def bootstrap() -> list[str]:
    """Create <comp>-custom.nix from the .example if missing; make sure it
    imports <comp>-managed.nix. Returns human-readable messages."""
    msgs: list[str] = []
    custom = custom_path()
    example = custom.with_name(custom.name + ".example")

    if not custom.exists():
        if not example.exists():
            raise FileNotFoundError(f"missing {example}")
        shutil.copyfile(example, custom)
        msgs.append(f"Created {custom.name} from {example.name}")

    text = custom.read_text()
    if f"{COMPOSITOR}-managed.nix" in text:
        return msgs

    if re.search(r"^\s*imports\s*=", text, re.M):
        msgs.append(
            f"WARNING: {custom.name} already has an `imports` list — add "
            f"./{COMPOSITOR}-managed.nix to it yourself, otherwise the rules "
            "created here will not be applied."
        )
        return msgs

    # First line that is just "{" = the opening of the module body.
    m = re.search(r"^\{[ \t]*\n", text, re.M)
    if not m:
        msgs.append(
            f"WARNING: could not find the module body in {custom.name}; add "
            f"`imports = [ ./{COMPOSITOR}-managed.nix ];` yourself."
        )
        return msgs
    custom.write_text(text[: m.end()] + IMPORT_LINE + text[m.end():])
    msgs.append(f"Added the managed import to {custom.name}")
    return msgs


# ───────────────────────── managed data ─────────────────────────

def load_rules() -> list[dict]:
    p = managed_json_path()
    if not p.exists():
        return []
    try:
        return list(json.loads(p.read_text()).get("window_rule", []))
    except (json.JSONDecodeError, AttributeError):
        return []


def save_rules(rules: list[dict]) -> None:
    p = managed_json_path()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"window_rule": rules}, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(p)


# ───────────────────────── system sources ─────────────────────────

def _run_json(cmd: list[str]):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def _collect(node, key: str) -> list[dict]:
    """Dicts holding `key`, wherever they sit in the JSON (shape-tolerant)."""
    found: list[dict] = []
    if isinstance(node, dict):
        if key in node and isinstance(node[key], str):
            found.append(node)
        else:
            for v in node.values():
                found += _collect(v, key)
    elif isinstance(node, list):
        for v in node:
            found += _collect(v, key)
    return found


def list_windows() -> list[dict]:
    """Open windows: [{app_id, title}], one per app_id."""
    data = _run_json([COMPOSITOR, "windows", "--json"])
    seen: dict[str, dict] = {}
    for w in _collect(data, "app_id") if data is not None else []:
        app_id = w.get("app_id", "")
        if app_id and app_id not in seen:
            seen[app_id] = {"app_id": app_id, "title": w.get("title", "")}
    return list(seen.values())


def list_outputs() -> list[str]:
    data = _run_json([COMPOSITOR, "outputs", "--json"])
    names: list[str] = []
    for o in _collect(data, "name") if data is not None else []:
        if o["name"] not in names:
            names.append(o["name"])
    return names


def _desktop_dirs() -> list[Path]:
    dirs = []
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    dirs.append(Path(data_home) / "applications")
    for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":"):
        if d:
            dirs.append(Path(d) / "applications")
    dirs += [
        Path("/run/current-system/sw/share/applications"),
        Path.home() / ".nix-profile/share/applications",
        Path("/etc/profiles/per-user") / os.environ.get("USER", "") / "share/applications",
    ]
    out, seen = [], set()
    for d in dirs:
        if d.is_dir() and d.resolve() not in seen:
            seen.add(d.resolve())
            out.append(d)
    return out


def list_desktop_apps() -> list[dict]:
    """Installed apps: [{name, app_id}]. The guessed app_id is StartupWMClass
    or the .desktop file name — it is only a hint (Xwayland apps, for
    instance, expose their X11 class), so open windows are the better source."""
    apps: dict[str, dict] = {}
    for d in _desktop_dirs():
        for f in sorted(d.glob("*.desktop")):
            entry: dict[str, str] = {}
            in_entry = False
            try:
                lines = f.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            for line in lines:
                s = line.strip()
                if s.startswith("["):
                    in_entry = s == "[Desktop Entry]"
                elif in_entry and "=" in s and not s.startswith("#"):
                    k, v = s.split("=", 1)
                    entry.setdefault(k, v)
            if entry.get("Type") != "Application" or entry.get("NoDisplay", "").lower() == "true":
                continue
            app_id = entry.get("StartupWMClass") or f.stem
            apps.setdefault(app_id, {"name": entry.get("Name", f.stem), "app_id": app_id})
    return sorted(apps.values(), key=lambda a: a["name"].lower())


# ───────────────────────── rule building ─────────────────────────

_REGEX_SPECIAL = set(".^$*+?()[]{}|\\")


def exact_pattern(text: str) -> str:
    """app_id -> anchored ECMAScript regex (escapes only what must be)."""
    return "^" + "".join("\\" + c if c in _REGEX_SPECIAL else c for c in text) + "$"


PLACEMENTS = {
    "Flottante": "default_floating",
    "Maximisée": "default_maximize",
    "Plein écran": "default_fullscreen",
}


def build_rule(app_id: str, title: str = "", output: str | None = None,
               workspace: int | None = None, placement: str | None = None,
               blur: bool | None = None, opacity: float | None = None) -> dict:
    match: dict = {}
    if app_id:
        match["app_id"] = app_id
    if title:
        match["title"] = title
    if not match:
        raise ValueError("app_id or title required")
    rule: dict = {"match": match}
    if output:
        rule["default_output"] = output
    if workspace is not None:
        rule["default_workspace"] = workspace
    if placement:
        rule[PLACEMENTS[placement]] = True
    if blur is not None:
        rule["blur"] = blur
    if opacity is not None:
        if not 0.0 <= opacity <= 1.0:
            raise ValueError("opacity must be between 0 and 1")
        rule["opacity"] = opacity
    if len(rule) == 1:
        raise ValueError("choose at least one setting")
    return rule


def rule_to_toml(rule: dict) -> str:
    """Preview of what ends up in umbriel's TOML."""
    def val(v):
        return "true" if v is True else "false" if v is False else json.dumps(v, ensure_ascii=False)
    lines = ["[[window_rule]]"]
    for k, v in rule["match"].items():
        lines.append(f"match.{k} = {val(v)}")
    for k, v in rule.items():
        if k != "match":
            lines.append(f"{k} = {val(v)}")
    return "\n".join(lines)


def rule_summary(rule: dict) -> str:
    return ", ".join(f"{k.removeprefix('default_')}={v}" for k, v in rule.items() if k != "match")


# ───────────────────────── TUI ─────────────────────────

def make_app():
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.screen import ModalScreen
        from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Select, Static
    except ImportError:
        sys.exit("textual is missing — run this script directly (nix-shell shebang) "
                 "or: nix-shell -p 'python3.withPackages (ps: [ps.textual])'")

    BLANK = getattr(Select, "NULL", None) or getattr(Select, "BLANK")

    def chosen(sel: "Select"):
        v = sel.value
        return None if v is BLANK or v is None else v

    class AddRule(ModalScreen):
        CSS = """
        AddRule { align: center middle; }
        #box { width: 90; max-width: 96%; height: 96%; border: round $accent;
               background: $surface; padding: 0 2; }
        #form { height: 1fr; }
        #form Label { margin-top: 1; }
        #preview { height: auto; max-height: 9; margin-top: 1; border: round $primary; padding: 0 1; }
        #buttons { height: auto; margin-top: 1; }
        #buttons Button { margin-right: 2; }
        #error { color: $error; }
        """

        BINDINGS = [("ctrl+s", "save", "Enregistrer"), ("escape", "cancel", "Annuler")]

        def __init__(self, windows, apps, outputs):
            super().__init__()
            self.windows, self.apps, self.outputs = windows, apps, outputs

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
              yield Label("Nouvelle règle de fenêtre — Ctrl+S enregistrer · Échap annuler", id="title")
              with VerticalScroll(id="form"):
                  yield Label(f"Fenêtre ouverte ({len(self.windows)}) — app_id réel")
                  yield Select([(f"{w['app_id']} — {w['title'][:45]}", w["app_id"]) for w in self.windows],
                               id="win", prompt="(aucune)", allow_blank=True)
                  yield Label(f"App installée ({len(self.apps)}) — app_id deviné")
                  yield Select([(f"{a['name']} ({a['app_id']})", a["app_id"]) for a in self.apps],
                               id="app", prompt="(aucune)", allow_blank=True)
                  yield Label("app_id (regex — rempli en ^…$ quand tu choisis une fenêtre ou une app)")
                  yield Input(id="app_id", placeholder="ex. ^obs$")
                  yield Label("Titre (regex, optionnel)")
                  yield Input(id="title_re", placeholder="ex. Picture-in-Picture")
                  yield Label("Écran")
                  yield Select([(o, o) for o in self.outputs], id="output", prompt="(inchangé)", allow_blank=True)
                  yield Label("Workspace")
                  yield Select([(str(i), i) for i in range(1, 11)], id="ws", prompt="(inchangé)", allow_blank=True)
                  yield Label("Placement")
                  yield Select([(k, k) for k in PLACEMENTS], id="place", prompt="(inchangé)", allow_blank=True)
                  yield Label("Blur")
                  yield Select([("Activé", True), ("Désactivé", False)], id="blur", prompt="(inchangé)", allow_blank=True)
                  yield Label("Opacité (0 à 1, optionnel)")
                  yield Input(id="opacity", placeholder="ex. 0.9")
              yield Static("", id="preview")
              yield Static("", id="error")
              with Horizontal(id="buttons"):
                  yield Button("Enregistrer", variant="success", id="save")
                  yield Button("Annuler", id="cancel")

        def on_select_changed(self, event: Select.Changed) -> None:
            v = chosen(event.select)
            if event.select.id in ("win", "app") and v:
                self.query_one("#app_id", Input).value = exact_pattern(v)
            self.refresh_preview()

        def on_input_changed(self, event: Input.Changed) -> None:
            self.refresh_preview()

        def collect(self) -> dict:
            op = self.query_one("#opacity", Input).value.strip()
            return build_rule(
                self.query_one("#app_id", Input).value.strip(),
                self.query_one("#title_re", Input).value.strip(),
                chosen(self.query_one("#output", Select)),
                chosen(self.query_one("#ws", Select)),
                chosen(self.query_one("#place", Select)),
                chosen(self.query_one("#blur", Select)),
                float(op) if op else None,
            )

        def refresh_preview(self) -> None:
            prev, err = self.query_one("#preview", Static), self.query_one("#error", Static)
            try:
                prev.update(rule_to_toml(self.collect()))
                err.update("")
            except ValueError as e:
                prev.update("")
                err.update(str(e))

        def action_cancel(self) -> None:
            self.dismiss(None)

        def action_save(self) -> None:
            try:
                self.dismiss(self.collect())
            except ValueError as e:
                self.query_one("#error", Static).update(str(e))

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "cancel":
                self.action_cancel()
            else:
                self.action_save()

    class ConfigApp(App):
        TITLE = "roudix-config"
        SUB_TITLE = "Umbriel — règles de fenêtres"
        BINDINGS = [("a", "add", "Ajouter"), ("d", "delete", "Supprimer"), ("q", "quit", "Quitter")]
        CSS = "#hint { margin: 1 2; color: $text-muted; } #status { margin: 0 2; }"

        def __init__(self, messages: list[str]):
            super().__init__()
            self.messages = messages
            self.rules = load_rules()

        def compose(self) -> ComposeResult:
            yield Header()
            yield DataTable(id="table", cursor_type="row")
            yield Static("", id="status")
            yield Static(
                "a = ajouter · d = supprimer · puis `rebuild` et Mod+Shift+R pour appliquer.\n"
                f"Données : {managed_json_path()}", id="hint")
            yield Footer()

        def on_mount(self) -> None:
            t = self.query_one(DataTable)
            t.add_columns("app_id", "titre", "réglages")
            self.render_rules()
            self.query_one("#status", Static).update("\n".join(self.messages))

        def render_rules(self) -> None:
            t = self.query_one(DataTable)
            t.clear()
            for r in self.rules:
                t.add_row(r["match"].get("app_id", ""), r["match"].get("title", ""), rule_summary(r))

        def action_add(self) -> None:
            def done(rule):
                if rule:
                    self.rules.append(rule)
                    save_rules(self.rules)
                    self.render_rules()
                    self.query_one("#status", Static).update("Règle enregistrée — pense à rebuild.")
            self.push_screen(AddRule(list_windows(), list_desktop_apps(), list_outputs()), done)

        def action_delete(self) -> None:
            t = self.query_one(DataTable)
            if self.rules and t.cursor_row is not None and 0 <= t.cursor_row < len(self.rules):
                del self.rules[t.cursor_row]
                save_rules(self.rules)
                self.render_rules()

    return ConfigApp(bootstrap())


def run_tui() -> None:
    make_app().run()


# ───────────────────────── entry point ─────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Add Umbriel window rules without writing Nix.")
    ap.add_argument("--list", action="store_true", help="print the managed rules and exit")
    ap.add_argument("--bootstrap-only", action="store_true",
                    help="only create umbriel-custom.nix / wire the import, then exit")
    args = ap.parse_args()

    if args.list:
        for r in load_rules():
            print(rule_to_toml(r), end="\n\n")
        return
    if args.bootstrap_only:
        for m in bootstrap() or ["Nothing to do."]:
            print(m)
        return
    run_tui()


if __name__ == "__main__":
    main()

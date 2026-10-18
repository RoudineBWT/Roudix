#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (ps: [ ps.textual ])"
"""roudix-config — configure Umbriel from a menu instead of writing Nix.

Everything it manages lives in ONE marked block inside your own
modules/home/umbriel-custom.nix (gitignored; copied from the .example if it
doesn't exist yet). The block is readable and the tool reads it back, so you can
add, edit or remove what it wrote earlier; everything outside the block is
yours and is never touched (the "Mon -custom.nix" tab edits the whole file).

Tabs
  * Règles de fenêtres : pick an app (open now / seen before / installed) and
    set output, workspace, placement, blur, opacity.
  * Écrans & workspaces : resolution, scale, rotation, workspace names.
  * Raccourcis : change, add, remove keybinds (starts from your live config).
  * Mon -custom.nix : the file itself, with a syntax check on save.

Only available when roudix.desktop.type is a compositor it supports (not on
GNOME / KDE / Cinnamon).

    scripts/roudix-config.py            # TUI (run it inside your session)
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


# ───────────────────────── paths & -custom.nix block ─────────────────────────
#
# Everything the tool manages lives in ONE marked block inside the user's own
# modules/home/umbriel-custom.nix (gitignored). The block is an inline module
# inside `imports`, so it never clashes with attributes the user wrote by hand.
# The tool reads its state back from that block; what is outside it is never
# touched (the "Mon -custom.nix" tab lets you edit all of it).

def repo_root() -> Path:
    env = os.environ.get("ROUDIX_DIR")
    return Path(env).expanduser() if env else Path(__file__).resolve().parent.parent


def home_dir() -> Path:
    return repo_root() / "modules" / "home"


def custom_path() -> Path:
    return home_dir() / f"{COMPOSITOR}-custom.nix"


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "roudix-config"


BEGIN = "# >>> roudix-config >>>"
END = "# <<< roudix-config <<<"

BLOCK_TEMPLATE = """\
    {begin} généré par scripts/roudix-config.py — modifie-le via l'app
    ({{ lib, ... }}:
      let
        data = builtins.fromJSON ''
{json}
        '';
        ov = data.overrides or {{ }};
      in
      {{
        # window_rule: appended AFTER the repo's rules (Umbriel applies the last match).
        # overrides.output: per-output keys replacing the repo's (mkForce per leaf).
        # overrides.keybinds: the COMPLETE table replacing the repo's one.
        programs.umbriel.settings = lib.mkMerge [
          (lib.mkAfter {{ window_rule = data.window_rule or [ ]; }})
          (lib.optionalAttrs (ov ? output) {{
            output = lib.mapAttrsRecursive (_: lib.mkForce) ov.output;
          }})
          (lib.optionalAttrs (ov ? keybinds) {{ keybinds = lib.mkForce ov.keybinds; }})
        ];
      }})
    {end}
"""


def nix_escape(s: str) -> str:
    """Escape text for a Nix indented string ('' ... '')."""
    return s.replace("''", "'''").replace("${", "''${")


def nix_unescape(s: str) -> str:
    return re.sub(r"'''|''\$\{", lambda m: "''" if m.group(0) == "'''" else "${", s)


def render_block(data: dict) -> str:
    js = nix_escape(json.dumps(data, indent=2, ensure_ascii=False))
    return BLOCK_TEMPLATE.format(begin=BEGIN, end=END, json=js)


_BLOCK_RE = re.compile(r"^[ \t]*" + re.escape(BEGIN) + r".*?^[ \t]*" + re.escape(END) + r"[^\n]*\n?",
                       re.S | re.M)
_JSON_RE = re.compile(r"fromJSON ''\n(.*?)\n[ \t]*'';", re.S)


def parse_block(text: str) -> dict | None:
    m = _BLOCK_RE.search(text)
    if not m:
        return None
    j = _JSON_RE.search(m.group(0))
    if not j:
        return None
    try:
        data = json.loads(nix_unescape(j.group(1)))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def splice_block(text: str, block: str | None) -> str:
    """Replace / insert / remove the managed block. Inserts into an existing
    `imports = [` list, or creates one right after the module's opening `{`."""
    if _BLOCK_RE.search(text):
        return _BLOCK_RE.sub(lambda _m: block or "", text, count=1)
    if block is None:
        return text
    m = re.search(r"^[ \t]*imports\s*=\s*\[", text, re.M)
    if m:
        return text[: m.end()] + "\n" + block.rstrip("\n") + "\n" + text[m.end():]
    m = re.search(r"^\{[ \t]*\n", text, re.M)
    if not m:
        raise ValueError(f"module body not found in {custom_path().name}")
    return text[: m.end()] + "  imports = [\n" + block + "  ];\n" + text[m.end():]


def bootstrap() -> list[str]:
    """Make sure <comp>-custom.nix exists (copied from the .example if not) and
    migrate what the previous version stored in umbriel-managed.json."""
    msgs: list[str] = []
    custom = custom_path()
    example = custom.with_name(custom.name + ".example")

    if not custom.exists():
        if not example.exists():
            raise FileNotFoundError(f"missing {example}")
        shutil.copyfile(example, custom)
        msgs.append(f"Created {custom.name} from {example.name}")

    text = custom.read_text()
    # v2 imported a separate umbriel-managed.nix from the custom file: drop that.
    cleaned = re.sub(r"^[ \t]*imports = \[ \./umbriel-managed\.nix \];[^\n]*\n", "", text, flags=re.M)
    if cleaned != text:
        text = cleaned
        custom.write_text(text)
        msgs.append("Removed the old umbriel-managed.nix import (no longer used)")
    elif "umbriel-managed.nix" in text:
        msgs.append("NOTE: umbriel-custom.nix still mentions umbriel-managed.nix — remove it by hand, "
                    "that file is obsolete.")

    old = home_dir() / f"{COMPOSITOR}-managed.json"
    if old.exists():
        try:
            legacy = json.loads(old.read_text())
        except json.JSONDecodeError:
            legacy = {}
        if parse_block(text) is None:
            data = {k: legacy[k] for k in ("window_rule", "overrides") if legacy.get(k)}
            if data:
                save_data(data)
                msgs.append(f"Moved your rules/overrides from {old.name} into {custom.name}")
        seen = legacy.get("seen")
        if isinstance(seen, dict) and seen:
            merged = {**load_seen(), **seen}
            _save_seen(merged)
        old.rename(old.with_name(old.name + ".migrated"))
    return msgs


# ───────────────────────── managed data ─────────────────────────

def load_data() -> dict:
    try:
        return parse_block(custom_path().read_text()) or {}
    except OSError:
        return {}


def save_data(data: dict) -> None:
    data = {k: v for k, v in data.items() if v}
    custom = custom_path()
    text = custom.read_text()
    new = splice_block(text, render_block(data) if data else None)
    if new != text:
        tmp = custom.with_name(custom.name + ".tmp")
        tmp.write_text(new)
        tmp.replace(custom)


def load_rules() -> list[dict]:
    return list(load_data().get("window_rule", []))


def save_rules(rules: list[dict]) -> None:
    data = load_data()
    data["window_rule"] = rules
    save_data(data)


def _seen_path() -> Path:
    return state_dir() / "seen.json"


def load_seen() -> dict[str, str]:
    """app_id -> last title for every window ever seen open by this tool (kept
    outside -custom.nix: it's a cache, not configuration)."""
    try:
        seen = json.loads(_seen_path().read_text())
        return seen if isinstance(seen, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_seen(seen: dict) -> None:
    p = _seen_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(list(seen.items())[-300:]), indent=2, ensure_ascii=False) + "\n")


def remember_windows(windows: list[dict]) -> None:
    if not windows:
        return
    seen = load_seen()
    changed = False
    for w in windows:
        if seen.get(w["app_id"]) != w["title"]:
            seen[w["app_id"]] = w["title"]
            changed = True
    if changed:
        _save_seen(seen)


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
    """Installed apps: [{name, candidates}]. The real app_id of an app that has
    never been opened here is unknown: candidates are StartupWMClass, the
    .desktop file name and the executable name (plus lowercase variants).
    Xwayland apps expose their X11 class instead, so the guess can miss."""
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
            exec_bin = ""
            if entry.get("Exec"):
                parts = [t for t in entry["Exec"].split() if not t.startswith("%") and "=" not in t.split("/")[-1]]
                exec_bin = Path(parts[0]).name if parts else ""
            cands: list[str] = []
            for c in (entry.get("StartupWMClass"), f.stem, exec_bin):
                for v in (c, c.lower() if c else c):
                    if v and v not in cands:
                        cands.append(v)
            apps.setdefault(cands[0], {"name": entry.get("Name", f.stem), "candidates": cands})
    return sorted(apps.values(), key=lambda a: a["name"].lower())


# ───────────────────────── rule building ─────────────────────────

_REGEX_SPECIAL = set(".^$*+?()[]{}|\\")


def exact_pattern(text: str) -> str:
    """app_id -> anchored ECMAScript regex (escapes only what must be)."""
    return "^" + "".join("\\" + c if c in _REGEX_SPECIAL else c for c in text) + "$"


def pattern_for(candidates: list[str]) -> str:
    if len(candidates) == 1:
        return exact_pattern(candidates[0])
    return "^(" + "|".join(exact_pattern(c)[1:-1] for c in candidates) + ")$"


def build_sources(windows: list[dict], seen: dict[str, str], apps: list[dict]) -> list[dict]:
    """One searchable list: open windows, then previously seen, then installed.
    Each item: {kind, label, pattern}."""
    items: list[dict] = []
    known: set[str] = set()
    for w in windows:
        items.append({"kind": "open", "label": f"● {w['app_id']} — {w['title'][:50]}",
                      "pattern": exact_pattern(w["app_id"])})
        known.add(w["app_id"])
    for app_id, title in sorted(seen.items()):
        if app_id not in known:
            items.append({"kind": "seen", "label": f"○ {app_id} — {title[:50]} (vu ouvert avant)",
                          "pattern": exact_pattern(app_id)})
            known.add(app_id)
    for a in apps:
        if known.isdisjoint(a["candidates"]):
            items.append({"kind": "installed", "label": f"  {a['name']} (installée, app_id deviné)",
                          "pattern": pattern_for(a["candidates"])})
    return items


def filter_sources(items: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    return [i for i in items if q in i["label"].lower()] if q else items


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


# ───────────────────────── availability (which compositor?) ─────────────────────────

SUPPORTED = {"umbriel"}
NATIVE_DE = {"gnome", "kde", "cinnamon"}
TRANSFORMS = ["normal", "90", "180", "270", "flipped", "flipped-90", "flipped-180", "flipped-270"]


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def desktop_type() -> str | None:
    """roudix.desktop.type, written by Home-Manager to ~/.config/roudix/desktop-type.
    Falls back to the running session name before the first rebuild."""
    f = config_home() / "roudix" / "desktop-type"
    try:
        v = f.read_text().strip().lower()
        if v:
            return v
    except OSError:
        pass
    sess = (os.environ.get("XDG_CURRENT_DESKTOP", "") + ":" + os.environ.get("XDG_SESSION_DESKTOP", "")).lower()
    for name, needle in (("umbriel", "umbriel"), ("niri", "niri"), ("hyprland", "hyprland"),
                         ("mangowc", "mango"), ("gnome", "gnome"), ("kde", "kde"),
                         ("kde", "plasma"), ("cinnamon", "cinnamon")):
        if needle in sess:
            return name
    return None


def availability() -> str | None:
    """None when the tool can run, else the reason it can't."""
    t = desktop_type()
    if t in SUPPORTED:
        return None
    if t in NATIVE_DE:
        return (f"roudix-config n'est pas disponible sur {t} : utilise ses réglages natifs "
                "(Paramètres système).")
    if t:
        return f"roudix-config ne gère pas encore {t} (pour l'instant : {', '.join(sorted(SUPPORTED))})."
    return ("Impossible de déterminer le bureau (roudix.desktop.type). Fais un rebuild pour que "
            "~/.config/roudix/desktop-type soit créé.")


# ───────────────────────── live config & overrides ─────────────────────────

def load_live() -> dict:
    """The config Umbriel actually runs with (generated by Home-Manager)."""
    try:
        import tomllib
        return tomllib.loads((config_home() / "umbriel" / "config.toml").read_text())
    except (OSError, ValueError, ImportError):
        return {}


def get_overrides(data: dict | None = None) -> dict:
    ov = (data if data is not None else load_data()).get("overrides", {})
    return ov if isinstance(ov, dict) else {}


def effective_outputs(live: dict, ov: dict) -> dict[str, dict]:
    out = {n: dict(c) for n, c in (live.get("output") or {}).items() if isinstance(c, dict)}
    for n, c in (ov.get("output") or {}).items():
        out.setdefault(n, {}).update(c)
    return out


def effective_binds(live: dict, ov: dict) -> dict:
    if isinstance(ov.get("keybinds"), dict):
        return json.loads(json.dumps(ov["keybinds"]))
    return json.loads(json.dumps(live.get("keybinds") or {}))


def bind_action(v) -> str:
    return v if isinstance(v, str) else str(v.get("action", "")) if isinstance(v, dict) else str(v)


def set_bind(table: dict, key: str, action: str, old_key: str | None = None) -> dict:
    """Return a new table with `key` bound to `action` (moving it from old_key)."""
    key, action = key.strip(), action.strip()
    if not key or not action:
        raise ValueError("raccourci et action requis")
    new = dict(table)
    prev = new.pop(old_key, None) if old_key else None
    if prev is None:
        prev = table.get(key)
    if isinstance(prev, dict):
        value = dict(prev)
        value["action"] = action
    else:
        value = action
    new[key] = value
    return new


def save_output_override(name: str, changes: dict) -> None:
    data = load_data()
    ov = data.setdefault("overrides", {})
    cur = ov.setdefault("output", {}).setdefault(name, {})
    cur.update(changes)
    if not cur:
        ov["output"].pop(name, None)
    save_data(data)


def reset_override(section: str, name: str | None = None) -> None:
    data = load_data()
    ov = data.get("overrides", {})
    if section == "output" and name:
        ov.get("output", {}).pop(name, None)
        if not ov.get("output"):
            ov.pop("output", None)
    else:
        ov.pop(section, None)
    if not ov:
        data.pop("overrides", None)
    save_data(data)


def save_binds_override(table: dict) -> None:
    data = load_data()
    data.setdefault("overrides", {})["keybinds"] = table
    save_data(data)


def list_outputs_full() -> dict[str, dict]:
    """name -> {modes: ["2560x1440@240.000", ...], current: str|None}"""
    data = _run_json([COMPOSITOR, "outputs", "--json"])
    res: dict[str, dict] = {}
    for o in _collect(data, "name") if data is not None else []:
        modes, current = [], None
        for m in o.get("modes", []) or []:
            if not isinstance(m, dict) or "width" not in m:
                continue
            s = f"{m['width']}x{m['height']}@{m.get('refresh_mhz', 0) / 1000:.3f}"
            if s not in modes:
                modes.append(s)
            if m.get("current"):
                current = s
        res[o["name"]] = {"modes": modes, "current": current}
    return res


def nix_parse_check(text: str) -> tuple[bool, str]:
    """(ok, message). Uses `nix-instantiate --parse`; unchecked if nix is absent."""
    exe = shutil.which("nix-instantiate")
    if not exe:
        return True, "syntaxe non vérifiée, nix-instantiate introuvable"
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".nix", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        r = subprocess.run([exe, "--parse", path], capture_output=True, text=True, timeout=15)
    finally:
        os.unlink(path)
    if r.returncode == 0:
        return True, "syntaxe Nix valide"
    return False, (r.stderr.strip().splitlines() or ["erreur de syntaxe"])[-1]


# ───────────────────────── TUI ─────────────────────────

def make_app():
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.screen import ModalScreen
        from textual.widgets import (Button, DataTable, Footer, Header, Input, Label, OptionList,
                                     Select, Static, TabbedContent, TabPane, TextArea)
        from textual.widgets.option_list import Option
    except ImportError:
        sys.exit("textual is missing — run this script directly (nix-shell shebang) "
                 "or: nix-shell -p 'python3.withPackages (ps: [ps.textual])'")

    BLANK = getattr(Select, "NULL", None) or getattr(Select, "BLANK")

    def chosen(sel):
        v = sel.value
        return None if v is BLANK or v is None else v

    def put(sel, value):
        try:
            sel.value = value
        except Exception:
            pass

    MODAL_CSS = """
    #box { width: 90; max-width: 96%; height: 96%; border: round $accent;
           background: $surface; padding: 0 2; }
    #form { height: 1fr; }
    #form Label { margin-top: 1; }
    #preview { height: auto; max-height: 9; margin-top: 1; border: round $primary; padding: 0 1; }
    #buttons { height: auto; margin-top: 1; }
    #buttons Button { margin-right: 2; }
    #error { color: $error; }
    """

    class Modal(ModalScreen):
        """Shared save/cancel plumbing. Subclasses implement result() -> value."""
        CSS = "Modal { align: center middle; }\n" + MODAL_CSS
        BINDINGS = [("ctrl+s", "save", "Enregistrer"), ("escape", "cancel", "Annuler")]

        def result(self):
            raise NotImplementedError

        def action_cancel(self) -> None:
            self.dismiss(None)

        def action_save(self) -> None:
            try:
                self.dismiss(self.result())
            except ValueError as e:
                self.query_one("#error", Static).update(str(e))

        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.action_cancel() if event.button.id == "cancel" else self.action_save()

        def footer_widgets(self):
            yield Static("", id="error")
            with Horizontal(id="buttons"):
                yield Button("Enregistrer", variant="success", id="save")
                yield Button("Annuler", id="cancel")

    # ── window rules ──
    class RuleForm(Modal):
        def __init__(self, sources, outputs, initial: dict | None = None):
            super().__init__()
            self.sources, self.outputs, self.initial = sources, outputs, initial
            self.shown = list(sources)

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
                yield Label("Règle de fenêtre — Ctrl+S enregistrer · Échap annuler")
                with VerticalScroll(id="form"):
                    yield Label("App — ● ouverte maintenant · ○ déjà vue ouverte · sans symbole = installée")
                    yield Input(id="search", placeholder="Rechercher une app…")
                    yield OptionList(*[Option(i["label"]) for i in self.sources], id="sources")
                    yield Label("app_id (regex — rempli en ^…$ quand tu choisis une app)")
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
                yield from self.footer_widgets()

        def on_mount(self) -> None:
            r = self.initial
            if not r:
                return
            self.query_one("#app_id", Input).value = r["match"].get("app_id", "")
            self.query_one("#title_re", Input).value = r["match"].get("title", "")
            put(self.query_one("#output", Select), r.get("default_output", BLANK))
            put(self.query_one("#ws", Select), r.get("default_workspace", BLANK))
            for label, key in PLACEMENTS.items():
                if r.get(key):
                    put(self.query_one("#place", Select), label)
            if "blur" in r:
                put(self.query_one("#blur", Select), r["blur"])
            if "opacity" in r:
                self.query_one("#opacity", Input).value = str(r["opacity"])
            self.refresh_preview()

        def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
            if 0 <= event.option_index < len(self.shown):
                self.query_one("#app_id", Input).value = self.shown[event.option_index]["pattern"]
                self.query_one("#output", Select).focus()
            self.refresh_preview()

        def on_select_changed(self, event) -> None:
            self.refresh_preview()

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "search":
                self.shown = filter_sources(self.sources, event.value)
                ol = self.query_one("#sources", OptionList)
                ol.clear_options()
                ol.add_options([Option(i["label"]) for i in self.shown])
                return
            self.refresh_preview()

        def result(self) -> dict:
            op = self.query_one("#opacity", Input).value.strip()
            try:
                opacity = float(op) if op else None
            except ValueError:
                raise ValueError("opacité : nombre entre 0 et 1")
            rule = build_rule(
                self.query_one("#app_id", Input).value.strip(),
                self.query_one("#title_re", Input).value.strip(),
                chosen(self.query_one("#output", Select)),
                chosen(self.query_one("#ws", Select)),
                chosen(self.query_one("#place", Select)),
                chosen(self.query_one("#blur", Select)),
                opacity,
            )
            return rule

        def refresh_preview(self) -> None:
            prev, err = self.query_one("#preview", Static), self.query_one("#error", Static)
            try:
                prev.update(rule_to_toml(self.result()))
                err.update("")
            except ValueError as e:
                prev.update("")
                err.update(str(e))

    # ── outputs ──
    class OutputForm(Modal):
        def __init__(self, name: str | None, names: list[str], cfg: dict, live: dict[str, dict]):
            super().__init__()
            self.name0, self.names, self.cfg, self.live = name, names, cfg, live

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
                yield Label("Écran — Ctrl+S enregistrer · Échap annuler")
                with VerticalScroll(id="form"):
                    yield Label("Sortie")
                    yield Select([(n, n) for n in self.names], id="name", allow_blank=False,
                                 value=self.name0 or (self.names[0] if self.names else BLANK))
                    yield Label("Résolution / fréquence (modes détectés si Umbriel tourne)")
                    yield Select([], id="modes", prompt="(choisir un mode)", allow_blank=True)
                    yield Input(id="mode", placeholder='ex. 2560x1440@240.000')
                    yield Label("Échelle (0.25 à 4)")
                    yield Input(id="scale", placeholder="ex. 1 ou 1.25")
                    yield Label("Rotation")
                    yield Select([(t, t) for t in TRANSFORMS], id="transform", prompt="(inchangé)", allow_blank=True)
                    yield Label("Noms des workspaces de cet écran, séparés par des espaces")
                    yield Input(id="workspaces", placeholder="ex.  web code chat   (ou des icônes)")
                    yield Static("Évite un nom purement numérique présent sur un seul écran : "
                                 "Umbriel le traite comme unique et Mod+N sauterait toujours vers cet écran.")
                yield from self.footer_widgets()

        def on_mount(self) -> None:
            self.load_for(self.query_one("#name", Select).value)

        def load_for(self, name) -> None:
            cfg = self.cfg.get(name, {}) if name else {}
            info = self.live.get(name, {}) if name else {}
            modes = self.query_one("#modes", Select)
            modes.set_options([(m + (" (actuel)" if m == info.get("current") else ""), m)
                               for m in info.get("modes", [])])
            self.query_one("#mode", Input).value = str(cfg.get("mode", ""))
            self.query_one("#scale", Input).value = "" if "scale" not in cfg else str(cfg["scale"])
            put(self.query_one("#transform", Select), cfg.get("transform", BLANK))
            ws = cfg.get("workspaces")
            self.query_one("#workspaces", Input).value = " ".join(ws) if isinstance(ws, list) else ""

        def on_select_changed(self, event) -> None:
            if event.select.id == "name":
                self.load_for(chosen(event.select))
            elif event.select.id == "modes" and chosen(event.select):
                self.query_one("#mode", Input).value = chosen(event.select)

        def result(self):
            name = chosen(self.query_one("#name", Select))
            if not name:
                raise ValueError("choisis une sortie")
            ch: dict = {}
            mode = self.query_one("#mode", Input).value.strip()
            if mode:
                if not re.fullmatch(r"\d+x\d+(@\d+(\.\d+)?)?", mode):
                    raise ValueError("mode : format 2560x1440 ou 2560x1440@240")
                ch["mode"] = mode
            sc = self.query_one("#scale", Input).value.strip()
            if sc:
                try:
                    v = float(sc)
                except ValueError:
                    raise ValueError("échelle : nombre")
                if not 0.25 <= v <= 4.0:
                    raise ValueError("échelle entre 0.25 et 4")
                ch["scale"] = int(v) if v == int(v) else v
            tr = chosen(self.query_one("#transform", Select))
            if tr:
                ch["transform"] = tr
            ws = self.query_one("#workspaces", Input).value.split()
            if ws:
                ch["workspaces"] = ws
            if not ch:
                raise ValueError("rien à enregistrer")
            return name, ch

    # ── keybinds ──
    class BindForm(Modal):
        def __init__(self, key: str, action: str, known_actions: list[str]):
            super().__init__()
            self.key0, self.action0, self.known = key, action, known_actions

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
                yield Label("Raccourci — Ctrl+S enregistrer · Échap annuler")
                with VerticalScroll(id="form"):
                    yield Label("Raccourci (ex. Mod+Q, Mod+Shift+Return, XF86AudioMute)")
                    yield Input(id="key", value=self.key0)
                    yield Label("Action (ex. window-close, spawn:ghostty, spawn:noctalia msg panel-toggle launcher)")
                    yield Input(id="action", value=self.action0)
                    yield Label("Actions déjà utilisées (choisir pour remplir)")
                    yield Select([(a[:70], a) for a in self.known], id="known", prompt="(aucune)", allow_blank=True)
                yield from self.footer_widgets()

        def on_select_changed(self, event) -> None:
            if chosen(event.select):
                self.query_one("#action", Input).value = chosen(event.select)

        def result(self):
            return (self.query_one("#key", Input).value.strip(),
                    self.query_one("#action", Input).value.strip())

    # ── main app ──
    class ConfigApp(App):
        TITLE = "roudix-config"
        SUB_TITLE = "Umbriel"
        BINDINGS = [("a", "add", "Ajouter"), ("e", "edit", "Modifier"), ("d", "delete", "Supprimer"),
                    ("r", "reset", "Réinitialiser"), ("ctrl+s", "save_nix", "Sauver le .nix"),
                    ("q", "quit", "Quitter")]
        CSS = "#status { margin: 0 2; } .hint { margin: 0 2; color: $text-muted; } TextArea { height: 1fr; }"

        def __init__(self, messages: list[str]):
            super().__init__()
            self.messages = messages
            self.data = load_data()
            self.nix_text = ""

        # data helpers
        def rules(self) -> list[dict]:
            return self.data.setdefault("window_rule", [])

        def persist(self) -> None:
            save_data(self.data)
            self.refresh_nix()

        def reload(self) -> None:
            self.data = load_data()
            self.refresh_nix()

        def nix_dirty(self) -> bool:
            return self.query_one("#nixedit", TextArea).text != self.nix_text

        def refresh_nix(self) -> None:
            """Show the file as it is on disk, unless the user has unsaved edits."""
            ta = self.query_one("#nixedit", TextArea)
            if ta.text != self.nix_text:
                return
            nix = custom_path()
            txt = nix.read_text() if nix.exists() else ""
            if txt != ta.text:
                ta.load_text(txt)
            self.nix_text = ta.text

        def blocked(self) -> bool:
            if self.tab() != "t-nix" and self.nix_dirty():
                self.status("Modifications non sauvegardées dans l'onglet -custom.nix : "
                            "Ctrl+S pour les garder (ou ferme sans sauver) avant de continuer.")
                return True
            return False

        def on_tabbed_content_tab_activated(self, event) -> None:
            if event.pane.id == "t-nix":
                self.refresh_nix()

        def live(self) -> dict:
            return load_live()

        def status(self, text: str) -> None:
            self.query_one("#status", Static).update(text)

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent(id="tabs"):
                with TabPane("Règles de fenêtres", id="t-rules"):
                    yield DataTable(id="rules", cursor_type="row")
                    yield Static("a ajouter · e modifier · d supprimer", classes="hint")
                with TabPane("Écrans & workspaces", id="t-screens"):
                    yield DataTable(id="screens", cursor_type="row")
                    yield Static("e modifier (résolution, échelle, rotation, noms des workspaces) · "
                                 "r revenir aux valeurs par défaut de la sortie", classes="hint")
                with TabPane("Raccourcis", id="t-binds"):
                    yield DataTable(id="binds", cursor_type="row")
                    yield Static("a ajouter · e modifier · d supprimer · r tout remettre par défaut\n"
                                 "Une fois modifiée, la table est figée : les nouveaux raccourcis par défaut du repo "
                                 "n'arriveront plus (r pour revenir).", classes="hint")
                with TabPane("Mon -custom.nix", id="t-nix"):
                    yield TextArea("", id="nixedit", show_line_numbers=True)
                    yield Static("Ctrl+S sauvegarde (copie .bak + vérification de syntaxe).", classes="hint")
            yield Static("", id="status")
            yield Footer()

        def on_mount(self) -> None:
            self.query_one("#rules", DataTable).add_columns("app_id", "titre", "réglages")
            self.query_one("#screens", DataTable).add_columns("sortie", "mode", "échelle", "rotation", "workspaces")
            self.query_one("#binds", DataTable).add_columns("raccourci", "action")
            nix = custom_path()
            ta = self.query_one("#nixedit", TextArea)
            ta.load_text(nix.read_text() if nix.exists() else "")
            self.nix_text = ta.text
            self.render_all()
            self.status("\n".join(self.messages))

        # rendering
        def render_all(self) -> None:
            self.render_rules(); self.render_screens(); self.render_binds()

        def render_rules(self) -> None:
            t = self.query_one("#rules", DataTable); t.clear()
            for r in self.rules():
                t.add_row(r["match"].get("app_id", ""), r["match"].get("title", ""), rule_summary(r))

        def screen_names(self) -> list[str]:
            ov = get_overrides(self.data)
            names = list(effective_outputs(self.live(), ov))
            for n in list_outputs_full():
                if n not in names:
                    names.append(n)
            return names

        def render_screens(self) -> None:
            t = self.query_one("#screens", DataTable); t.clear()
            eff = effective_outputs(self.live(), get_overrides(self.data))
            for n in self.screen_names():
                c = eff.get(n, {})
                ws = c.get("workspaces")
                t.add_row(n, str(c.get("mode", "auto")), str(c.get("scale", 1)), str(c.get("transform", "normal")),
                          " ".join(ws) if isinstance(ws, list) else str(ws or "dynamic"), key=n)

        def binds(self) -> dict:
            return effective_binds(self.live(), get_overrides(self.data))

        def render_binds(self) -> None:
            t = self.query_one("#binds", DataTable); t.clear()
            for k, v in self.binds().items():
                t.add_row(k, bind_action(v), key=k)

        def cursor_key(self, table_id: str):
            t = self.query_one(table_id, DataTable)
            if t.row_count == 0:
                return None
            return t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value

        def tab(self) -> str:
            return self.query_one("#tabs", TabbedContent).active

        # actions
        def action_add(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-rules":
                self.open_rule(None)
            elif tab == "t-binds":
                self.open_bind(None)
            elif tab == "t-screens":
                self.open_output(None)

        def action_edit(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-rules":
                t = self.query_one("#rules", DataTable)
                if t.row_count:
                    self.open_rule(t.cursor_row)
            elif tab == "t-binds":
                self.open_bind(self.cursor_key("#binds"))
            elif tab == "t-screens":
                self.open_output(self.cursor_key("#screens"))

        def action_delete(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-rules":
                t = self.query_one("#rules", DataTable)
                if t.row_count and 0 <= t.cursor_row < len(self.rules()):
                    del self.rules()[t.cursor_row]
                    self.persist(); self.render_rules(); self.status("Règle supprimée — rebuild requis.")
            elif tab == "t-binds":
                k = self.cursor_key("#binds")
                if k:
                    table = self.binds(); table.pop(k, None)
                    save_binds_override(table); self.reload()
                    self.render_binds(); self.status(f"{k} supprimé — rebuild requis.")

        def action_reset(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-binds":
                reset_override("keybinds"); self.reload(); self.render_binds()
                self.status("Raccourcis remis par défaut — rebuild requis.")
            elif tab == "t-screens":
                k = self.cursor_key("#screens")
                if k:
                    reset_override("output", k); self.reload(); self.render_screens()
                    self.status(f"{k} remis par défaut — rebuild requis.")

        def action_save_nix(self) -> None:
            if self.tab() != "t-nix":
                return
            ta = self.query_one("#nixedit", TextArea)
            ok, msg = nix_parse_check(ta.text)
            if not ok:
                self.status(f"NON sauvegardé — erreur Nix : {msg}")
                return
            nix = custom_path()
            if nix.exists():
                shutil.copyfile(nix, nix.with_name(nix.name + ".bak"))
            nix.write_text(ta.text)
            self.nix_text = ta.text
            self.data = load_data()
            self.render_all()
            self.status(f"{nix.name} sauvegardé ({msg}). Ancienne version : {nix.name}.bak — rebuild requis.")

        # modal launchers
        def open_rule(self, index) -> None:
            windows = list_windows()
            remember_windows(windows)
            sources = build_sources(windows, load_seen(), list_desktop_apps())
            initial = self.rules()[index] if index is not None else None

            def done(rule):
                if rule:
                    if index is None:
                        self.rules().append(rule)
                    else:
                        self.rules()[index] = rule
                    self.persist(); self.render_rules(); self.status("Règle enregistrée — rebuild requis.")
            self.push_screen(RuleForm(sources, list_outputs(), initial), done)

        def open_output(self, name) -> None:
            names = self.screen_names()
            eff = effective_outputs(self.live(), get_overrides(self.data))

            def done(res):
                if res:
                    n, ch = res
                    save_output_override(n, ch); self.reload(); self.render_screens()
                    self.status(f"{n} enregistré — rebuild requis.")
            self.push_screen(OutputForm(name, names, eff, list_outputs_full()), done)

        def open_bind(self, key) -> None:
            table = self.binds()
            known = sorted({bind_action(v) for v in table.values()})
            action = bind_action(table[key]) if key in table else ""

            def done(res):
                if res:
                    k, a = res
                    try:
                        new = set_bind(table, k, a, old_key=key)
                    except ValueError as e:
                        self.status(str(e)); return
                    save_binds_override(new); self.reload(); self.render_binds()
                    self.status(f"{k} → {a} enregistré — rebuild requis.")
            self.push_screen(BindForm(key or "", action, known), done)

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

    reason = availability()
    if reason and not args.list:
        sys.exit(reason)

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

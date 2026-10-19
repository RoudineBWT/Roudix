"""roudix_config_core — logic shared by the TUI (roudix-config.py) and the GUI
(roudix-config-gui.py): the managed block in <compositor>-custom.nix, live
config, overrides, open windows / installed apps / outputs, availability check.
Everything compositor-specific lives in roudix_config_backends.py; the functions
below delegate to the active backend. No UI code here."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path



# ───────────────────────── language (same idiom as the other Roudix apps) ─────────────────────────

def _detect_lang() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val:
            return "fr" if val.lower().startswith("fr") else "en"
    return "en"


LANG = _detect_lang()


def L(fr: str, en: str) -> str:
    return fr if LANG == "fr" else en


def backend():
    """The backend of the active compositor (roudix.desktop.type). Falls back to
    Umbriel when the type is unknown so read-only helpers never crash; the UIs
    check availability() first. ROUDIX_BACKEND forces one (tests)."""
    from roudix_config_backends import BACKENDS
    return BACKENDS.get(os.environ.get("ROUDIX_BACKEND") or desktop_type() or "") or BACKENDS["umbriel"]


# ───────────────────────── paths & -custom.nix block ─────────────────────────
#
# Everything the tool manages lives in ONE marked block inside the user's own
# modules/home/umbriel-custom.nix (gitignored). The block is an inline module
# inside `imports`, so it never clashes with attributes the user wrote by hand.
# The tool reads its state back from that block; what is outside it is never
# touched (the "Mon -custom.nix" tab lets you edit all of it).

def repo_root() -> Path:
    """The roudix checkout holding modules/home/<comp>-custom.nix.
    ROUDIX_DIR wins; else walk up from this file to the folder with flake.nix
    (running from a checkout); else ~/.config/roudix (installed package, where
    this file lives in the Nix store — same default as NH_FLAKE)."""
    env = os.environ.get("ROUDIX_DIR")
    if env:
        return Path(env).expanduser()
    for p in Path(__file__).resolve().parents:
        if (p / "flake.nix").exists():
            return p
    return Path.home() / ".config" / "roudix"


def home_dir() -> Path:
    return repo_root() / "modules" / "home"


def custom_path() -> Path:
    return home_dir() / backend().custom_name


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "roudix-config"


BEGIN = "# >>> roudix-config >>>"
END = "# <<< roudix-config <<<"

def nix_escape(s: str) -> str:
    """Escape text for a Nix indented string ('' ... '')."""
    return s.replace("''", "'''").replace("${", "''${")


def nix_unescape(s: str) -> str:
    return re.sub(r"'''|''\$\{", lambda m: "''" if m.group(0) == "'''" else "${", s)


def render_block(data: dict) -> str:
    return backend().render_block(data)


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
        raise ValueError(L(f"corps du module introuvable dans {custom_path().name}", f"module body not found in {custom_path().name}"))
    return text[: m.end()] + "  imports = [\n" + block + "  ];\n" + text[m.end():]


def bootstrap() -> list[str]:
    """Make sure <comp>-custom.nix exists (copied from the .example if not) and
    migrate what the previous version stored in umbriel-managed.json."""
    msgs: list[str] = []
    custom = custom_path()
    example = custom.with_name(custom.name + ".example")

    if not custom.exists():
        if not example.exists():
            raise FileNotFoundError(L(f"fichier manquant : {example}", f"missing file: {example}"))
        shutil.copyfile(example, custom)
        msgs.append(L(f"{custom.name} créé à partir de {example.name}", f"{custom.name} created from {example.name}"))

    text = custom.read_text()
    # v2 imported a separate umbriel-managed.nix from the custom file: drop that.
    cleaned = re.sub(r"^[ \t]*imports = \[ \./umbriel-managed\.nix \];[^\n]*\n", "", text, flags=re.M)
    if cleaned != text:
        text = cleaned
        custom.write_text(text)
        msgs.append(L("Ancien import umbriel-managed.nix retiré (obsolète)", "Removed the old umbriel-managed.nix import (obsolete)"))
    elif "umbriel-managed.nix" in text:
        msgs.append(L("NOTE : umbriel-custom.nix mentionne encore umbriel-managed.nix — retire-le à la main, ce fichier est obsolète.",
                      "NOTE: umbriel-custom.nix still mentions umbriel-managed.nix — remove it by hand, that file is obsolete."))

    old = home_dir() / "umbriel-managed.json"       # only ever written by the Umbriel-only v2
    if backend().id == "umbriel" and old.exists():
        try:
            legacy = json.loads(old.read_text())
        except json.JSONDecodeError:
            legacy = {}
        if parse_block(text) is None:
            data = {k: legacy[k] for k in ("window_rule", "overrides") if legacy.get(k)}
            if data:
                save_data(data)
                msgs.append(L(f"Règles et réglages déplacés de {old.name} vers {custom.name}", f"Rules and settings moved from {old.name} to {custom.name}"))
        seen = legacy.get("seen")
        if isinstance(seen, dict) and seen:
            merged = {**load_seen(), **seen}
            _save_seen(merged)
        old.rename(old.with_name(old.name + ".migrated"))
    return msgs


# ───────────────────────── managed data ─────────────────────────

def load_data() -> dict:
    """What the app manages, read back from the block. `native` is derived from
    the rest on every save (and is what Nix consumes), so it is never kept."""
    try:
        data = dict(parse_block(custom_path().read_text()) or {})
    except OSError:
        return {}
    data.pop("native", None)
    return data


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
    """Open windows: [{app_id, title}], one per app_id (via the active compositor's CLI)."""
    return backend().list_windows()


def list_outputs() -> list[str]:
    return list(backend().outputs_runtime())


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
            items.append({"kind": "seen", "label": f"○ {app_id} — {title[:50]} " + L("(vu ouvert avant)", "(seen open before)"),
                          "pattern": exact_pattern(app_id)})
            known.add(app_id)
    for a in apps:
        if known.isdisjoint(a["candidates"]):
            items.append({"kind": "installed", "label": f"  {a['name']} " + L("(installée, app_id deviné)", "(installed, app_id guessed)"),
                          "pattern": pattern_for(a["candidates"])})
    return items


def filter_sources(items: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    return [i for i in items if q in i["label"].lower()] if q else items


# Internal keys are stable English ids; labels are translated for display.
PLACEMENTS = {
    "floating": "default_floating",
    "maximize": "default_maximize",
    "fullscreen": "default_fullscreen",
}


def placement_label(key: str) -> str:
    return {"floating": L("Flottante", "Floating"), "maximize": L("Maximisée", "Maximized"),
            "fullscreen": L("Plein écran", "Fullscreen")}[key]


def blur_label(value) -> str:
    return {True: L("Activé", "On"), False: L("Désactivé", "Off")}[value]


def build_rule(app_id: str, title: str = "", output: str | None = None,
               workspace=None, placement: str | None = None,
               blur: bool | None = None, opacity: float | None = None) -> dict:
    match: dict = {}
    if app_id:
        match["app_id"] = app_id
    if title:
        match["title"] = title
    if not match:
        raise ValueError(L("app_id ou titre requis", "app_id or title required"))
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
            raise ValueError(L("opacité entre 0 et 1", "opacity must be between 0 and 1"))
        rule["opacity"] = opacity
    if len(rule) == 1:
        raise ValueError(L("choisis au moins un réglage", "choose at least one setting"))
    return rule


def rule_preview(rule: dict) -> str:
    """What the rule becomes in the active compositor's own syntax."""
    return backend().preview_rule(rule)


def rule_summary(rule: dict) -> str:
    return ", ".join(f"{k.removeprefix('default_')}={v}" for k, v in rule.items() if k != "match")


# ───────────────────────── availability (which compositor?) ─────────────────────────

SUPPORTED = {"umbriel", "niri", "mangowc"}
NATIVE_DE = {"gnome", "kde", "cinnamon"}
TRANSFORMS = ["normal", "90", "180", "270", "flipped", "flipped-90", "flipped-180", "flipped-270"]


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def desktop_type() -> str | None:
    """roudix.desktop.type, written by Home-Manager to ~/.local/share/roudix/desktop-type.
    Falls back to the running session name before the first rebuild."""
    f = data_home() / "roudix" / "desktop-type"
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
        return L(f"Roudix Config n'est pas disponible sur {t} : utilise ses réglages natifs (Paramètres système).",
                 f"Roudix Config isn't available on {t}: use its native settings (System Settings).")
    if t:
        return L(f"Roudix Config ne gère pas encore {t} (pour l'instant : {', '.join(sorted(SUPPORTED))}).",
                 f"Roudix Config doesn't support {t} yet (for now: {', '.join(sorted(SUPPORTED))}).")
    return L("Impossible de déterminer le bureau (roudix.desktop.type). Fais un rebuild pour que "
             "~/.local/share/roudix/desktop-type soit créé.",
             "Can't determine the desktop (roudix.desktop.type). Rebuild so that "
             "~/.local/share/roudix/desktop-type gets created.")


# ───────────────────────── live config & overrides ─────────────────────────

def load_live() -> dict:
    """The config the compositor actually runs with (generated by Home-Manager)."""
    return backend().load_live()


def get_overrides(data: dict | None = None) -> dict:
    ov = (data if data is not None else load_data()).get("overrides", {})
    return ov if isinstance(ov, dict) else {}


def effective_outputs(live: dict, ov: dict) -> dict[str, dict]:
    """name -> {mode:'WxH@R', scale, transform[, workspaces]}: live config + pending overrides."""
    return backend().effective_outputs(live, ov)


def effective_binds(live: dict, ov: dict) -> dict:
    return backend().effective_binds(live, ov)


def bind_action(v) -> str:
    return backend().bind_action(v)


def set_bind(table: dict, key: str, action: str, old_key: str | None = None) -> dict:
    """Return the new table with `key` bound to `action` (backend rules decide moves/limits)."""
    return backend().set_bind(table, key, action, old_key)


_MODE_RE = re.compile(r"(\d+)x(\d+)(?:@(\d+(?:\.\d+)?))?")


def _same(a, b) -> bool:
    """Equal as config values: 1 == 1.0, '2560x1440@240' == '2560x1440@240.000'."""
    if a is None or b is None:
        return a is b
    ma, mb = (_MODE_RE.fullmatch(str(x)) for x in (a, b))
    if ma and mb:
        key = lambda m: (int(m[1]), int(m[2]), None if m[3] is None else round(float(m[3]), 3))  # noqa: E731
        return key(ma) == key(mb)
    if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (a, b)):
        return abs(a - b) < 1e-9
    return a == b


def save_output_override(name: str, desired: dict) -> None:
    """`desired` is the full state the form shows for this output. Only what differs
    from the live config is stored (so the rest keeps following the repo's defaults),
    and it REPLACES any previous override of that output: clearing or restoring a
    field drops its override."""
    base = backend().effective_outputs(backend().load_live(), {}).get(name, {})
    keep = {k: v for k, v in desired.items() if not _same(base.get(k), v)}
    data = load_data()
    ov = data.setdefault("overrides", {})
    outs = ov.setdefault("output", {})
    if keep:
        outs[name] = keep
    else:
        outs.pop(name, None)
    if not outs:
        ov.pop("output", None)
    if not ov:
        data.pop("overrides", None)
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
    if not table and backend().binds_mode == "keys":     # nothing left that differs from the defaults
        reset_override("keybinds")
        return
    data = load_data()
    data.setdefault("overrides", {})["keybinds"] = table
    save_data(data)


def list_outputs_full() -> dict[str, dict]:
    """name -> {modes: ["2560x1440@240.000", ...], current: str|None}"""
    return backend().outputs_runtime()


def nix_parse_check(text: str) -> tuple[bool, str]:
    """(ok, message). Uses `nix-instantiate --parse`; unchecked if nix is absent."""
    exe = shutil.which("nix-instantiate")
    if not exe:
        return True, L("syntaxe non vérifiée, nix-instantiate introuvable", "syntax not checked, nix-instantiate not found")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".nix", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        r = subprocess.run([exe, "--parse", path], capture_output=True, text=True, timeout=15)
    finally:
        os.unlink(path)
    if r.returncode == 0:
        return True, L("syntaxe Nix valide", "valid Nix syntax")
    return False, (r.stderr.strip().splitlines() or [L("erreur de syntaxe", "syntax error")])[-1]



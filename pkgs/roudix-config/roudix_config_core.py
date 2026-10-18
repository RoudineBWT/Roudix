"""roudix_config_core — logic shared by the TUI (roudix-config.py) and the GUI
(roudix-config-gui.py): the managed block in umbriel-custom.nix, live config,
overrides, open windows / installed apps / outputs, availability check.
No UI code here."""
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
    return home_dir() / f"{COMPOSITOR}-custom.nix"


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "roudix-config"


BEGIN = "# >>> roudix-config >>>"
END = "# <<< roudix-config <<<"

BLOCK_TEMPLATE = """\
    {begin} généré par Roudix Config — modifie-le via l'app
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
        msgs.append(f"{custom.name} créé à partir de {example.name}")

    text = custom.read_text()
    # v2 imported a separate umbriel-managed.nix from the custom file: drop that.
    cleaned = re.sub(r"^[ \t]*imports = \[ \./umbriel-managed\.nix \];[^\n]*\n", "", text, flags=re.M)
    if cleaned != text:
        text = cleaned
        custom.write_text(text)
        msgs.append("Ancien import umbriel-managed.nix retiré (obsolète)")
    elif "umbriel-managed.nix" in text:
        msgs.append("NOTE : umbriel-custom.nix mentionne encore umbriel-managed.nix — "
                    "retire-le à la main, ce fichier est obsolète.")

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
                msgs.append(f"Règles et réglages déplacés de {old.name} vers {custom.name}")
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
        return (f"roudix-config n'est pas disponible sur {t} : utilise ses réglages natifs "
                "(Paramètres système).")
    if t:
        return f"roudix-config ne gère pas encore {t} (pour l'instant : {', '.join(sorted(SUPPORTED))})."
    return ("Impossible de déterminer le bureau (roudix.desktop.type). Fais un rebuild pour que "
            "~/.local/share/roudix/desktop-type soit créé.")


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



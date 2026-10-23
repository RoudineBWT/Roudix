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
import shlex
import shutil
import subprocess
import sys
from pathlib import Path



# ───────────────────────── language (same idiom as the other Roudix apps) ─────────────────────────

# ── translations (gettext) ───────────────────────────────────────────────────
# Messages are written in English: tr("…"). Catalogs live in po/<lang>.po and the Nix
# package compiles them to share/locale/<lang>/LC_MESSAGES/roudix-config.mo. The language comes
# from LANGUAGE / LC_ALL / LC_MESSAGES / LANG; a missing catalog falls back to English.
import gettext as _gettext
import glob as _glob

_DOMAIN = "roudix-config"


def _find_localedir(domain):
    cands = [os.environ.get("ROUDIX_LOCALEDIR", "")]
    d = os.path.dirname(os.path.realpath(__file__))
    while True:
        cands += [os.path.join(d, "share", "locale"), os.path.join(d, "locale")]
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    for c in cands:
        if c and _glob.glob(os.path.join(c, "*", "LC_MESSAGES", domain + ".mo")):
            return c
    return None


_translation = _gettext.translation(_DOMAIN, _find_localedir(_DOMAIN), fallback=True)
tr = _translation.gettext        # tr("text")
trc = _translation.pgettext      # trc("context", "text")


def tr_noop(text):
    """Mark a string for extraction now, translate it later with tr()."""
    return text


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


def _strip_trailing_commas(raw: str) -> str:
    """Drop `,` directly before a `]` or `}` (outside strings). A hand edit of the
    JSON in the Nix tab often leaves one behind; it is unambiguous to repair."""
    out: list[str] = []
    in_str = esc = False
    for i, ch in enumerate(raw):
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == ",":
            rest = raw[i + 1:].lstrip()
            if rest[:1] in ("]", "}"):
                continue
        out.append(ch)
    return "".join(out)


def block_json_error(text: str) -> str | None:
    """None if the managed block's embedded JSON is valid *for Nix* (builtins.fromJSON
    is strict: no trailing commas), else a short message with line/column.
    The Nix syntax check cannot see this: to it the JSON is just a string."""
    m = _BLOCK_RE.search(text)
    j = _JSON_RE.search(m.group(0)) if m else None
    if not j:
        return None
    try:
        json.loads(nix_unescape(j.group(1)))
    except json.JSONDecodeError as e:
        line = text[: m.start() + j.start(1)].count("\n") + e.lineno
        return tr("Invalid JSON in the roudix-config block (line {line}, column {colno}): "
                "{msg} — trailing comma before ] or }} ?").format(line=line, colno=e.colno, msg=e.msg)
    return None


def parse_block(text: str) -> dict | None:
    m = _BLOCK_RE.search(text)
    if not m:
        return None
    j = _JSON_RE.search(m.group(0))
    if not j:
        return None
    raw = nix_unescape(j.group(1))
    for candidate in (raw, _strip_trailing_commas(raw)):     # 2nd pass self-heals trailing commas
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return data if isinstance(data, dict) else None
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
        raise ValueError(tr("module body not found in {name}").format(name=custom_path().name))
    return text[: m.end()] + "  imports = [\n" + block + "  ];\n" + text[m.end():]


def bootstrap() -> list[str]:
    """Make sure <comp>-custom.nix exists (copied from the .example if not) and
    migrate what the previous version stored in umbriel-managed.json."""
    msgs: list[str] = []
    custom = custom_path()
    example = custom.with_name(custom.name + ".example")

    if not custom.exists():
        if not example.exists():
            raise FileNotFoundError(tr("missing file: {example}").format(example=example))
        shutil.copyfile(example, custom)
        msgs.append(tr("{name} created from {name2}").format(name=custom.name, name2=example.name))

    text = custom.read_text()
    # v2 imported a separate umbriel-managed.nix from the custom file: drop that.
    cleaned = re.sub(r"^[ \t]*imports = \[ \./umbriel-managed\.nix \];[^\n]*\n", "", text, flags=re.M)
    if cleaned != text:
        text = cleaned
        custom.write_text(text)
        msgs.append(tr("Removed the old umbriel-managed.nix import (obsolete)"))
    elif "umbriel-managed.nix" in text:
        msgs.append(tr("NOTE: umbriel-custom.nix still mentions umbriel-managed.nix — remove it by hand, that file is obsolete."))

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
                msgs.append(tr("Rules and settings moved from {name} to {name2}").format(name=old.name, name2=custom.name))
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
    if _BLOCK_RE.search(text) and parse_block(text) is None:
        # Unreadable block (JSON broken beyond repair): keep a copy before regenerating it.
        shutil.copyfile(custom, custom.with_name(custom.name + ".broken.bak"))
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
            items.append({"kind": "seen", "label": f"○ {app_id} — {title[:50]} " + tr("(seen open before)"),
                          "pattern": exact_pattern(app_id)})
            known.add(app_id)
    for a in apps:
        if known.isdisjoint(a["candidates"]):
            items.append({"kind": "installed", "label": f"  {a['name']} " + tr("(installed, app_id guessed)"),
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
    return {"floating": tr("Floating"), "maximize": tr("Maximized"),
            "fullscreen": tr("Fullscreen")}[key]


def blur_label(value) -> str:
    return {True: tr("On"), False: tr("Off")}[value]


def build_rule(app_id: str, title: str = "", output: str | None = None,
               workspace=None, placement: str | None = None,
               blur: bool | None = None, opacity: float | None = None) -> dict:
    match: dict = {}
    if app_id:
        match["app_id"] = app_id
    if title:
        match["title"] = title
    if not match:
        raise ValueError(tr("app_id or title required"))
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
            raise ValueError(tr("opacity must be between 0 and 1"))
        rule["opacity"] = opacity
    if len(rule) == 1:
        raise ValueError(tr("choose at least one setting"))
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
        return tr("Roudix Config isn't available on {t}: use its native settings (System "
                "Settings).").format(t=t)
    if t:
        return tr("Roudix Config doesn't support {t} yet (for now: {join}).").format(t=t, join=', '.join(sorted(SUPPORTED)))
    return tr("Can't determine the desktop (roudix.desktop.type). Rebuild so that "
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


# ── Settings tab (curated knobs, see roudix_config_backends.*_SETTINGS) ──

def settings_catalog() -> list:
    return backend().settings_catalog()


def effective_settings(live: dict, ov: dict) -> dict:
    """id -> value shown: the user's override if any, else what the compositor runs with
    (None when unknown, e.g. no live config yet)."""
    B = backend()
    mine = ov.get("settings") or {}
    return {s.id: (mine[s.id] if s.id in mine else B.live_setting(live, s)) for s in B.settings_catalog()}


def set_setting_override(sid: str, value) -> None:
    """Store `value` for setting `sid`; if it equals what the compositor already runs
    with, the override is dropped so the setting keeps following the repo's default."""
    from roudix_config_backends import _coerce_setting
    B = backend()
    spec = next((s for s in B.settings_catalog() if s.id == sid), None)
    if spec is None:
        raise ValueError(tr("unknown setting: {sid}").format(sid=sid))
    value = _coerce_setting(spec, value)
    base = B.live_setting(B.load_live(), spec)
    data = load_data()
    ov = data.setdefault("overrides", {})
    st = ov.setdefault("settings", {})
    if base is not None and _same(base, value):
        st.pop(sid, None)
    else:
        st[sid] = value
    if not st:
        ov.pop("settings", None)
    if not ov:
        data.pop("overrides", None)
    save_data(data)


def reset_setting(sid: str) -> None:
    data = load_data()
    ov = data.get("overrides", {})
    ov.get("settings", {}).pop(sid, None)
    if not ov.get("settings"):
        ov.pop("settings", None)
    if not ov:
        data.pop("overrides", None)
    save_data(data)


# ── rebuild (same command as the `rebuild` alias of the shell modules) ──

def rebuild_argv() -> list[str]:
    nh = shutil.which("nh")
    if not nh:
        raise ValueError(tr("`nh` not found: run the rebuild by hand (the `rebuild` alias)."))
    flake = os.environ.get("NH_FLAKE") or str(repo_root())
    if not flake.startswith(("path:", "github:", "git+")):
        flake = "path:" + flake          # `path:` so the gitignored -custom.nix is part of the build
    return [nh, "os", "switch", "--accept-flake-config", flake]


_TERMINALS = ("ghostty", "kitty", "foot", "alacritty", "wezterm", "konsole",
              "gnome-terminal", "ptyxis", "xfce4-terminal", "xterm")
_EXEC_FLAG = {"gnome-terminal": ["--"], "ptyxis": ["--"], "xfce4-terminal": ["-x"], "wezterm": ["start", "--"]}


def spawn_rebuild() -> str:
    """Run the rebuild in a terminal window (live output, sudo password prompt works) and
    return the terminal's name. The window stays open until Enter so the result can be read."""
    argv = rebuild_argv()
    script = (f'{shlex.join(argv)}; rc=$?; echo; '
              f'if [ $rc -eq 0 ]; then echo "{tr("Rebuild done ✔ — reload the compositor config if needed.")}"; '
              f'else echo "{tr("Rebuild failed ✘ (code $rc) — read the messages above.")}"; fi; '
              f'printf "%s" "{tr("Press Enter to close… ")}"; read _')
    for t in ([os.environ["TERMINAL"]] if os.environ.get("TERMINAL") else []) + list(_TERMINALS):
        exe = shutil.which(t)
        if not exe:
            continue
        flag = _EXEC_FLAG.get(Path(exe).name, ["-e"])
        subprocess.Popen([exe, *flag, "sh", "-c", script], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return Path(exe).name
    raise ValueError(tr("No terminal found: run the rebuild by hand (the `rebuild` alias)."))


def list_outputs_full() -> dict[str, dict]:
    """name -> {modes: ["2560x1440@240.000", ...], current: str|None}"""
    return backend().outputs_runtime()


def nix_parse_check(text: str) -> tuple[bool, str]:
    """(ok, message). Checks the managed block's JSON, then `nix-instantiate --parse`
    (unchecked if nix is absent)."""
    jerr = block_json_error(text)
    if jerr:
        return False, jerr
    exe = shutil.which("nix-instantiate")
    if not exe:
        return True, tr("syntax not checked, nix-instantiate not found")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".nix", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        r = subprocess.run([exe, "--parse", path], capture_output=True, text=True, timeout=15)
    finally:
        os.unlink(path)
    if r.returncode == 0:
        return True, tr("valid Nix syntax")
    return False, (r.stderr.strip().splitlines() or [tr("syntax error")])[-1]



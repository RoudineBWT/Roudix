"""roudix_config_backends — one backend per compositor.

A backend knows, for ONE compositor:
  * how to list the open windows / outputs right now (its own CLI),
  * how to read the config it runs with (so the app shows real values),
  * how to turn the app's neutral data into that compositor's native settings
    and render the marked Nix block written into <comp>-custom.nix.

The data kept in the block is neutral (see roudix_config_core.build_rule):
    window_rule : [ {match:{app_id,title}, default_output, default_workspace,
                     default_floating|default_maximize|default_fullscreen,
                     blur, opacity} ]
    overrides.output[name]  : {mode:"WxH@R", scale, transform, [workspaces]}
    overrides.keybinds      : compositor-specific (see each backend)
Backends that need a different native shape (Niri, Mango) also store it under
`native`, which is what their Nix block consumes.
"""
from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from roudix_config_core import (
    BEGIN, END, TRANSFORMS, L, _collect, _run_json, config_home, nix_escape,
)


# ───────────────────────── curated settings ─────────────────────────
#
# "Settings" tab: a short, curated list of the knobs most people want to change
# (gaps, corners, blur, animations, touchpad, cursor, focus...). Each one is
# stored by id in overrides.settings and turned into a per-key lib.mkForce in
# the -custom.nix block, so it wins over the repo's default without touching
# the repo. Only values that differ from the live config are kept.

class Setting:
    def __init__(self, id, group, fr, en, kind, path="", lo=None, hi=None, step=1,
                 choices=(), keys=(), kdl=(), invert=False, as_int=False):
        self.id, self.group, self.kind, self.path = id, group, kind, path
        self.title = L(fr, en)
        self.lo, self.hi, self.step, self.choices = lo, hi, step, tuple(choices)
        self.keys, self.kdl, self.invert, self.as_int = tuple(keys), tuple(kdl), invert, as_int


GROUPS = {
    "look": L("Apparence", "Appearance"),
    "layout": L("Disposition", "Layout"),
    "anim": L("Animations", "Animations"),
    "input": L("Souris, clavier, curseur", "Mouse, keyboard, cursor"),
    "behavior": L("Comportement", "Behavior"),
}


def _nest(out: dict, parts: list[str], value) -> None:
    for p in parts[:-1]:
        out = out.setdefault(p, {})
    out[parts[-1]] = value


def _coerce_setting(s: "Setting", value):
    if s.kind == "bool":
        return bool(value)
    if s.kind == "int":
        return max(s.lo, min(s.hi, int(round(float(value))))) if s.lo is not None else int(round(float(value)))
    if s.kind == "float":
        v = round(float(value), 4)
        return max(s.lo, min(s.hi, v)) if s.lo is not None else v
    if s.kind == "choice":
        if value not in s.choices:
            raise ValueError(L(f"valeur inconnue : {value}", f"unknown value: {value}"))
        return value
    value = str(value).strip()
    if not value or any(c in value for c in "\"\n$"):
        raise ValueError(L("texte vide ou caractères interdits", "empty text or forbidden characters"))
    return value


def _S(*a, **k) -> "Setting":
    return Setting(*a, **k)


UMBRIEL_SETTINGS = [
    _S("gap", "look", "Espacement entre fenêtres (px)", "Gap between windows (px)", "int", "layout.gap", 0, 60),
    _S("corner", "look", "Arrondi des coins (px)", "Corner radius (px)", "int", "appearance.corner_radius", 0, 40),
    _S("blur", "look", "Flou (blur)", "Blur", "bool", "appearance.blur.enabled"),
    _S("blur_passes", "look", "Flou : nombre de passes", "Blur: passes", "int", "appearance.blur.passes", 1, 8),
    _S("shadow", "look", "Ombres des fenêtres", "Window shadows", "bool", "appearance.shadow.enabled"),
    _S("no_csd", "look", "Forcer les décorations côté serveur", "Prefer server-side decorations", "bool", "appearance.prefer_no_csd"),
    _S("layout", "layout", "Disposition par défaut", "Default layout", "choice", "layout.mode", choices=("scrolling", "dwindle", "master")),
    _S("center", "layout", "Centrer la colonne focalisée", "Center the focused column", "choice", "layout.scrolling.center_focused", choices=("never", "always", "on_overflow")),
    _S("col_width", "layout", "Largeur par défaut des colonnes", "Default column width", "float", "layout.scrolling.default_extent_fraction", 0.2, 1.0, 0.05),
    _S("master_width", "layout", "Largeur de la zone principale (master)", "Master area width", "float", "layout.master.default_width_fraction", 0.2, 0.8, 0.05),
    _S("anim", "anim", "Animations", "Animations", "bool", "animation.enabled"),
    _S("tap", "input", "Toucher pour cliquer (touchpad)", "Tap to click (touchpad)", "bool", "input.touchpad.tap"),
    _S("natural", "input", "Défilement naturel (touchpad)", "Natural scrolling (touchpad)", "bool", "input.touchpad.natural_scroll"),
    _S("accel", "input", "Accélération de la souris", "Mouse acceleration", "choice", "input.mouse.accel_profile", choices=("flat", "adaptive")),
    _S("follow", "input", "Le focus suit la souris", "Focus follows mouse", "bool", "input.focus.follows_mouse"),
    _S("hide_typing", "input", "Cacher le curseur en tapant", "Hide the cursor while typing", "bool", "input.cursor.hide_when_typing"),
    _S("cursor_size", "input", "Taille du curseur", "Cursor size", "int", "input.cursor.size", 16, 64),
    _S("cursor_theme", "input", "Thème du curseur", "Cursor theme", "text", "input.cursor.theme"),
    _S("activate", "behavior", "Donner le focus à une fenêtre qui le demande", "Focus windows that ask for attention", "bool", "general.focus_on_activate"),
    _S("back_forth", "behavior", "Revenir au workspace précédent (même touche)", "Workspace back-and-forth", "bool", "workspaces.back_and_forth"),
    _S("cheatsheet", "behavior", "Aide des raccourcis au démarrage", "Shortcut cheatsheet at startup", "bool", "general.show_cheatsheet"),
]

MANGO_SETTINGS = [
    _S("gap_inner", "look", "Espacement entre fenêtres (px)", "Gap between windows (px)", "int", "", 0, 40, keys=("gap_inner_horizontal", "gap_inner_vertical")),
    _S("gap_outer", "look", "Marge autour de l'écran (px)", "Outer margin (px)", "int", "", 0, 60, keys=("gap_outer_horizontal", "gap_outer_vertical")),
    _S("border", "look", "Épaisseur de la bordure (px)", "Border width (px)", "int", "", 0, 10, keys=("border_px",)),
    _S("corner", "look", "Arrondi des coins (px)", "Corner radius (px)", "int", "", 0, 40, keys=("border_radius",)),
    _S("blur", "look", "Flou (blur)", "Blur", "bool", "", keys=("blur",), as_int=True),
    _S("blur_radius", "look", "Flou : rayon", "Blur: radius", "int", "", 1, 30, keys=("blur_params_radius",)),
    _S("shadows", "look", "Ombres des fenêtres", "Window shadows", "bool", "", keys=("shadows",), as_int=True),
    _S("unfocused", "look", "Opacité des fenêtres non focalisées", "Unfocused window opacity", "float", "", 0.3, 1.0, 0.05, keys=("unfocused_opacity",)),
    _S("focused", "look", "Opacité de la fenêtre focalisée", "Focused window opacity", "float", "", 0.3, 1.0, 0.05, keys=("focused_opacity",)),
    _S("smart_gaps", "layout", "Pas d'espacement quand une seule fenêtre", "No gaps with a single window", "bool", "", keys=("smart_gaps",), as_int=True),
    _S("no_border_single", "layout", "Pas de bordure quand une seule fenêtre", "No border with a single window", "bool", "", keys=("no_border_when_single",), as_int=True),
    _S("master_factor", "layout", "Largeur de la zone principale (master)", "Master area width", "float", "", 0.2, 0.8, 0.05, keys=("default_master_factor",)),
    _S("scroller_width", "layout", "Largeur par défaut en mode scroller", "Default scroller width", "float", "", 0.2, 1.0, 0.05, keys=("scroller_default_proportion",)),
    _S("anim", "anim", "Animations", "Animations", "bool", "", keys=("animations",), as_int=True),
    _S("tap", "input", "Toucher pour cliquer (touchpad)", "Tap to click (touchpad)", "bool", "", keys=("tap_to_click",), as_int=True),
    _S("natural", "input", "Défilement naturel (touchpad)", "Natural scrolling (touchpad)", "bool", "", keys=("trackpad_natural_scrolling",), as_int=True),
    _S("follow", "input", "Le focus suit la souris", "Focus follows mouse", "bool", "", keys=("sloppy_focus",), as_int=True),
    _S("warp", "input", "Le curseur suit le focus", "Cursor follows focus", "bool", "", keys=("warp_cursor",), as_int=True),
    _S("numlock", "input", "Verrouillage numérique au démarrage", "Num Lock on at startup", "bool", "", keys=("numlock_on",), as_int=True),
    _S("repeat_rate", "input", "Répétition des touches (par seconde)", "Key repeat rate (per second)", "int", "", 10, 80, keys=("repeat_rate",)),
    _S("repeat_delay", "input", "Délai avant répétition (ms)", "Key repeat delay (ms)", "int", "", 150, 1000, 50, keys=("repeat_delay",)),
    _S("cursor_size", "input", "Taille du curseur", "Cursor size", "int", "", 16, 64, keys=("cursor_size",)),
    _S("cursor_theme", "input", "Thème du curseur", "Cursor theme", "text", "", keys=("cursor_theme",)),
]

NIRI_SETTINGS = [
    _S("gaps", "look", "Espacement entre fenêtres (px)", "Gap between windows (px)", "int", "layout.gaps", 0, 60, kdl=("layout", "gaps")),
    _S("no_csd", "look", "Forcer les décorations côté serveur", "Prefer server-side decorations", "bool", "prefer-no-csd", kdl=("prefer-no-csd",)),
    _S("center", "layout", "Centrer la colonne focalisée", "Center the focused column", "choice", "layout.center-focused-column", choices=("never", "always", "on-overflow"), kdl=("layout", "center-focused-column")),
    _S("anim", "anim", "Animations", "Animations", "bool", "animations.enable", kdl=("animations", "off"), invert=True),
    _S("slowdown", "anim", "Ralentir les animations (×)", "Animation slowdown (×)", "float", "animations.slowdown", 0.1, 5.0, 0.1, kdl=("animations", "slowdown")),
    _S("tap", "input", "Toucher pour cliquer (touchpad)", "Tap to click (touchpad)", "bool", "input.touchpad.tap", kdl=("input", "touchpad", "tap")),
    _S("natural", "input", "Défilement naturel (touchpad)", "Natural scrolling (touchpad)", "bool", "input.touchpad.natural-scroll", kdl=("input", "touchpad", "natural-scroll")),
    _S("accel", "input", "Accélération de la souris", "Mouse acceleration", "choice", "input.mouse.accel-profile", choices=("flat", "adaptive"), kdl=("input", "mouse", "accel-profile")),
    _S("follow", "input", "Le focus suit la souris", "Focus follows mouse", "bool", "input.focus-follows-mouse.enable", kdl=("input", "focus-follows-mouse")),
    _S("numlock", "input", "Verrouillage numérique au démarrage", "Num Lock on at startup", "bool", "input.keyboard.numlock", kdl=("input", "keyboard", "numlock")),
    _S("cursor_size", "input", "Taille du curseur", "Cursor size", "int", "cursor.size", 16, 64, kdl=("cursor", "xcursor-size")),
    _S("cursor_theme", "input", "Thème du curseur", "Cursor theme", "text", "cursor.theme", kdl=("cursor", "xcursor-theme")),
    _S("back_forth", "behavior", "Revenir au workspace précédent (même touche)", "Workspace back-and-forth", "bool", "input.workspace-auto-back-and-forth", kdl=("input", "workspace-auto-back-and-forth")),
    _S("hot_corner", "behavior", "Coin actif (overview)", "Hot corner (overview)", "bool", "gestures.hot-corners.enable", kdl=("gestures", "hot-corners", "off"), invert=True),
    _S("hotkey_overlay", "behavior", "Masquer l'aide des raccourcis au démarrage", "Hide the shortcut overlay at startup", "bool", "hotkey-overlay.skip-at-startup", kdl=("hotkey-overlay", "skip-at-startup")),
]


# ───────────────────────── KDL (just what niri configs use) ─────────────────────────

class KdlError(ValueError):
    pass


class Node:
    __slots__ = ("name", "args", "props", "children")

    def __init__(self, name: str):
        self.name = name
        self.args: list = []
        self.props: dict = {}
        self.children: list[Node] = []

    def child(self, name: str):
        return next((c for c in self.children if c.name == name), None)

    def __repr__(self) -> str:  # debugging aid
        return f"Node({self.name!r}, {self.args!r}, {self.props!r}, {len(self.children)} children)"


_BARE_STOP = set(' \t\r\n{}();[]=",\\')


class _Kdl:
    def __init__(self, text: str):
        self.s = text
        self.i = 0

    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.s[j] if j < len(self.s) else ""

    def skip_space(self, newlines: bool) -> None:
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\ufeff":
                self.i += 1
            elif c in "\r\n":
                if not newlines:
                    return
                self.i += 1
            elif c == "\\" and self.peek(1) in ("\n", "\r"):  # line continuation
                self.i += 2
                if self.peek() == "\n" and s[self.i - 1] == "\r":
                    self.i += 1
            elif c == "/" and self.peek(1) == "/":
                while self.i < len(s) and s[self.i] not in "\r\n":
                    self.i += 1
            elif c == "/" and self.peek(1) == "*":
                depth, self.i = 1, self.i + 2
                while self.i < len(s) and depth:
                    if s.startswith("/*", self.i):
                        depth, self.i = depth + 1, self.i + 2
                    elif s.startswith("*/", self.i):
                        depth, self.i = depth - 1, self.i + 2
                    else:
                        self.i += 1
            else:
                return

    def string(self) -> str:
        s = self.s
        if s[self.i] == "r" or s[self.i] == "#":  # raw string r#"..."#
            j = self.i + (1 if s[self.i] == "r" else 0)
            h = 0
            while s[j] == "#":
                h, j = h + 1, j + 1
            if s[j] != '"':
                raise KdlError("bad raw string")
            end = s.find('"' + "#" * h, j + 1)
            if end < 0:
                raise KdlError("unterminated raw string")
            self.i = end + 1 + h
            return s[j + 1:end]
        self.i += 1
        out = []
        esc = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "s": " "}
        while self.i < len(s):
            c = s[self.i]
            if c == '"':
                self.i += 1
                return "".join(out)
            if c == "\\":
                n = s[self.i + 1]
                if n == "u" and s[self.i + 2] == "{":
                    e = s.index("}", self.i)
                    out.append(chr(int(s[self.i + 3:e], 16)))
                    self.i = e + 1
                    continue
                out.append(esc.get(n, n))
                self.i += 2
                continue
            out.append(c)
            self.i += 1
        raise KdlError("unterminated string")

    def bare(self) -> str:
        j = self.i
        while j < len(self.s) and self.s[j] not in _BARE_STOP:
            j += 1
        w = self.s[self.i:j]
        self.i = j
        return w

    @staticmethod
    def convert(word: str):
        if word in ("true", "#true"):
            return True
        if word in ("false", "#false"):
            return False
        if word in ("null", "#null"):
            return None
        try:
            return int(word, 0) if re.fullmatch(r"[+-]?(0x[0-9a-fA-F_]+|\d[\d_]*)", word) else float(word)
        except ValueError:
            return word

    def value(self):
        c = self.peek()
        if c == '"' or (c == "r" and self.peek(1) in ('"', "#")) or (c == "#" and self.peek(1) in ('"', "#")):
            return self.string()
        return self.convert(self.bare())

    def nodes(self, top: bool) -> list[Node]:
        out: list[Node] = []
        while True:
            self.skip_space(True)
            c = self.peek()
            if c == "":
                if not top:
                    raise KdlError("unexpected end of file")
                return out
            if c == "}":
                if top:
                    raise KdlError("unexpected }")
                self.i += 1
                return out
            if c == ";":
                self.i += 1
                continue
            drop = False
            if c == "/" and self.peek(1) == "-":
                self.i += 2
                self.skip_space(True)
                drop = True
            node = self.node()
            if not drop:
                out.append(node)

    def node(self) -> Node:
        c = self.peek()
        name = self.string() if c == '"' or (c == "r" and self.peek(1) in ('"', "#")) else self.bare()
        if not name:
            raise KdlError(f"bad node name at offset {self.i}")
        node = Node(name)
        while True:
            self.skip_space(False)
            c = self.peek()
            if c in ("", "\n", "\r", ";", "}"):
                if c == ";":
                    self.i += 1
                return node
            if c == "{":
                self.i += 1
                node.children = self.nodes(False)
                self.skip_space(False)
                if self.peek() == ";":
                    self.i += 1
                return node
            drop = False
            if c == "/" and self.peek(1) == "-":
                self.i += 2
                self.skip_space(False)
                drop = True
                if self.peek() == "{":
                    self.i += 1
                    self.nodes(False)
                    continue
            start = self.i
            if self.peek() == '"' or (self.peek() == "r" and self.peek(1) in ('"', "#")):
                first = self.string()
                quoted = True
            else:
                first = self.bare()
                quoted = False
            if self.peek() == "=":  # property
                self.i += 1
                v = self.value()
                if not drop:
                    node.props[first] = v
            else:
                self.i = start
                v = self.value()
                if not drop:
                    node.args.append(v)
            _ = quoted


def parse_kdl(text: str) -> list[Node]:
    return _Kdl(text).nodes(True)


# ───────────────────────── helpers shared by backends ─────────────────────────

def _fmt_refresh(mhz: float) -> str:
    return f"{mhz / 1000:.3f}"


def mode_from_string(mode: str) -> tuple[int, int, float | None]:
    m = re.fullmatch(r"(\d+)x(\d+)(?:@(\d+(?:\.\d+)?))?", mode.strip())
    if not m:
        raise ValueError(L("Mode : format 2560x1440 ou 2560x1440@240", "Mode: use 2560x1440 or 2560x1440@240"))
    return int(m.group(1)), int(m.group(2)), float(m.group(3)) if m.group(3) else None


def _norm_mode(mode) -> str:
    """'2560x1440@240.000000' -> '2560x1440@240.000'."""
    m = re.fullmatch(r"(\d+)x(\d+)(?:@(\d+(?:\.\d+)?))?", str(mode))
    if not m:
        return str(mode)
    return f"{m.group(1)}x{m.group(2)}" + (f"@{float(m.group(3)):.3f}" if m.group(3) else "")


def _render(template: str, begin_comment: str, data: dict) -> str:
    js = nix_escape(json.dumps(data, indent=2, ensure_ascii=False))
    return template.format(begin=BEGIN, end=END, json=js, comment=begin_comment)


_HEAD = """\
    {begin} {comment}
    ({{ lib, ... }}:
      let
        data = builtins.fromJSON ''
{json}
        '';
"""


class Backend:
    id = ""
    custom_name = ""           # file under modules/home/
    label = ""
    features = frozenset({"rules", "screens", "binds"})
    workspace_names = False    # can the app rename workspaces?
    binds_mode = "table"       # "table": whole table replaced · "keys": per-key overrides only
    can_delete_binds = True
    can_move_binds = True
    modifiers = ["Mod", "Super", "Ctrl", "Alt", "Shift"]
    placements = ("floating", "maximize", "fullscreen")
    blur_choices = (True, False)   # values offered besides "unchanged"
    cli = ""

    # ── what the UIs show ──
    def key_help(self) -> str:
        return L("Ex. Mod+Q, Mod+Shift+Return, XF86AudioMute", "e.g. Mod+Q, Mod+Shift+Return, XF86AudioMute")

    def action_help(self) -> str:
        return ""

    def compose_key(self, mods: list[str], key: str) -> str:
        return "+".join(mods + ([key] if key else []))

    def parse_key(self, raw: str) -> tuple[list[str], str]:
        parts = raw.strip().split("+")
        return parts[:-1], (parts[-1] if parts else "")

    def bind_action(self, v) -> str:
        return v if isinstance(v, str) else str(v.get("action", "")) if isinstance(v, dict) else str(v)

    def validate_bind(self, key: str, action: str) -> None:
        if not key.strip() or not action.strip():
            raise ValueError(L("raccourci et action requis", "shortcut and action required"))

    def workspace_choices(self) -> list[tuple[str, object]]:
        return [(str(i), i) for i in range(1, 11)]

    # ── runtime ──
    def list_windows(self) -> list[dict]:
        return []

    def outputs_runtime(self) -> dict[str, dict]:
        """name -> {modes: ['2560x1440@240.000', ...], current: str|None}"""
        return {}

    # ── config ──
    def load_live(self) -> dict:
        return {}

    def effective_outputs(self, live: dict, ov: dict) -> dict[str, dict]:
        raise NotImplementedError

    def effective_binds(self, live: dict, ov: dict) -> dict:
        raise NotImplementedError

    def set_bind(self, table: dict, key: str, action: str, old_key: str | None = None) -> dict:
        raise NotImplementedError

    def preview_rule(self, rule: dict) -> str:
        raise NotImplementedError

    def render_block(self, data: dict) -> str:
        raise NotImplementedError

    # ── curated settings (see UMBRIEL_SETTINGS & co) ──
    def settings_catalog(self) -> list:
        return []

    def live_setting(self, live: dict, s):
        """Value the compositor runs with right now, or None when unknown."""
        return None

    def native_settings(self, values: dict) -> dict:
        return {}

    def _chosen(self, values: dict):
        return [s for s in self.settings_catalog() if s.id in values]


# ───────────────────────── Umbriel ─────────────────────────

class Umbriel(Backend):
    id = "umbriel"
    custom_name = "umbriel-custom.nix"
    label = "Umbriel"
    workspace_names = True
    cli = "umbriel"

    TEMPLATE = _HEAD + """\
        ov = data.overrides or {{ }};
        n = data.native or {{ }};
      in
      {{
        # window_rule: appended AFTER the repo's rules (Umbriel applies the last match).
        # overrides.output: per-output keys replacing the repo's (mkForce per leaf).
        # overrides.keybinds: the COMPLETE table replacing the repo's one.
        # native.settings: the Settings tab (one mkForce per changed key).
        programs.umbriel.settings = lib.mkMerge [
          (lib.mkAfter {{ window_rule = data.window_rule or [ ]; }})
          (lib.optionalAttrs (n ? settings) (lib.mapAttrsRecursive (_: lib.mkForce) n.settings))
          (lib.optionalAttrs (ov ? output) {{
            output = lib.mapAttrsRecursive (_: lib.mkForce) ov.output;
          }})
          (lib.optionalAttrs (ov ? keybinds) {{ keybinds = lib.mkForce ov.keybinds; }})
        ];
      }})
    {end}
"""

    def action_help(self) -> str:
        return "window-close · spawn:ghostty · spawn:noctalia msg panel-toggle launcher"

    def list_windows(self) -> list[dict]:
        data = _run_json(["umbriel", "windows", "--json"])
        seen: dict[str, dict] = {}
        for w in _collect(data, "app_id") if data is not None else []:
            a = w.get("app_id", "")
            if a and a not in seen:
                seen[a] = {"app_id": a, "title": w.get("title", "")}
        return list(seen.values())

    def outputs_runtime(self) -> dict[str, dict]:
        data = _run_json(["umbriel", "outputs", "--json"])
        res: dict[str, dict] = {}
        for o in _collect(data, "name") if data is not None else []:
            modes, current = [], None
            for m in o.get("modes", []) or []:
                if not isinstance(m, dict) or "width" not in m:
                    continue
                s = f"{m['width']}x{m['height']}@{_fmt_refresh(m.get('refresh_mhz', 0))}"
                if s not in modes:
                    modes.append(s)
                if m.get("current"):
                    current = s
            res[o["name"]] = {"modes": modes, "current": current}
        return res

    def load_live(self) -> dict:
        try:
            import tomllib
            return tomllib.loads((config_home() / "umbriel" / "config.toml").read_text())
        except (OSError, ValueError, ImportError):
            return {}

    def effective_outputs(self, live: dict, ov: dict) -> dict[str, dict]:
        out = {n: dict(c) for n, c in (live.get("output") or {}).items() if isinstance(c, dict)}
        for n, c in (ov.get("output") or {}).items():
            out.setdefault(n, {}).update(c)
        return out

    def effective_binds(self, live: dict, ov: dict) -> dict:
        if isinstance(ov.get("keybinds"), dict):
            return json.loads(json.dumps(ov["keybinds"]))
        return json.loads(json.dumps(live.get("keybinds") or {}))

    def set_bind(self, table: dict, key: str, action: str, old_key: str | None = None) -> dict:
        self.validate_bind(key, action)
        key, action = key.strip(), action.strip()
        new = dict(table)
        prev = new.pop(old_key, None) if old_key else None
        if prev is None:
            prev = table.get(key)
        value = dict(prev, action=action) if isinstance(prev, dict) else action
        new[key] = value
        return new

    def preview_rule(self, rule: dict) -> str:
        def val(v):
            return "true" if v is True else "false" if v is False else json.dumps(v, ensure_ascii=False)
        lines = ["[[window_rule]]"]
        for k, v in rule["match"].items():
            lines.append(f"match.{k} = {val(v)}")
        for k, v in rule.items():
            if k != "match":
                lines.append(f"{k} = {val(v)}")
        return "\n".join(lines)

    def settings_catalog(self) -> list:
        return UMBRIEL_SETTINGS

    def live_setting(self, live: dict, s):
        cur = live
        for part in s.path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur if not isinstance(cur, (dict, list)) else None

    def native_settings(self, values: dict) -> dict:
        out: dict = {}
        for s in self._chosen(values):
            _nest(out, s.path.split("."), values[s.id])
        return out

    def render_block(self, data: dict) -> str:
        nat = self.native_settings((data.get("overrides") or {}).get("settings") or {})
        full = dict(data, native={"settings": nat}) if nat else data
        return _render(self.TEMPLATE, L("généré par Roudix Config — modifie-le via l'app",
                                        "generated by Roudix Config — edit it through the app"), full)


# ───────────────────────── MangoWC ─────────────────────────

MANGO_RR = {i: t for i, t in enumerate(TRANSFORMS)}          # rr 0..7 == wl_output transforms
MANGO_RR_REV = {t: i for i, t in MANGO_RR.items()}


def parse_mango_conf(text: str) -> dict[str, list[str]]:
    """config.conf -> {key: [values...]} (repeated keys keep every line)."""
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out.setdefault(k.strip(), []).append(v.strip())
    return out


def parse_mango_props(rule: str) -> dict[str, str]:
    """'name:^DP-1$,width:2560,...' -> ordered dict (values may contain ':' or ',' only if regex)."""
    props: dict[str, str] = {}
    for part in re.split(r",(?=[A-Za-z_]+:)", rule):
        if ":" in part:
            k, v = part.split(":", 1)
            props[k.strip()] = v.strip()
    return props


def mango_rule_name(props: dict[str, str]) -> str | None:
    n = props.get("name")
    return re.sub(r"^\^|\$$", "", n) if n else None


class Mango(Backend):
    id = "mangowc"
    custom_name = "mango-custom.nix"
    label = "MangoWC"
    modifiers = ["SUPER", "CTRL", "ALT", "SHIFT"]
    placements = ("floating", "fullscreen")      # no clean "maximized" rule in mango
    blur_choices = (False,)                      # window_rule only offers no_blur
    cli = "mmsg"

    TEMPLATE = _HEAD + """\
        n = data.native or {{ }};
      in
      {{
        # window_rule: added to the repo's. monitor_rule / bind: Mango applies the FIRST
        # matching monitor rule and has no way to drop a bind, so when the app changes
        # them it replaces the whole list (taken from your live config.conf).
        wayland.windowManager.mango.settings = lib.mkMerge [
          (lib.mkAfter {{ window_rule = n.window_rule or [ ]; }})
          (lib.optionalAttrs (n ? settings) (lib.mapAttrs (_: lib.mkForce) n.settings))
          (lib.optionalAttrs (n ? monitor_rule) {{ monitor_rule = lib.mkForce n.monitor_rule; }})
          (lib.optionalAttrs (n ? bind) {{ bind = lib.mkForce n.bind; }})
        ];
      }})
    {end}
"""

    def key_help(self) -> str:
        return L("Ex. SUPER,Q · SUPER+SHIFT,Return · NONE,XF86AudioMute  (modificateurs, touche)",
                 "e.g. SUPER,Q · SUPER+SHIFT,Return · NONE,XF86AudioMute  (modifiers, key)")

    def action_help(self) -> str:
        return "killclient · spawn,ghostty · togglefloating · view,3"

    def compose_key(self, mods: list[str], key: str) -> str:
        return ("+".join(mods) if mods else "NONE") + "," + key

    def parse_key(self, raw: str) -> tuple[list[str], str]:
        if "," not in raw:
            return [], raw.strip()
        mods, key = raw.split(",", 1)
        m = [] if mods.strip().upper() == "NONE" else [x.strip().upper() for x in mods.split("+") if x.strip()]
        return m, key.strip()

    def validate_bind(self, key: str, action: str) -> None:
        super().validate_bind(key, action)
        if "," not in key:
            raise ValueError(L("Raccourci Mango : « MODS,TOUCHE » (ex. SUPER,Q)", "Mango shortcut: “MODS,KEY” (e.g. SUPER,Q)"))

    def workspace_choices(self) -> list[tuple[str, object]]:
        return [(str(i), i) for i in range(1, 10)]

    def _conf(self) -> dict[str, list[str]]:
        try:
            return parse_mango_conf((config_home() / "mango" / "config.conf").read_text())
        except OSError:
            return {}

    def list_windows(self) -> list[dict]:
        data = _run_json(["mmsg", "get", "all-clients"])
        seen: dict[str, dict] = {}
        key = "app_id" if data is not None and _collect(data, "app_id") else "appid"   # 0.18 renamed it
        for w in _collect(data, key) if data is not None else []:
            a = w.get(key, "")
            if a and a not in seen:
                seen[a] = {"app_id": a, "title": w.get("title", "")}
        return list(seen.values())

    def outputs_runtime(self) -> dict[str, dict]:
        res: dict[str, dict] = {}
        data = _run_json(["mmsg", "get", "all-monitors"])
        for m in _collect(data, "name") if data is not None else []:
            res[m["name"]] = {"modes": [], "current": None}
        # modes come from wlr-randr when it is installed (mmsg doesn't list them)
        if shutil.which("wlr-randr"):
            rr = _run_json(["wlr-randr", "--json"])
            for o in _collect(rr, "name") if rr is not None else []:
                modes, current = [], None
                for m in o.get("modes", []) or []:
                    if "width" not in m:
                        continue
                    s = f"{m['width']}x{m['height']}@{float(m.get('refresh', 0)):.3f}"
                    if s not in modes:
                        modes.append(s)
                    if m.get("current"):
                        current = s
                res[o["name"]] = {"modes": modes, "current": current}
        return res

    def load_live(self) -> dict:
        return self._conf()

    def settings_catalog(self) -> list:
        return MANGO_SETTINGS

    def live_setting(self, live: dict, s):
        vals = live.get(s.keys[0]) if s.keys else None
        if not vals:
            return None
        raw = vals[-1].strip()
        try:
            if s.kind == "bool":
                return raw.lower() in ("1", "true", "yes", "on")
            if s.kind == "int":
                return int(float(raw))
            if s.kind == "float":
                return float(raw)
        except ValueError:
            return None
        return raw.strip('"')

    def native_settings(self, values: dict) -> dict:
        out: dict = {}
        for s in self._chosen(values):
            v = values[s.id]
            v = int(v) if s.as_int and isinstance(v, bool) else v
            for k in s.keys:
                out[k] = v
        return out

    def _monitor_rules(self, live: dict) -> list[dict[str, str]]:
        return [parse_mango_props(r) for r in live.get("monitor_rule", [])]

    def effective_outputs(self, live: dict, ov: dict) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for p in self._monitor_rules(live):
            name = mango_rule_name(p)
            if not name or name in out:           # first matching rule wins
                continue
            cfg: dict = {}
            if "width" in p and "height" in p:
                cfg["mode"] = f"{p['width']}x{p['height']}" + (f"@{float(p['refresh']):.3f}" if "refresh" in p else "")
            if "scale" in p:
                cfg["scale"] = float(p["scale"])
            if "rr" in p and p["rr"].isdigit() and int(p["rr"]) in MANGO_RR:
                cfg["transform"] = MANGO_RR[int(p["rr"])]
            out[name] = cfg
        for n, c in (ov.get("output") or {}).items():
            out.setdefault(n, {}).update({k: v for k, v in c.items() if k != "workspaces"})
        return out

    def native_monitor_rules(self, live: dict, ov_out: dict) -> list[str] | None:
        """Full monitor_rule list: the live one with the overrides applied in place."""
        if not ov_out:
            return None
        rules = self._monitor_rules(live)
        done: set[str] = set()
        result: list[dict[str, str]] = []
        for p in rules:
            name = mango_rule_name(p)
            if name in ov_out and name not in done:
                done.add(name)
                p = self._apply_output(dict(p), ov_out[name])
            result.append(p)
        for name, c in ov_out.items():                    # outputs with no rule yet
            if name not in done:
                result.append(self._apply_output({"name": f"^{name}$"}, c))
        return [",".join(f"{k}:{v}" for k, v in p.items()) for p in result]

    @staticmethod
    def _apply_output(p: dict[str, str], c: dict) -> dict[str, str]:
        if "mode" in c:
            w, h, r = mode_from_string(c["mode"])
            p["width"], p["height"] = str(w), str(h)
            if r is not None:
                p["refresh"] = f"{r:g}"
        if "scale" in c:
            p["scale"] = f"{c['scale']:g}"
        if "transform" in c:
            p["rr"] = str(MANGO_RR_REV.get(c["transform"], 0))
        return p

    def effective_binds(self, live: dict, ov: dict) -> dict:
        if isinstance(ov.get("keybinds"), dict):
            return dict(ov["keybinds"])
        table: dict[str, str] = {}
        for line in live.get("bind", []):
            parts = line.split(",", 2)
            if len(parts) < 3:
                continue
            table[f"{parts[0].strip()},{parts[1].strip()}"] = parts[2].strip()
        return table

    def set_bind(self, table: dict, key: str, action: str, old_key: str | None = None) -> dict:
        self.validate_bind(key, action)
        new = dict(table)
        if old_key:
            new.pop(old_key, None)
        new[key.strip()] = action.strip()
        return new

    # neutral rule -> mango window_rule line
    def native_window_rule(self, r: dict) -> str:
        parts: list[str] = []
        if "default_workspace" in r:
            parts.append(f"tags:{r['default_workspace']}")
        if "default_output" in r:
            parts.append(f"monitor:{r['default_output']}")
        if r.get("default_floating"):
            parts.append("is_floating:1")
        if r.get("default_fullscreen"):
            parts.append("is_fullscreen:1")
        if r.get("blur") is False:
            parts.append("no_blur:1")
        if "opacity" in r:
            parts += [f"focused_opacity:{r['opacity']:g}", f"unfocused_opacity:{r['opacity']:g}"]
        for k in ("app_id", "title"):
            if k in r["match"]:
                parts.append(f"{k}:{r['match'][k]}")
        return ",".join(parts)

    def preview_rule(self, rule: dict) -> str:
        return "window_rule=" + self.native_window_rule(rule)

    def native(self, data: dict) -> dict:
        ov = data.get("overrides", {})
        nat: dict = {"window_rule": [self.native_window_rule(r) for r in data.get("window_rule", [])]}
        live = self._conf()
        mon = self.native_monitor_rules(live, ov.get("output", {}))
        if mon:
            nat["monitor_rule"] = mon
        st = self.native_settings(ov.get("settings") or {})
        if st:
            nat["settings"] = st
        if isinstance(ov.get("keybinds"), dict):
            nat["bind"] = [f"{k},{v}" for k, v in ov["keybinds"].items()]
        return nat

    def render_block(self, data: dict) -> str:
        full = dict(data, native=self.native(data))
        return _render(self.TEMPLATE, L("généré par Roudix Config — modifie-le via l'app",
                                        "generated by Roudix Config — edit it through the app"), full)


# ───────────────────────── Niri ─────────────────────────

def _kdl_text(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return f"{v:g}" if isinstance(v, float) else str(v)
    return v if re.fullmatch(r"[A-Za-z0-9_./%+\-]+", v) and not re.fullmatch(r"[+-]?\d[\d.]*", v) \
        else json.dumps(v, ensure_ascii=False)


def niri_action_text(node: Node) -> str:
    parts = [node.name] + [_kdl_text(a) for a in node.args] + [f"{k}={_kdl_text(v)}" for k, v in node.props.items()]
    return " ".join(parts)


def parse_niri_action(text: str) -> tuple[str, list]:
    """'spawn "a b" 3 focus=false' -> ('spawn', ['a b', 3, {'focus': False}])"""
    try:
        toks = shlex.split(text.strip())
    except ValueError as e:
        raise ValueError(L("Action : guillemets mal fermés", "Action: unbalanced quotes")) from e
    if not toks:
        raise ValueError(L("Action vide", "Empty action"))
    name, args, props = toks[0], [], {}

    def conv(w: str):
        if w in ("true", "false"):
            return w == "true"
        if re.fullmatch(r"[+-]?\d+", w):
            return int(w)
        if re.fullmatch(r"[+-]?\d+\.\d+", w):
            return float(w)
        return w
    for t in toks[1:]:
        m = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*)=(.+)", t)
        if m:
            props[m.group(1)] = conv(m.group(2))
        else:
            args.append(conv(t))
    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        raise ValueError(L("Nom d'action invalide (ex. spawn, close-window, focus-workspace)",
                           "Invalid action name (e.g. spawn, close-window, focus-workspace)"))
    return name, args + ([props] if props else [])


class Niri(Backend):
    id = "niri"
    custom_name = "niri-custom.nix"
    label = "Niri"
    binds_mode = "keys"
    can_delete_binds = False
    can_move_binds = False
    workspace_names = False
    cli = "niri"

    TEMPLATE = _HEAD + """\
        n = data.native or {{ }};
        force = lib.mapAttrsRecursive (_: lib.mkForce);
      in
      {{
        # window-rules: appended AFTER the repo's (niri applies later rules last).
        # outputs: per-leaf mkForce. binds: only the keys you changed/added; the whole
        # `action` is forced (niri-flake requires exactly one action per bind).
        # (modifiers go on each field, never around the whole `settings`: niri-flake's
        # submodule type doesn't accept a wrapped value there.)
        programs.niri.settings =
          {{ window-rules = lib.mkAfter (n.window-rules or [ ]); }}
          // lib.optionalAttrs (n ? settings) (force n.settings)
          // lib.optionalAttrs (n ? outputs) {{ outputs = force n.outputs; }}
          // lib.optionalAttrs (n ? binds) {{
            binds = lib.mapAttrs (_: b: {{ action = lib.mkForce b.action; }}) n.binds;
          }};
      }})
    {end}
"""

    def action_help(self) -> str:
        return 'spawn "ghostty" · close-window · focus-workspace "web" · spawn-sh "noctalia msg …"'

    def workspace_choices(self) -> list[tuple[str, object]]:
        names: list[str] = []
        ws = _run_json(["niri", "msg", "--json", "workspaces"])
        for w in _collect(ws, "output") if ws is not None else []:   # idx/id are ints, output is a string
            if w.get("name") and w["name"] not in names:
                names.append(w["name"])
        for n in self._kdl():
            if n.name == "workspace" and n.args and str(n.args[0]) not in names:
                names.append(str(n.args[0]))
        return [(n, n) for n in names]

    def _kdl(self) -> list[Node]:
        try:
            return parse_kdl((config_home() / "niri" / "config.kdl").read_text())
        except (OSError, KdlError, ValueError, IndexError):
            return []

    def list_windows(self) -> list[dict]:
        data = _run_json(["niri", "msg", "--json", "windows"])
        seen: dict[str, dict] = {}
        for w in _collect(data, "app_id") if data is not None else []:
            a = w.get("app_id") or ""
            if a and a not in seen:
                seen[a] = {"app_id": a, "title": w.get("title", "")}
        return list(seen.values())

    def outputs_runtime(self) -> dict[str, dict]:
        data = _run_json(["niri", "msg", "--json", "outputs"])
        res: dict[str, dict] = {}
        for o in _collect(data, "name") if data is not None else []:
            modes = [f"{m['width']}x{m['height']}@{_fmt_refresh(m['refresh_rate'])}"
                     for m in o.get("modes", []) or [] if "width" in m]
            cur = o.get("current_mode")
            res[o["name"]] = {"modes": list(dict.fromkeys(modes)),
                              "current": modes[cur] if isinstance(cur, int) and 0 <= cur < len(modes) else None}
        return res

    def load_live(self) -> dict:
        nodes = self._kdl()
        live: dict = {"output": {}, "binds": {}}
        for n in nodes:
            if n.name == "output" and n.args:
                cfg: dict = {}
                for c in n.children:
                    if c.name == "mode" and c.args:
                        cfg["mode"] = _norm_mode(c.args[0])
                    elif c.name == "scale" and c.args:
                        cfg["scale"] = float(c.args[0])
                    elif c.name == "transform" and c.args:
                        cfg["transform"] = str(c.args[0])
                live["output"][str(n.args[0])] = cfg
            elif n.name == "binds":
                for b in n.children:
                    act = b.children[0] if b.children else None
                    if act is not None:
                        live["binds"][b.name] = niri_action_text(act)
        live["nodes"] = nodes          # for the Settings tab (live_setting)
        return live

    def settings_catalog(self) -> list:
        return NIRI_SETTINGS

    def live_setting(self, live: dict, s):
        nodes = live.get("nodes") or []
        if not nodes:
            return None                # no config.kdl read: absence would be meaningless
        cur = None
        level = nodes
        for name in s.kdl:
            cur = next((n for n in level if n.name == name), None)
            if cur is None:
                break
            level = cur.children
        if s.kind == "bool":
            return (cur is None) if s.invert else (cur is not None)
        if cur is None or not cur.args:
            return None
        v = cur.args[0]
        if s.kind == "int":
            return int(float(v))
        if s.kind == "float":
            return float(v)
        return str(v)

    def native_settings(self, values: dict) -> dict:
        out: dict = {}
        for s in self._chosen(values):
            _nest(out, s.path.split("."), values[s.id])
        return out

    def effective_outputs(self, live: dict, ov: dict) -> dict[str, dict]:
        out = {n: dict(c) for n, c in (live.get("output") or {}).items()}
        for n, c in (ov.get("output") or {}).items():
            out.setdefault(n, {}).update({k: v for k, v in c.items() if k != "workspaces"})
        return out

    def effective_binds(self, live: dict, ov: dict) -> dict:
        table = dict(live.get("binds") or {})
        table.update(ov.get("keybinds") or {})
        return table

    def validate_bind(self, key: str, action: str) -> None:
        super().validate_bind(key, action)
        parse_niri_action(action)

    def set_bind(self, table: dict, key: str, action: str, old_key: str | None = None) -> dict:
        self.validate_bind(key, action)
        if old_key and old_key != key:
            raise ValueError(L("Niri : déplacer un raccourci n'est pas pris en charge (utilise l'onglet Fichier).",
                               "Niri: moving a shortcut isn't supported (use the File tab)."))
        # overrides.keybinds only holds what changed
        new = dict(table)
        new[key.strip()] = action.strip()
        return new

    # neutral rule -> niri-flake window rule
    def native_window_rule(self, r: dict) -> dict:
        match = {"app-id": r["match"]["app_id"]} if "app_id" in r["match"] else {}
        if "title" in r["match"]:
            match["title"] = r["match"]["title"]
        rule: dict = {"matches": [match]}
        if "default_output" in r:
            rule["open-on-output"] = r["default_output"]
        if "default_workspace" in r:
            rule["open-on-workspace"] = str(r["default_workspace"])
        if r.get("default_floating"):
            rule["open-floating"] = True
        if r.get("default_maximize"):
            rule["open-maximized"] = True
        if r.get("default_fullscreen"):
            rule["open-fullscreen"] = True
        if "blur" in r:                       # niri-flake: background-effect { blur … }
            rule["background-effect"] = {"blur": r["blur"]}
        if "opacity" in r:
            rule["opacity"] = float(r["opacity"])
        return rule

    def preview_rule(self, rule: dict) -> str:
        nat = self.native_window_rule(rule)
        lines = ["window-rule {"]
        for m in nat["matches"]:
            lines.append("    match " + " ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in m.items()))
        for k, v in nat.items():
            if k == "matches":
                continue
            if isinstance(v, dict):
                lines.append(f"    {k} {{ " + " ".join(f"{a} {_kdl_text(b)};" for a, b in v.items()) + " }")
            else:
                lines.append(f"    {k} {_kdl_text(v)}")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def native_transform(t: str) -> dict:
        if t in (None, "", "normal"):
            return {"rotation": 0, "flipped": False}
        flipped = t.startswith("flipped")
        rot = re.search(r"(\d+)$", t)
        return {"rotation": int(rot.group(1)) if rot else 0, "flipped": flipped}

    def native(self, data: dict) -> dict:
        ov = data.get("overrides", {})
        nat: dict = {"window-rules": [self.native_window_rule(r) for r in data.get("window_rule", [])]}
        outs: dict = {}
        for name, c in (ov.get("output") or {}).items():
            o: dict = {}
            if "mode" in c:
                w, h, r = mode_from_string(c["mode"])
                o["mode"] = {"width": w, "height": h, "refresh": r}
            if "scale" in c:
                o["scale"] = float(c["scale"])
            if "transform" in c:
                o["transform"] = self.native_transform(c["transform"])
            if o:
                outs[name] = o
        if outs:
            nat["outputs"] = outs
        binds = {}
        for key, text in (ov.get("keybinds") or {}).items():
            name, args = parse_niri_action(text)
            binds[key] = {"action": {name: args if args else {}}}
        if binds:
            nat["binds"] = binds
        st = self.native_settings(ov.get("settings") or {})
        if st:
            nat["settings"] = st
        return nat

    def render_block(self, data: dict) -> str:
        full = dict(data, native=self.native(data))
        return _render(self.TEMPLATE, L("généré par Roudix Config — modifie-le via l'app",
                                        "generated by Roudix Config — edit it through the app"), full)


BACKENDS: dict[str, Backend] = {b.id: b for b in (Umbriel(), Niri(), Mango())}

#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (ps: [ ps.textual ])"
"""roudix-config (terminal) — configure Umbriel, Niri or MangoWC from a menu instead of writing Nix.

Everything it manages lives in ONE marked block inside your own
modules/home/<compositor>-custom.nix (gitignored; copied from the .example if it
doesn't exist yet). The block is readable and the tool reads it back, so you can
add, edit or remove what it wrote earlier; everything outside the block is
yours and is never touched (the File tab edits the whole file).

Tabs: window rules · screens (& workspaces where supported) · shortcuts · file.
It configures the compositor selected by roudix.desktop.type (not on
GNOME / KDE / Cinnamon, where it stays unavailable).

    roudix-config-tui            # TUI (run it inside your session)
    roudix-config-tui --list     # print the managed rules
    roudix-config-tui --bootstrap-only

Then rebuild (F5 runs `nh os switch` right here, or the `rebuild` alias) and reload the config.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
for _p in (_here.parent / "lib" / "roudix-config", _here):  # package layout, then checkout
    sys.path.insert(0, str(_p))
from roudix_config_core import *  # noqa: F401,F403  (shared logic)
from roudix_config_core import _collect, _run_json  # noqa: F401
from roudix_config_backends import GROUPS, _coerce_setting  # noqa: E402

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
    UNSET = tr("(unchanged)")

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
        BINDINGS = [("ctrl+s", "save", tr("Save")), ("escape", "cancel", tr("Cancel"))]

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
                yield Button(tr("Save"), variant="success", id="save")
                yield Button(tr("Cancel"), id="cancel")

    # ── window rules ──
    class RuleForm(Modal):
        def __init__(self, sources, outputs, initial: dict | None = None):
            super().__init__()
            B = backend()
            self.sources, self.outputs, self.initial = sources, outputs, initial
            self.shown = list(sources)
            self.place_keys = [k for k in PLACEMENTS if k in B.placements]
            self.blur_values = list(B.blur_choices)
            self.ws_choices = B.workspace_choices()

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
                yield Label(tr("Window rule — Ctrl+S save · Esc cancel"))
                with VerticalScroll(id="form"):
                    yield Label(tr("App — ● open now · ○ seen open before · no symbol = installed"))
                    yield Input(id="search", placeholder=tr("Search an app…"))
                    yield OptionList(*[Option(i["label"]) for i in self.sources], id="sources")
                    yield Label(tr("app_id (regex — filled as ^…$ when you pick an app)"))
                    yield Input(id="app_id", placeholder="ex. ^obs$")
                    yield Label(tr("Title (regex, optional)"))
                    yield Input(id="title_re", placeholder="ex. Picture-in-Picture")
                    yield Label(tr("Screen"))
                    yield Select([(o, o) for o in self.outputs], id="output", prompt=UNSET, allow_blank=True)
                    yield Label(tr("Workspace"))
                    yield Select([(lab, val) for lab, val in self.ws_choices], id="ws", prompt=UNSET, allow_blank=True)
                    yield Label(tr("Placement"))
                    yield Select([(placement_label(k), k) for k in self.place_keys], id="place", prompt=UNSET, allow_blank=True)
                    yield Label(tr("Blur"))
                    yield Select([(blur_label(v), v) for v in self.blur_values], id="blur", prompt=UNSET, allow_blank=True)
                    yield Label(tr("Opacity (0 to 1, optional)"))
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
            for k in self.place_keys:
                if r.get(PLACEMENTS[k]):
                    put(self.query_one("#place", Select), k)
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
                raise ValueError(tr("opacity: a number between 0 and 1"))
            return build_rule(
                self.query_one("#app_id", Input).value.strip(),
                self.query_one("#title_re", Input).value.strip(),
                chosen(self.query_one("#output", Select)),
                chosen(self.query_one("#ws", Select)),
                chosen(self.query_one("#place", Select)),
                chosen(self.query_one("#blur", Select)),
                opacity,
            )

        def refresh_preview(self) -> None:
            prev, err = self.query_one("#preview", Static), self.query_one("#error", Static)
            try:
                prev.update(rule_preview(self.result()))
                err.update("")
            except ValueError as e:
                prev.update("")
                err.update(str(e))

    # ── outputs ──
    class OutputForm(Modal):
        def __init__(self, name: str | None, names: list[str], cfg: dict, live: dict[str, dict]):
            super().__init__()
            self.name0, self.names, self.cfg, self.live = name, names, cfg, live
            self.has_ws = backend().workspace_names

        def compose(self) -> ComposeResult:
            with Vertical(id="box"):
                yield Label(tr("Screen — Ctrl+S save · Esc cancel"))
                with VerticalScroll(id="form"):
                    yield Label(tr("Output"))
                    yield Select([(n, n) for n in self.names], id="name", allow_blank=False,
                                 value=self.name0 or (self.names[0] if self.names else BLANK))
                    yield Label(tr("Resolution / refresh rate (detected modes when the compositor runs)"))
                    yield Select([], id="modes", prompt=tr("(pick a mode)"), allow_blank=True)
                    yield Input(id="mode", placeholder='ex. 2560x1440@240.000')
                    yield Label(tr("Scale (0.25 to 4)"))
                    yield Input(id="scale", placeholder="ex. 1 ou 1.25")
                    yield Label(tr("Rotation"))
                    yield Select([(t, t) for t in TRANSFORMS], id="transform", prompt=UNSET, allow_blank=True)
                    if self.has_ws:
                        yield Label(tr("This screen's workspace names, separated by spaces"))
                        yield Input(id="workspaces", placeholder=tr("e.g.  web code chat   (or icons)"))
                        yield Static(tr("Avoid a purely numeric name that exists on one screen only: the compositor "
                                       "treats it as unique and Mod+N would always jump to that screen."))
                yield from self.footer_widgets()

        def on_mount(self) -> None:
            self.load_for(self.query_one("#name", Select).value)

        def load_for(self, name) -> None:
            cfg = self.cfg.get(name, {}) if name else {}
            info = self.live.get(name, {}) if name else {}
            modes = self.query_one("#modes", Select)
            cur = tr(" (current)")
            modes.set_options([(m + (cur if m == info.get("current") else ""), m) for m in info.get("modes", [])])
            self.query_one("#mode", Input).value = str(cfg.get("mode", ""))
            self.query_one("#scale", Input).value = "" if "scale" not in cfg else str(cfg["scale"])
            put(self.query_one("#transform", Select), cfg.get("transform", BLANK))
            if self.has_ws:
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
                raise ValueError(tr("pick an output"))
            ch: dict = {}
            mode = self.query_one("#mode", Input).value.strip()
            if mode:
                if not re.fullmatch(r"\d+x\d+(@\d+(\.\d+)?)?", mode):
                    raise ValueError(tr("mode: use 2560x1440 or 2560x1440@240"))
                ch["mode"] = mode
            sc = self.query_one("#scale", Input).value.strip()
            if sc:
                try:
                    v = float(sc.replace(",", "."))
                except ValueError:
                    raise ValueError(tr("scale: a number"))
                if not 0.25 <= v <= 4.0:
                    raise ValueError(tr("scale between 0.25 and 4"))
                ch["scale"] = int(v) if v == int(v) else v
            transform = chosen(self.query_one("#transform", Select))
            if transform:
                ch["transform"] = transform
            if self.has_ws:
                ws = self.query_one("#workspaces", Input).value.split()
                if ws:
                    ch["workspaces"] = ws
            if not ch:
                raise ValueError(tr("nothing to save"))
            return name, ch

    # ── keybinds ──
    class BindForm(Modal):
        def __init__(self, key: str, action: str, known_actions: list[str]):
            super().__init__()
            self.key0, self.action0, self.known = key, action, known_actions
            B = backend()
            self.frozen = bool(key) and not B.can_move_binds

        def compose(self) -> ComposeResult:
            B = backend()
            with Vertical(id="box"):
                yield Label(tr("Shortcut — Ctrl+S save · Esc cancel"))
                with VerticalScroll(id="form"):
                    yield Label(tr("Shortcut. ") + B.key_help())
                    yield Input(id="key", value=self.key0, disabled=self.frozen)
                    if self.frozen:
                        yield Static(tr("An existing shortcut's key can't be changed here."))
                    yield Label(tr("Action. ") + B.action_help())
                    yield Input(id="action", value=self.action0)
                    yield Label(tr("Actions already in use (pick to fill in)"))
                    yield Select([(a[:70], a) for a in self.known], id="known", prompt=tr("(none)"), allow_blank=True)
                yield from self.footer_widgets()

        def on_select_changed(self, event) -> None:
            if chosen(event.select):
                self.query_one("#action", Input).value = chosen(event.select)

        def result(self):
            key = self.query_one("#key", Input).value.strip()
            action = self.query_one("#action", Input).value.strip()
            backend().validate_bind(key, action)       # keep the form open on a bad shortcut/action
            return key, action

    # ── curated settings ──
    class SettingForm(Modal):
        def __init__(self, spec, value):
            super().__init__()
            self.spec, self.value0 = spec, value

        def compose(self) -> ComposeResult:
            sp = self.spec
            with Vertical(id="box"):
                yield Label(f"{sp.title} — " + tr("Ctrl+S save · Esc cancel"))
                with VerticalScroll(id="form"):
                    if sp.kind == "bool":
                        yield Select([(tr("on"), True), (tr("off"), False)], id="val",
                                     value=bool(self.value0), allow_blank=False)
                    elif sp.kind == "choice":
                        yield Select([(c, c) for c in sp.choices], id="val",
                                     value=self.value0 if self.value0 in sp.choices else sp.choices[0], allow_blank=False)
                    else:
                        if sp.kind in ("int", "float"):
                            yield Label(tr("Value between {lo} and {hi}").format(lo=sp.lo, hi=sp.hi))
                        yield Input(id="val", value="" if self.value0 is None else str(self.value0))
                yield from self.footer_widgets()

        def result(self):
            sp = self.spec
            w = self.query_one("#val")
            raw = w.value if isinstance(w, Input) else chosen(w)
            try:
                return (_coerce_setting(sp, raw),)
            except (TypeError, ValueError) as e:
                raise ValueError(str(e) or tr("invalid value"))

    # ── main app ──
    class ConfigApp(App):
        TITLE = "roudix-config"
        BINDINGS = [("a", "add", tr("Add")), ("e", "edit", tr("Edit")),
                    ("d", "delete", tr("Delete")), ("r", "reset", tr("Reset")),
                    ("f5", "rebuild", tr("Rebuild")),
                    ("ctrl+s", "save_nix", tr("Save the .nix")), ("q", "quit", tr("Quit"))]
        CSS = "#status { margin: 0 2; } .hint { margin: 0 2; color: $text-muted; } TextArea { height: 1fr; }"

        def __init__(self, messages: list[str]):
            super().__init__()
            self.sub_title = backend().label
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
            txt = nix.read_text(encoding="utf-8") if nix.exists() else ""
            if txt != ta.text:
                ta.load_text(txt)
            self.nix_text = ta.text

        def blocked(self) -> bool:
            if self.tab() != "t-nix" and self.nix_dirty():
                self.status(tr("Unsaved changes in the File tab: Ctrl+S to keep them "
                              "(or leave without saving) before continuing."))
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
            B = backend()
            yield Header()
            with TabbedContent(id="tabs"):
                with TabPane(tr("Rules"), id="t-rules"):
                    yield DataTable(id="rules", cursor_type="row")
                    yield Static(tr("a add · e edit · d delete"), classes="hint")
                with TabPane(tr("Screens"), id="t-screens"):
                    yield DataTable(id="screens", cursor_type="row")
                    yield Static(tr("e edit (resolution, scale, rotation{names}) · r back to the output's defaults").format(names=(tr(", workspace names") if B.workspace_names else "")), classes="hint")
                with TabPane(tr("Shortcuts"), id="t-binds"):
                    yield DataTable(id="binds", cursor_type="row")
                    if B.binds_mode == "keys":
                        hint = tr("a add · e change the action · r reset everything\n{label}: moving or "
                                "deleting a default shortcut is done in the File tab. ✎ = changed by you.").format(label=B.label)
                    else:
                        hint = tr("a add · e edit · d delete · r reset everything\n"
                                 "Once changed, the table is frozen: new default shortcuts added to the repo "
                                 "won't reach you any more (r to go back).")
                    yield Static(hint, classes="hint")
                with TabPane(tr("Settings"), id="t-settings"):
                    yield DataTable(id="settings", cursor_type="row")
                    yield Static(tr("e edit · r restore this setting's default · F5 rebuild\n"
                                   "✎ = changed by you; the others follow the repo's defaults."), classes="hint")
                with TabPane(tr("File"), id="t-nix"):
                    yield TextArea("", id="nixedit", show_line_numbers=True)
                    yield Static(tr("Your {custom_name} file. Ctrl+S saves (.bak copy + syntax check).").format(custom_name=B.custom_name), classes="hint")
            yield Static("", id="status")
            yield Footer()

        def on_mount(self) -> None:
            self.query_one("#rules", DataTable).add_columns("app_id", tr("title"), tr("settings"))
            self.query_one("#screens", DataTable).add_columns(
                tr("output"), "mode", tr("scale"), tr("rotation"),
                *(["workspaces"] if backend().workspace_names else []))
            self.query_one("#binds", DataTable).add_columns(tr("shortcut"), "action")
            self.query_one("#settings", DataTable).add_columns(tr("group"), tr("setting"), tr("value"))
            nix = custom_path()
            ta = self.query_one("#nixedit", TextArea)
            ta.load_text(nix.read_text(encoding="utf-8") if nix.exists() else "")
            self.nix_text = ta.text
            self.render_all()
            self.status("\n".join(self.messages))

        # rendering
        def render_all(self) -> None:
            self.render_rules(); self.render_screens(); self.render_binds(); self.render_settings()

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
            B = backend()
            for n in self.screen_names():
                c = eff.get(n, {})
                row = [n, str(c.get("mode", "auto")), str(c.get("scale", 1)), str(c.get("transform", "normal"))]
                if B.workspace_names:
                    ws = c.get("workspaces")
                    row.append(" ".join(ws) if isinstance(ws, list) else str(ws or tr("dynamic")))
                t.add_row(*row, key=n)

        def binds(self) -> dict:
            return effective_binds(self.live(), get_overrides(self.data))

        def render_binds(self) -> None:
            t = self.query_one("#binds", DataTable); t.clear()
            B = backend()
            mine = get_overrides(self.data).get("keybinds") or {}
            for k, v in self.binds().items():
                t.add_row(k + ("  ✎" if B.binds_mode == "keys" and k in mine else ""), bind_action(v), key=k)

        @staticmethod
        def show_value(sp, v, changed: bool) -> str:
            txt = "—" if v is None else (tr("on") if v is True else tr("off") if v is False else str(v))
            return txt + ("  ✎" if changed else "")

        def render_settings(self) -> None:
            t = self.query_one("#settings", DataTable)
            keep = t.cursor_row
            t.clear()
            ov = get_overrides(self.data)
            mine = ov.get("settings") or {}
            eff = effective_settings(self.live(), ov)
            for sp in settings_catalog():
                t.add_row(GROUPS.get(sp.group, sp.group), sp.title, self.show_value(sp, eff.get(sp.id), sp.id in mine), key=sp.id)
            if t.row_count:
                t.move_cursor(row=min(keep, t.row_count - 1))

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
            elif tab == "t-settings":
                self.open_setting(self.cursor_key("#settings"))

        def action_delete(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-rules":
                t = self.query_one("#rules", DataTable)
                if t.row_count and 0 <= t.cursor_row < len(self.rules()):
                    del self.rules()[t.cursor_row]
                    self.persist(); self.render_rules()
                    self.status(tr("Rule deleted — rebuild required."))
            elif tab == "t-binds":
                if not backend().can_delete_binds:
                    self.status(tr("{label}: deleting a default shortcut is done in the File tab.").format(label=backend().label))
                    return
                k = self.cursor_key("#binds")
                if k:
                    table = self.binds(); table.pop(k, None)
                    save_binds_override(table); self.reload()
                    self.render_binds()
                    self.status(tr("{k} deleted — rebuild required.").format(k=k))

        def action_reset(self) -> None:
            if self.blocked():
                return
            tab = self.tab()
            if tab == "t-binds":
                reset_override("keybinds"); self.reload(); self.render_binds()
                self.status(tr("Shortcuts reset — rebuild required."))
            elif tab == "t-settings":
                k = self.cursor_key("#settings")
                if k:
                    reset_setting(k); self.reload(); self.render_settings()
                    self.status(tr("Setting restored — rebuild required (F5)."))
            elif tab == "t-screens":
                k = self.cursor_key("#screens")
                if k:
                    reset_override("output", k); self.reload(); self.render_screens()
                    self.status(tr("{k} reset — rebuild required.").format(k=k))

        def action_save_nix(self) -> None:
            if self.tab() != "t-nix":
                return
            ta = self.query_one("#nixedit", TextArea)
            ok, msg = nix_parse_check(ta.text)
            if not ok:
                self.status(tr("NOT saved — Nix error: {msg}").format(msg=msg))
                return
            nix = custom_path()
            if nix.exists():
                shutil.copyfile(nix, nix.with_name(nix.name + ".bak"))
            nix.write_text(ta.text, encoding="utf-8")
            self.nix_text = ta.text
            self.data = load_data()
            self.render_all()
            self.status(tr("{name} saved ({msg}). Previous version: {name}.bak — rebuild required.").format(name=nix.name, msg=msg))

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
                    self.persist(); self.render_rules()
                    self.status(tr("Rule saved — rebuild required."))
            self.push_screen(RuleForm(sources, list_outputs(), initial), done)

        def open_output(self, name) -> None:
            names = self.screen_names()
            eff = effective_outputs(self.live(), get_overrides(self.data))

            def done(res):
                if res:
                    n, ch = res
                    save_output_override(n, ch); self.reload(); self.render_screens()
                    self.status(tr("{n} saved — rebuild required.").format(n=n))
            self.push_screen(OutputForm(name, names, eff, list_outputs_full()), done)

        def open_setting(self, sid) -> None:
            sp = next((x for x in settings_catalog() if x.id == sid), None)
            if sp is None:
                return
            ov = get_overrides(self.data)
            cur = effective_settings(self.live(), ov).get(sid)

            def done(res):
                if res is None:
                    return
                try:
                    set_setting_override(sid, res[0])
                except ValueError as e:
                    self.status(str(e)); return
                self.reload(); self.render_settings()
                self.status(tr("{title} saved — rebuild required (F5).").format(title=sp.title))
            self.push_screen(SettingForm(sp, cur), done)

        def action_rebuild(self) -> None:
            if self.blocked():
                return
            try:
                argv = rebuild_argv()
            except ValueError as e:
                self.status(str(e)); return
            import subprocess
            try:
                with self.suspend():
                    print("\n$ " + " ".join(argv) + "\n")
                    rc = subprocess.run(argv).returncode
                    print("\n" + (tr("Rebuild done ✔") if rc == 0
                                   else tr("Rebuild failed ✘ (code {rc})").format(rc=rc)))
                    input(tr("Press Enter to return to roudix-config… "))
            except Exception as e:  # noqa: BLE001 - suspend() unsupported (old textual) or no tty
                self.status(tr("Can't rebuild from the TUI ({e}): run the `rebuild` alias.").format(e=e))
                return
            self.reload(); self.render_all()
            self.status(tr("Rebuild finished (see the terminal) — reload the compositor config if needed."))

        def open_bind(self, key) -> None:
            table = self.binds()
            known = sorted({bind_action(v) for v in table.values()})
            action = bind_action(table[key]) if key in table else ""
            B = backend()

            def done(res):
                if res:
                    k, a = res
                    try:
                        new = set_bind(table, k, a, old_key=key)
                    except ValueError as e:
                        self.status(str(e)); return
                    if B.binds_mode == "keys":           # only what differs from the live config is kept
                        live = effective_binds(self.live(), {})
                        new = {kk: vv for kk, vv in new.items() if live.get(kk) != vv}
                    save_binds_override(new); self.reload(); self.render_binds()
                    self.status(tr("{k} → {a} saved — rebuild required.").format(k=k, a=a))
            self.push_screen(BindForm(key or "", action, known), done)

    return ConfigApp(bootstrap())


def run_tui() -> None:
    make_app().run()


# ───────────────────────── entry point ─────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=tr("Configure Umbriel, Niri or MangoWC without writing Nix."))
    ap.add_argument("--list", action="store_true", help=tr("print the managed rules and exit"))
    ap.add_argument("--bootstrap-only", action="store_true",
                    help=tr("only create the -custom.nix file, then exit"))
    args = ap.parse_args()

    reason = availability()
    if reason and not args.list:
        sys.exit(reason)

    if args.list:
        for r in load_rules():
            print(rule_preview(r), end="\n\n")
        return
    if args.bootstrap_only:
        for m in bootstrap() or [tr("Nothing to do.")]:
            print(m)
        return
    run_tui()


if __name__ == "__main__":
    main()

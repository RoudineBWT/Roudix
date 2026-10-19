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

    roudix-config-tui            # TUI (run it inside your session)
    roudix-config-tui --list     # print the managed rules
    roudix-config-tui --bootstrap-only

Then rebuild (`rebuild`) and reload the config (Mod+Shift+R).
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

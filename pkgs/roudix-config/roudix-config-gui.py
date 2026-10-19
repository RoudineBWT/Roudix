#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (ps: [ ps.pygobject3 ])" gtk4 libadwaita gobject-introspection adwaita-icon-theme
"""roudix-config-gui — GTK4/libadwaita front-end of roudix-config (Umbriel, Niri, MangoWC).

Same engine as the TUI (roudix_config_core.py): everything it manages lives in
one marked block of your own modules/home/<compositor>-custom.nix; what is outside
the block is yours and never touched. Pages: window rules, screens &
workspaces, keybinds, and the -custom.nix file itself.

Launch it inside your session (so open windows and outputs are live):
    roudix-config   (or pkgs/roudix-config/roudix-config-gui.py from a checkout)
Then rebuild and reload the config (Mod+Shift+R).
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
for _p in (_here.parent / "lib" / "roudix-config", _here):  # package layout, then checkout
    sys.path.insert(0, str(_p))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk, Pango  # noqa: E402

from roudix_config_core import (  # noqa: E402
    PLACEMENTS, TRANSFORMS, L, availability, backend, bind_action, blur_label, bootstrap, build_rule,
    build_sources, custom_path, effective_binds, effective_outputs, get_overrides, list_desktop_apps,
    list_outputs, list_outputs_full, list_windows, load_data, load_live, load_seen, nix_parse_check,
    placement_label, remember_windows, reset_override, rule_preview, rule_summary, save_binds_override,
    save_data, save_output_override, set_bind,
)

APP_ID = "io.roudix.config"
UNSET = L("(inchangé)", "(unchanged)")


# ───────────────────────── small widget helpers ─────────────────────────

def combo(title: str, options: list[str], subtitle: str = "", searchable: bool = False) -> Adw.ComboRow:
    row = Adw.ComboRow(title=title, subtitle=subtitle, model=Gtk.StringList.new(options))
    if searchable:
        row.set_enable_search(True)
        row.set_expression(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
    return row


def entry(title: str, text: str = "") -> Adw.EntryRow:
    row = Adw.EntryRow(title=title)
    row.set_text(text)
    return row


def plain(row) -> None:
    """Rows show Pango markup by default: regexes contain & < >."""
    try:
        row.set_use_markup(False)
    except Exception:
        pass


def clear(listbox: Gtk.ListBox) -> None:
    while (child := listbox.get_first_child()) is not None:
        listbox.remove(child)


def icon_button(icon: str, tooltip: str, cb) -> Gtk.Button:
    b = Gtk.Button(icon_name=icon, tooltip_text=tooltip, valign=Gtk.Align.CENTER)
    b.add_css_class("flat")
    b.connect("clicked", lambda *_: cb())
    return b


# ───────────────────────── dialogs ─────────────────────────

class FormDialog(Adw.Window):
    """Modal form: header with Cancel / Save, a preferences page as body."""

    def __init__(self, parent: Gtk.Window, title: str, on_done, width: int = 560, height: int = 720):
        super().__init__(transient_for=parent, modal=True, title=title,
                         default_width=width, default_height=height)
        self.on_done = on_done
        self.overlay = Adw.ToastOverlay()
        self.page = Adw.PreferencesPage()
        self.overlay.set_child(self.page)

        header = Adw.HeaderBar()
        cancel = Gtk.Button(label=L("Annuler", "Cancel"))
        cancel.connect("clicked", lambda *_: self.close())
        save = Gtk.Button(label=L("Enregistrer", "Save"))
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self.save())
        header.pack_start(cancel)
        header.pack_end(save)

        self.view = Adw.ToolbarView(content=self.overlay)
        self.view.add_top_bar(header)
        self.set_content(self.view)

        keys = Gtk.ShortcutController()
        keys.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("<Control>Return"),
                                           Gtk.CallbackAction.new(lambda *_: self.save() or True)))
        self.add_controller(keys)

    def bottom(self, widget: Gtk.Widget) -> None:
        """Always-visible strip under the scrolling form."""
        box = Gtk.Box(margin_top=8, margin_bottom=8, margin_start=16, margin_end=16)
        box.append(widget)
        self.view.add_bottom_bar(box)

    def group(self, title: str = "", description: str = "") -> Adw.PreferencesGroup:
        g = Adw.PreferencesGroup(title=title, description=description)
        self.page.add(g)
        return g

    def error(self, msg: str) -> None:
        self.overlay.add_toast(Adw.Toast(title=msg, timeout=4))

    def result(self):  # pragma: no cover - implemented by subclasses
        raise NotImplementedError

    def save(self) -> None:
        try:
            res = self.result()
        except ValueError as e:
            self.error(str(e))
            return
        self.close()
        self.on_done(res)


class RuleDialog(FormDialog):
    def __init__(self, parent, sources, outputs, initial, on_done):
        super().__init__(parent, L("Règle de fenêtre", "Window rule"), on_done)
        B = backend()
        self.sources, self.outputs = sources, outputs
        self.place_keys = [k for k in PLACEMENTS if k in B.placements]
        self.blur_values = list(B.blur_choices)
        self.ws_choices = B.workspace_choices()

        g = self.group(L("Application", "Application"),
                       L("● ouverte maintenant · ○ déjà vue ouverte · sans symbole : installée (l'app_id est alors deviné)",
                         "● open now · ○ seen open before · no symbol: installed (the app_id is then a guess)"))
        self.pick = combo(L("Choisir une app", "Pick an app"),
                          [L("(saisir à la main)", "(type it by hand)")] + [s["label"].strip() for s in sources],
                          searchable=True)
        self.pick.connect("notify::selected", self.on_pick)
        g.add(self.pick)
        self.app_id = entry(L("app_id (regex)", "app_id (regex)"))
        self.title_re = entry(L("Titre (regex, optionnel)", "Title (regex, optional)"))
        g.add(self.app_id)
        g.add(self.title_re)

        g2 = self.group(L("Réglages (laisser « inchangé » pour ne rien forcer)",
                          "Settings (leave “unchanged” to force nothing)"))
        self.output = combo(L("Écran", "Screen"), [UNSET] + outputs)
        self.ws = combo(L("Workspace", "Workspace"), [UNSET] + [lab for lab, _ in self.ws_choices])
        self.place = combo(L("Placement", "Placement"), [UNSET] + [placement_label(k) for k in self.place_keys])
        self.blur = combo(L("Flou (blur)", "Blur"), [UNSET] + [blur_label(v) for v in self.blur_values])
        self.opacity = entry(L("Opacité (0 à 1, optionnel)", "Opacity (0 to 1, optional)"))
        for w in (self.output, self.ws, self.place, self.blur, self.opacity):
            g2.add(w)

        self.preview = Gtk.Label(xalign=0, selectable=True, wrap=True, hexpand=True)
        self.preview.add_css_class("monospace")
        self.bottom(self.preview)

        if initial:
            self.app_id.set_text(initial["match"].get("app_id", ""))
            self.title_re.set_text(initial["match"].get("title", ""))
            if initial.get("default_output") in outputs:
                self.output.set_selected(outputs.index(initial["default_output"]) + 1)
            vals = [v for _, v in self.ws_choices]
            if initial.get("default_workspace") in vals:
                self.ws.set_selected(vals.index(initial["default_workspace"]) + 1)
            for i, k in enumerate(self.place_keys):
                if initial.get(PLACEMENTS[k]):
                    self.place.set_selected(i + 1)
            if "blur" in initial and initial["blur"] in self.blur_values:
                self.blur.set_selected(self.blur_values.index(initial["blur"]) + 1)
            if "opacity" in initial:
                self.opacity.set_text(str(initial["opacity"]))

        for w in (self.output, self.ws, self.place, self.blur):
            w.connect("notify::selected", lambda *_: self.refresh())
        for w in (self.app_id, self.title_re, self.opacity):
            w.connect("changed", lambda *_: self.refresh())
        self.refresh()

    def on_pick(self, *_):
        i = self.pick.get_selected()
        if 1 <= i <= len(self.sources):
            self.app_id.set_text(self.sources[i - 1]["pattern"])

    def result(self) -> dict:
        op = self.opacity.get_text().strip()
        try:
            opacity = float(op) if op else None
        except ValueError:
            raise ValueError(L("Opacité : un nombre entre 0 et 1", "Opacity: a number between 0 and 1"))
        o, w, p, b = (self.output.get_selected(), self.ws.get_selected(),
                      self.place.get_selected(), self.blur.get_selected())
        return build_rule(
            self.app_id.get_text().strip(), self.title_re.get_text().strip(),
            self.outputs[o - 1] if o > 0 else None,
            self.ws_choices[w - 1][1] if w > 0 else None,
            self.place_keys[p - 1] if p > 0 else None,
            self.blur_values[b - 1] if b > 0 else None,
            opacity,
        )

    def refresh(self) -> None:
        try:
            self.preview.set_text(rule_preview(self.result()))
        except ValueError as e:
            self.preview.set_text(f"⚠ {e}")


class OutputDialog(FormDialog):
    def __init__(self, parent, name, names, cfg, live, on_done):
        super().__init__(parent, L("Écran", "Screen"), on_done, height=760)
        B = backend()
        self.names, self.cfg, self.live = names, cfg, live
        g = self.group(L("Sortie", "Output"))
        self.name = combo(L("Écran", "Screen"), names)
        g.add(self.name)

        g2 = self.group(L("Affichage", "Display"),
                        L("Le format du mode est 2560x1440 ou 2560x1440@240.000",
                          "The mode format is 2560x1440 or 2560x1440@240.000"))
        self.modes = combo(L("Modes détectés (le compositeur doit tourner)", "Detected modes (the compositor must be running)"),
                           [L("(choisir)", "(pick one)")])
        self.mode = entry(L("Résolution / fréquence", "Resolution / refresh rate"))
        self.scale = entry(L("Échelle (0.25 à 4)", "Scale (0.25 to 4)"))
        self.transform = combo(L("Rotation", "Rotation"), [UNSET] + TRANSFORMS)
        for w in (self.modes, self.mode, self.scale, self.transform):
            g2.add(w)

        self.workspaces = None
        if B.workspace_names:
            g3 = self.group(L("Workspaces", "Workspaces"),
                            L("Noms séparés par des espaces. Évite un nom purement numérique présent sur un seul écran : "
                              "le compositeur le traite comme unique et Mod+N sauterait toujours vers cet écran.",
                              "Names separated by spaces. Avoid a purely numeric name that exists on one screen only: "
                              "the compositor treats it as unique and Mod+N would always jump to that screen."))
            self.workspaces = entry(L("Noms des workspaces de cet écran", "This screen's workspace names"))
            g3.add(self.workspaces)

        if name in names:
            self.name.set_selected(names.index(name))
        self.name.connect("notify::selected", lambda *_: self.load_for())
        self.modes.connect("notify::selected", self.on_mode_pick)
        self._modes: list[str] = []
        self.load_for()

    def current_name(self):
        return self.names[self.name.get_selected()] if self.names else None

    def load_for(self) -> None:
        n = self.current_name()
        cfg = self.cfg.get(n, {})
        info = self.live.get(n, {})
        self._modes = info.get("modes", [])
        cur = L(" (actuel)", " (current)")
        self.modes.set_model(Gtk.StringList.new(
            [L("(choisir)", "(pick one)")] + [m + (cur if m == info.get("current") else "") for m in self._modes]))
        self.mode.set_text(str(cfg.get("mode", "")))
        self.scale.set_text("" if "scale" not in cfg else str(cfg["scale"]))
        t = cfg.get("transform")
        self.transform.set_selected(TRANSFORMS.index(t) + 1 if t in TRANSFORMS else 0)
        if self.workspaces is not None:
            ws = cfg.get("workspaces")
            self.workspaces.set_text(" ".join(ws) if isinstance(ws, list) else "")

    def on_mode_pick(self, *_):
        i = self.modes.get_selected()
        if 1 <= i <= len(self._modes):
            self.mode.set_text(self._modes[i - 1])

    def result(self):
        import re
        name = self.current_name()
        if not name:
            raise ValueError(L("Choisis un écran", "Pick a screen"))
        ch: dict = {}
        mode = self.mode.get_text().strip()
        if mode:
            if not re.fullmatch(r"\d+x\d+(@\d+(\.\d+)?)?", mode):
                raise ValueError(L("Mode : format 2560x1440 ou 2560x1440@240", "Mode: use 2560x1440 or 2560x1440@240"))
            ch["mode"] = mode
        sc = self.scale.get_text().strip()
        if sc:
            try:
                v = float(sc.replace(",", "."))
            except ValueError:
                raise ValueError(L("Échelle : un nombre", "Scale: a number"))
            if not 0.25 <= v <= 4.0:
                raise ValueError(L("Échelle entre 0.25 et 4", "Scale between 0.25 and 4"))
            ch["scale"] = int(v) if v == int(v) else v
        t = self.transform.get_selected()
        if t > 0:
            ch["transform"] = TRANSFORMS[t - 1]
        if self.workspaces is not None:
            ws = self.workspaces.get_text().split()
            if ws:
                ch["workspaces"] = ws
        if not ch:
            raise ValueError(L("Rien à enregistrer", "Nothing to save"))
        return name, ch


class BindDialog(FormDialog):
    def __init__(self, parent, key, action, known, on_done):
        super().__init__(parent, L("Raccourci", "Shortcut"), on_done, height=840)
        B = backend()
        self.B, self.known = B, known
        self._lock = False
        editing = bool(key)
        frozen = editing and not B.can_move_binds     # e.g. Niri: only the action may change

        g = self.group(L("Touches", "Keys"), B.key_help())
        self.mod_rows: dict[str, Adw.SwitchRow] = {}
        for m in B.modifiers:
            r = Adw.SwitchRow(title=m)
            r.connect("notify::active", lambda *_: self.compose_raw())
            r.set_sensitive(not frozen)
            self.mod_rows[m] = r
            g.add(r)
        self.key = entry(L("Touche", "Key"))
        self.key.connect("changed", lambda *_: self.compose_raw())
        self.key.set_sensitive(not frozen)
        g.add(self.key)

        g2 = self.group(L("Résultat", "Result"),
                        L("Niri : la touche d'un raccourci existant n'est pas modifiable ici.",
                          "Niri: an existing shortcut's key can't be changed here.") if frozen else "")
        self.raw = entry(L("Raccourci complet (modifiable)", "Full shortcut (editable)"))
        self.raw.connect("changed", lambda *_: self.parse_raw())
        self.raw.set_sensitive(not frozen)
        g2.add(self.raw)

        g3 = self.group(L("Action", "Action"), B.action_help())
        self.action = entry(L("Action", "Action"))
        self.action.set_text(action)
        self.known_row = combo(L("Actions déjà utilisées", "Actions already in use"),
                               [L("(choisir pour remplir)", "(pick to fill in)")] + [k[:80] for k in known],
                               searchable=True)
        self.known_row.connect("notify::selected", self.on_known)
        g3.add(self.action)
        g3.add(self.known_row)

        self.raw.set_text(key)
        self.parse_raw()

    def compose_raw(self) -> None:
        if self._lock:
            return
        self._lock = True
        mods = [m for m in self.B.modifiers if self.mod_rows[m].get_active()]
        self.raw.set_text(self.B.compose_key(mods, self.key.get_text().strip()))
        self._lock = False

    def parse_raw(self) -> None:
        if self._lock:
            return
        self._lock = True
        mods, key = self.B.parse_key(self.raw.get_text())
        up = {m.lower() for m in mods}
        for m in self.B.modifiers:
            self.mod_rows[m].set_active(m.lower() in up)
        self.key.set_text(key)
        self._lock = False

    def on_known(self, *_):
        i = self.known_row.get_selected()
        if 1 <= i <= len(self.known):
            self.action.set_text(self.known[i - 1])

    def result(self):
        key, action = self.raw.get_text().strip(), self.action.get_text().strip()
        self.B.validate_bind(key, action)          # keep the dialog open on a bad shortcut/action
        return key, action


# ───────────────────────── main window ─────────────────────────

class ConfigWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, messages: list[str]):
        super().__init__(application=app, title=f"Roudix Config — {backend().label}",
                         default_width=920, default_height=720)
        self.data = load_data()
        self.nix_text = ""
        self.overlay = Adw.ToastOverlay()

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.rules_list = self.make_list_page("rules", L("Règles", "Rules"))
        self.screens_list = self.make_list_page("screens", L("Écrans", "Screens"))
        self.binds_list = self.make_list_page("binds", L("Raccourcis", "Shortcuts"), searchable=True,
                                              hint=self.binds_hint())
        self.make_nix_page()

        # Text-only tabs: AdwViewSwitcher always draws an icon (a "missing image"
        # placeholder when the page has none), so use a plain StackSwitcher.
        switcher = Gtk.StackSwitcher(stack=self.stack)
        header = Adw.HeaderBar(title_widget=switcher)
        self.add_btn = Gtk.Button(icon_name="list-add-symbolic", tooltip_text=L("Ajouter", "Add"))
        self.add_btn.connect("clicked", lambda *_: self.on_add())
        self.reset_btn = Gtk.Button(label=L("Tout remettre par défaut", "Reset everything"),
                                    tooltip_text=L("Abandonne tes changements de raccourcis", "Discards your shortcut changes"))
        self.reset_btn.connect("clicked", lambda *_: self.on_reset())
        self.save_btn = Gtk.Button(label=L("Sauvegarder", "Save"))
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", lambda *_: self.save_nix())
        header.pack_start(self.add_btn)
        header.pack_start(self.reset_btn)
        header.pack_end(self.save_btn)

        view = Adw.ToolbarView(content=self.stack)
        view.add_top_bar(header)
        self.overlay.set_child(view)
        self.set_content(self.overlay)

        self.render_all()
        self.refresh_nix()
        self.on_page()
        self.stack.connect("notify::visible-child-name", self.on_page)
        for m in messages:
            self.toast(m)

    @staticmethod
    def binds_hint() -> str:
        B = backend()
        if B.binds_mode == "keys":
            return L(f"{B.label} : tu peux changer l'action d'un raccourci ou en ajouter (✎ = modifié par toi). "
                     "Déplacer ou supprimer un raccourci par défaut se fait dans l'onglet Fichier.",
                     f"{B.label}: you can change a shortcut's action or add new ones (✎ = changed by you). "
                     "Moving or deleting a default shortcut is done in the File tab.")
        return L("Dès la première modification, la table de raccourcis est figée : les nouveaux raccourcis par défaut "
                 "du dépôt n'arriveront plus (« Tout remettre par défaut » pour revenir).",
                 "Once you change anything, the shortcut table is frozen: new default shortcuts added to the repo "
                 "won't reach you any more (“Reset everything” to go back).")

    # ── pages ──
    def make_list_page(self, name: str, title: str, searchable: bool = False, hint: str = "") -> Gtk.ListBox:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        if hint:
            lab = Gtk.Label(label=hint, xalign=0, wrap=True)
            lab.add_css_class("dim-label")
            box.append(lab)
        if searchable:
            search = Gtk.SearchEntry(placeholder_text=L("Filtrer les raccourcis…", "Filter shortcuts…"))
            search.connect("search-changed", lambda e: self.filter_binds(e.get_text()))
            box.append(search)
            self.bind_search = search
        lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        lb.add_css_class("boxed-list")
        scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(Adw.Clamp(maximum_size=760, child=lb, valign=Gtk.Align.START))
        box.append(scroll)
        self.stack.add_titled(box, name, title)
        return lb

    def make_nix_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        hint = Gtk.Label(xalign=0, wrap=True, label=L(
            f"Ton fichier {backend().custom_name} en entier. Le bloc « roudix-config » est géré par l'app ; "
            "le reste est à toi. La sauvegarde crée une copie .bak et vérifie la syntaxe.",
            f"Your whole {backend().custom_name} file. The “roudix-config” block is managed by the app; "
            "the rest is yours. Saving makes a .bak copy and checks the syntax."))
        hint.add_css_class("dim-label")
        box.append(hint)
        self.nix_view = Gtk.TextView(monospace=True, top_margin=6, bottom_margin=6, left_margin=8, right_margin=8)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.nix_view)
        box.append(scroll)
        self.stack.add_titled(box, "nix", L("Fichier", "File"))

    # ── state helpers ──
    def toast(self, msg: str) -> None:
        self.overlay.add_toast(Adw.Toast(title=msg, timeout=5))

    def page_name(self) -> str:
        return self.stack.get_visible_child_name() or "rules"

    def on_page(self, *_) -> None:
        p = self.page_name()
        self.add_btn.set_visible(p in ("rules", "binds", "screens"))
        self.reset_btn.set_visible(p == "binds")
        self.save_btn.set_visible(p == "nix")
        if p == "nix":
            self.refresh_nix()

    def reload(self) -> None:
        self.data = load_data()
        self.refresh_nix()

    def rules(self) -> list[dict]:
        return self.data.setdefault("window_rule", [])

    def persist(self) -> None:
        save_data(self.data)
        self.refresh_nix()

    def live(self) -> dict:
        return load_live()

    def binds(self) -> dict:
        return effective_binds(self.live(), get_overrides(self.data))

    def screen_names(self) -> list[str]:
        names = list(effective_outputs(self.live(), get_overrides(self.data)))
        for n in list_outputs_full():
            if n not in names:
                names.append(n)
        return names

    # ── nix page ──
    def nix_buffer_text(self) -> str:
        b = self.nix_view.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), True)

    def nix_dirty(self) -> bool:
        return self.nix_buffer_text() != self.nix_text

    def refresh_nix(self) -> None:
        if self.nix_dirty():
            return
        p = custom_path()
        txt = p.read_text(encoding="utf-8") if p.exists() else ""
        self.nix_view.get_buffer().set_text(txt)
        self.nix_text = self.nix_buffer_text()

    def blocked(self) -> bool:
        if self.page_name() != "nix" and self.nix_dirty():
            self.toast(L("Modifications non sauvegardées dans « Fichier » : sauvegarde-les d'abord.",
                         "Unsaved changes in “File”: save them first."))
            return True
        return False

    def save_nix(self) -> None:
        text = self.nix_buffer_text()
        ok, msg = nix_parse_check(text)
        if not ok:
            self.toast(L(f"Non sauvegardé — erreur Nix : {msg}", f"Not saved — Nix error: {msg}"))
            return
        p = custom_path()
        if p.exists():
            (p.with_name(p.name + ".bak")).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        p.write_text(text, encoding="utf-8")
        self.nix_text = text
        self.data = load_data()
        self.render_all()
        self.toast(L(f"Sauvegardé ({msg}). Rebuild requis.", f"Saved ({msg}). Rebuild required."))

    # ── rendering ──
    def render_all(self) -> None:
        self.render_rules()
        self.render_screens()
        self.render_binds()

    def row(self, title: str, subtitle: str, on_edit, on_delete=None) -> Adw.ActionRow:
        r = Adw.ActionRow(title=title, subtitle=subtitle, activatable=True,
                          tooltip_text=L("Cliquer pour modifier", "Click to edit"))
        plain(r)
        r.set_subtitle_lines(2)
        r.connect("activated", lambda *_: on_edit())
        if on_delete:
            r.add_suffix(icon_button("user-trash-symbolic", L("Supprimer", "Delete"), on_delete))
        r.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        return r

    def render_rules(self) -> None:
        clear(self.rules_list)
        rules = self.rules()
        if not rules:
            self.rules_list.append(Adw.ActionRow(title=L("Aucune règle", "No rules"),
                                                 subtitle=L("Ajoute-en une avec le bouton +", "Add one with the + button")))
        for i, r in enumerate(rules):
            m = r["match"]
            title = m.get("app_id", "") or m.get("title", "")
            sub = rule_summary(r) + (L(f"  ·  titre : {m['title']}", f"  ·  title: {m['title']}")
                                     if "app_id" in m and "title" in m else "")
            self.rules_list.append(self.row(title, sub, lambda i=i: self.edit_rule(i), lambda i=i: self.delete_rule(i)))

    def render_screens(self) -> None:
        clear(self.screens_list)
        B = backend()
        eff = effective_outputs(self.live(), get_overrides(self.data))
        ov = get_overrides(self.data).get("output", {})
        for n in self.screen_names():
            c = eff.get(n, {})
            sub = L(f"{c.get('mode', 'auto')} · échelle {c.get('scale', 1)} · rotation {c.get('transform', 'normal')}",
                    f"{c.get('mode', 'auto')} · scale {c.get('scale', 1)} · rotation {c.get('transform', 'normal')}")
            if B.workspace_names:
                ws = c.get("workspaces")
                dyn = L("dynamiques", "dynamic")
                sub += L("\nworkspaces : ", "\nworkspaces: ") + (" ".join(ws) if isinstance(ws, list) else (ws or dyn))
            title = n + ("  ✎" if n in ov else "")
            r = self.row(title, sub, lambda n=n: self.edit_output(n))
            if n in ov:
                btn = Gtk.Button(label=L("Défaut", "Default"),
                                 tooltip_text=L("Remettre les valeurs par défaut de cet écran",
                                                "Restore this screen's default values"),
                                 valign=Gtk.Align.CENTER)
                btn.add_css_class("flat")
                btn.connect("clicked", lambda *_, n=n: self.reset_output(n))
                r.add_prefix(btn)
            self.screens_list.append(r)

    def render_binds(self) -> None:
        clear(self.binds_list)
        B = backend()
        self._bind_rows: list[tuple[str, Adw.ActionRow]] = []
        mine = get_overrides(self.data).get("keybinds") or {}
        for k, v in self.binds().items():
            title = k + ("  ✎" if B.binds_mode == "keys" and k in mine else "")
            r = self.row(title, bind_action(v), lambda k=k: self.edit_bind(k),
                         (lambda k=k: self.delete_bind(k)) if B.can_delete_binds else None)
            self.binds_list.append(r)
            self._bind_rows.append((f"{k} {bind_action(v)}".lower(), r))
        if hasattr(self, "bind_search"):
            self.filter_binds(self.bind_search.get_text())

    def filter_binds(self, q: str) -> None:
        q = q.strip().lower()
        for text, r in getattr(self, "_bind_rows", []):
            r.set_visible(q in text)

    # ── actions ──
    def on_add(self) -> None:
        if self.blocked():
            return
        {"rules": lambda: self.edit_rule(None), "binds": lambda: self.edit_bind(None),
         "screens": lambda: self.edit_output(None)}.get(self.page_name(), lambda: None)()

    def on_reset(self) -> None:
        if self.blocked():
            return
        if self.page_name() == "binds":
            reset_override("keybinds")
            self.reload()
            self.render_binds()
            self.toast(L("Raccourcis remis par défaut — rebuild requis.", "Shortcuts reset — rebuild required."))

    def edit_rule(self, index) -> None:
        if self.blocked():
            return
        windows = list_windows()
        remember_windows(windows)
        sources = build_sources(windows, load_seen(), list_desktop_apps())
        initial = self.rules()[index] if index is not None else None

        def done(rule):
            if index is None:
                self.rules().append(rule)
            else:
                self.rules()[index] = rule
            self.persist()
            self.render_rules()
            self.toast(L("Règle enregistrée — rebuild requis.", "Rule saved — rebuild required."))
        RuleDialog(self, sources, list_outputs(), initial, done).present()

    def delete_rule(self, index) -> None:
        if self.blocked():
            return
        del self.rules()[index]
        self.persist()
        self.render_rules()
        self.toast(L("Règle supprimée — rebuild requis.", "Rule deleted — rebuild required."))

    def edit_output(self, name) -> None:
        if self.blocked():
            return
        names = self.screen_names()
        eff = effective_outputs(self.live(), get_overrides(self.data))

        def done(res):
            n, ch = res
            save_output_override(n, ch)
            self.reload()
            self.render_screens()
            self.toast(L(f"{n} enregistré — rebuild requis.", f"{n} saved — rebuild required."))
        OutputDialog(self, name, names, eff, list_outputs_full(), done).present()

    def reset_output(self, name) -> None:
        if self.blocked():
            return
        reset_override("output", name)
        self.reload()
        self.render_screens()
        self.toast(L(f"{name} remis par défaut — rebuild requis.", f"{name} reset — rebuild required."))

    def edit_bind(self, key) -> None:
        if self.blocked():
            return
        table = self.binds()
        known = sorted({bind_action(v) for v in table.values()})
        action = bind_action(table[key]) if key in table else ""
        B = backend()

        def done(res):
            k, a = res
            try:
                new = set_bind(table, k, a, old_key=key)
            except ValueError as e:
                self.toast(str(e))
                return
            if B.binds_mode == "keys":              # only what differs from the live config is kept
                live = effective_binds(self.live(), {})
                new = {kk: vv for kk, vv in new.items() if live.get(kk) != vv}
            save_binds_override(new)
            self.reload()
            self.render_binds()
            self.toast(L(f"{k} → {a} enregistré — rebuild requis.", f"{k} → {a} saved — rebuild required."))
        BindDialog(self, key or "", action, known, done).present()

    def delete_bind(self, key) -> None:
        if self.blocked():
            return
        table = self.binds()
        table.pop(key, None)
        save_binds_override(table)
        self.reload()
        self.render_binds()
        self.toast(L(f"{key} supprimé — rebuild requis.", f"{key} deleted — rebuild required."))


# ───────────────────────── application ─────────────────────────

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.win = None

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)  # io.roudix.config, from hicolor

    def do_activate(self) -> None:
        if self.win:
            self.win.present()
            return
        reason = availability()
        if reason:
            self.win = self.unavailable(reason)
        else:
            try:
                msgs = bootstrap()
            except Exception as e:  # noqa: BLE001 - show anything to the user, no terminal here
                self.win = self.unavailable(L(f"Impossible de préparer {backend().custom_name} : {e}",
                                              f"Couldn't prepare {backend().custom_name}: {e}"))
                self.win.present()
                return
            self.win = ConfigWindow(self, msgs)
        self.win.present()

    def unavailable(self, reason: str) -> Adw.ApplicationWindow:
        win = Adw.ApplicationWindow(application=self, title="Roudix Config", default_width=520, default_height=360)
        page = Adw.StatusPage(icon_name="dialog-information-symbolic",
                              title=L("Non disponible", "Not available"), description=reason)
        view = Adw.ToolbarView(content=page)
        view.add_top_bar(Adw.HeaderBar())
        win.set_content(view)
        return win


def main() -> int:
    return App().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

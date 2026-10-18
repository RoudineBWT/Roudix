#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages (ps: [ ps.pygobject3 ])" gtk4 libadwaita gobject-introspection adwaita-icon-theme
"""roudix-config-gui — GTK4/libadwaita front-end of roudix-config.

Same engine as the TUI (roudix_config_core.py): everything it manages lives in
one marked block of your own modules/home/umbriel-custom.nix; what is outside
the block is yours and never touched. Pages: window rules, screens &
workspaces, keybinds, and the -custom.nix file itself.

Launch it inside your session (so open windows and outputs are live):
    scripts/roudix-config-gui.py
Then rebuild and reload the config (Mod+Shift+R).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk, Pango  # noqa: E402

from roudix_config_core import (  # noqa: E402
    PLACEMENTS, TRANSFORMS, availability, bind_action, bootstrap, build_rule, build_sources,
    custom_path, desktop_type, effective_binds, effective_outputs, get_overrides, list_desktop_apps,
    list_outputs, list_outputs_full, list_windows, load_data, load_live, load_seen, nix_parse_check,
    remember_windows, reset_override, rule_summary, rule_to_toml, save_binds_override, save_data,
    save_output_override, set_bind,
)

APP_ID = "dev.roudix.Config"
UNSET = "(inchangé)"
MODIFIERS = ["Mod", "Super", "Ctrl", "Alt", "Shift"]
MOD_ALIASES = {"control": "Ctrl", "logo": "Super", "win": "Super"}


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


def set_selected_by_value(row: Adw.ComboRow, values: list, value) -> None:
    if value in values:
        row.set_selected(values.index(value))


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
        cancel = Gtk.Button(label="Annuler")
        cancel.connect("clicked", lambda *_: self.close())
        save = Gtk.Button(label="Enregistrer")
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
        super().__init__(parent, "Règle de fenêtre", on_done)
        self.sources, self.outputs = sources, outputs
        self.place_labels = list(PLACEMENTS)

        g = self.group("Application", "● ouverte maintenant · ○ déjà vue ouverte · sans symbole : installée "
                                      "(l'app_id est alors deviné)")
        self.pick = combo("Choisir une app", ["(saisir à la main)"] + [s["label"].strip() for s in sources],
                          searchable=True)
        self.pick.connect("notify::selected", self.on_pick)
        g.add(self.pick)
        self.app_id = entry("app_id (regex)")
        self.title_re = entry("Titre (regex, optionnel)")
        g.add(self.app_id)
        g.add(self.title_re)

        g2 = self.group("Réglages (laisser « inchangé » pour ne rien forcer)")
        self.output = combo("Écran", [UNSET] + outputs)
        self.ws = combo("Workspace", [UNSET] + [str(i) for i in range(1, 11)])
        self.place = combo("Placement", [UNSET] + self.place_labels)
        self.blur = combo("Flou (blur)", [UNSET, "Activé", "Désactivé"])
        self.opacity = entry("Opacité (0 à 1, optionnel)")
        for w in (self.output, self.ws, self.place, self.blur, self.opacity):
            g2.add(w)

        self.preview = Gtk.Label(xalign=0, selectable=True, wrap=True, hexpand=True)
        self.preview.add_css_class("monospace")
        self.bottom(self.preview)

        if initial:
            self.app_id.set_text(initial["match"].get("app_id", ""))
            self.title_re.set_text(initial["match"].get("title", ""))
            set_selected_by_value(self.output, [UNSET] + outputs, initial.get("default_output"))
            if "default_workspace" in initial:
                self.ws.set_selected(initial["default_workspace"] if 1 <= initial["default_workspace"] <= 10 else 0)
            for i, (label, key) in enumerate(PLACEMENTS.items()):
                if initial.get(key):
                    self.place.set_selected(i + 1)
            if "blur" in initial:
                self.blur.set_selected(1 if initial["blur"] else 2)
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
            raise ValueError("Opacité : un nombre entre 0 et 1")
        o = self.output.get_selected()
        w = self.ws.get_selected()
        p = self.place.get_selected()
        b = self.blur.get_selected()
        return build_rule(
            self.app_id.get_text().strip(), self.title_re.get_text().strip(),
            self.outputs[o - 1] if o > 0 else None,
            w if w > 0 else None,
            self.place_labels[p - 1] if p > 0 else None,
            {0: None, 1: True, 2: False}[b],
            opacity,
        )

    def refresh(self) -> None:
        try:
            self.preview.set_text(rule_to_toml(self.result()))
        except ValueError as e:
            self.preview.set_text(f"⚠ {e}")


class OutputDialog(FormDialog):
    def __init__(self, parent, name, names, cfg, live, on_done):
        super().__init__(parent, "Écran", on_done, height=760)
        self.names, self.cfg, self.live = names, cfg, live
        g = self.group("Sortie")
        self.name = combo("Écran", names)
        g.add(self.name)

        g2 = self.group("Affichage", "Le format du mode est 2560x1440 ou 2560x1440@240.000")
        self.modes = combo("Modes détectés (Umbriel doit tourner)", ["(choisir)"])
        self.mode = entry("Résolution / fréquence")
        self.scale = entry("Échelle (0.25 à 4)")
        self.transform = combo("Rotation", [UNSET] + TRANSFORMS)
        for w in (self.modes, self.mode, self.scale, self.transform):
            g2.add(w)

        g3 = self.group("Workspaces",
                        "Noms séparés par des espaces. Évite un nom purement numérique présent sur un seul écran : "
                        "Umbriel le traite comme unique et Mod+N sauterait toujours vers cet écran.")
        self.workspaces = entry("Noms des workspaces de cet écran")
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
        self.modes.set_model(Gtk.StringList.new(
            ["(choisir)"] + [m + (" (actuel)" if m == info.get("current") else "") for m in self._modes]))
        self.mode.set_text(str(cfg.get("mode", "")))
        self.scale.set_text("" if "scale" not in cfg else str(cfg["scale"]))
        t = cfg.get("transform")
        self.transform.set_selected(TRANSFORMS.index(t) + 1 if t in TRANSFORMS else 0)
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
            raise ValueError("Choisis un écran")
        ch: dict = {}
        mode = self.mode.get_text().strip()
        if mode:
            if not re.fullmatch(r"\d+x\d+(@\d+(\.\d+)?)?", mode):
                raise ValueError("Mode : format 2560x1440 ou 2560x1440@240")
            ch["mode"] = mode
        sc = self.scale.get_text().strip()
        if sc:
            try:
                v = float(sc.replace(",", "."))
            except ValueError:
                raise ValueError("Échelle : un nombre")
            if not 0.25 <= v <= 4.0:
                raise ValueError("Échelle entre 0.25 et 4")
            ch["scale"] = int(v) if v == int(v) else v
        t = self.transform.get_selected()
        if t > 0:
            ch["transform"] = TRANSFORMS[t - 1]
        ws = self.workspaces.get_text().split()
        if ws:
            ch["workspaces"] = ws
        if not ch:
            raise ValueError("Rien à enregistrer")
        return name, ch


class BindDialog(FormDialog):
    def __init__(self, parent, key, action, known, on_done):
        super().__init__(parent, "Raccourci", on_done, height=840)
        self.known = known
        self._lock = False
        g = self.group("Touches", "Active les modificateurs puis indique la touche (nom xkb : Q, Return, Left, "
                                  "F5, XF86AudioMute, WheelUp…). Mod = Super sur un vrai bureau.")
        self.mod_rows: dict[str, Adw.SwitchRow] = {}
        for m in MODIFIERS:
            r = Adw.SwitchRow(title=m)
            r.connect("notify::active", lambda *_: self.compose_raw())
            self.mod_rows[m] = r
            g.add(r)
        self.key = entry("Touche")
        self.key.connect("changed", lambda *_: self.compose_raw())
        g.add(self.key)

        g2 = self.group("Résultat")
        self.raw = entry("Raccourci complet (modifiable)")
        self.raw.connect("changed", lambda *_: self.parse_raw())
        g2.add(self.raw)

        g3 = self.group("Action", "Ex. window-close · spawn:ghostty · spawn:noctalia msg panel-toggle launcher")
        self.action = entry("Action")
        self.action.set_text(action)
        self.known_row = combo("Actions déjà utilisées", ["(choisir pour remplir)"] + [k[:80] for k in known],
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
        mods = [m for m in MODIFIERS if self.mod_rows[m].get_active()]
        k = self.key.get_text().strip()
        self.raw.set_text("+".join(mods + ([k] if k else [])))
        self._lock = False

    def parse_raw(self) -> None:
        if self._lock:
            return
        self._lock = True
        parts = [p for p in self.raw.get_text().strip().split("+")]
        mods = {MOD_ALIASES.get(p.lower(), p) for p in parts[:-1]}
        for m in MODIFIERS:
            self.mod_rows[m].set_active(m in mods)
        self.key.set_text(parts[-1] if parts else "")
        self._lock = False

    def on_known(self, *_):
        i = self.known_row.get_selected()
        if 1 <= i <= len(self.known):
            self.action.set_text(self.known[i - 1])

    def result(self):
        return self.raw.get_text().strip(), self.action.get_text().strip()


# ───────────────────────── main window ─────────────────────────

class ConfigWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, messages: list[str]):
        super().__init__(application=app, title="Roudix Config", default_width=920, default_height=720)
        self.data = load_data()
        self.nix_text = ""
        self.overlay = Adw.ToastOverlay()

        self.stack = Adw.ViewStack()
        self.rules_list = self.make_list_page("rules", "Règles", "view-list-symbolic")
        self.screens_list = self.make_list_page("screens", "Écrans", "video-display-symbolic")
        self.binds_list = self.make_list_page("binds", "Raccourcis", "input-keyboard-symbolic", searchable=True)
        self.make_nix_page()

        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header = Adw.HeaderBar(title_widget=switcher)
        self.add_btn = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Ajouter")
        self.add_btn.connect("clicked", lambda *_: self.on_add())
        self.reset_btn = Gtk.Button(label="Tout remettre par défaut",
                                    tooltip_text="Abandonne tes changements de raccourcis")
        self.reset_btn.connect("clicked", lambda *_: self.on_reset())
        self.save_btn = Gtk.Button(label="Sauvegarder")
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

    # ── pages ──
    def make_list_page(self, name: str, title: str, icon: str, searchable: bool = False) -> Gtk.ListBox:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        if searchable:
            search = Gtk.SearchEntry(placeholder_text="Filtrer les raccourcis…")
            search.connect("search-changed", lambda e: self.filter_binds(e.get_text()))
            box.append(search)
            self.bind_search = search
        lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        lb.add_css_class("boxed-list")
        scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(Adw.Clamp(maximum_size=760, child=lb, valign=Gtk.Align.START))
        box.append(scroll)
        self.stack.add_titled(box, name, title)  # no tab icon: theme-independent
        return lb

    def make_nix_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        hint = Gtk.Label(xalign=0, wrap=True, label="Ton fichier umbriel-custom.nix en entier. Le bloc "
                         "« roudix-config » est géré par l'app ; le reste est à toi. La sauvegarde crée une "
                         "copie .bak et vérifie la syntaxe.")
        hint.add_css_class("dim-label")
        box.append(hint)
        self.nix_view = Gtk.TextView(monospace=True, top_margin=6, bottom_margin=6, left_margin=8, right_margin=8)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.nix_view)
        box.append(scroll)
        self.stack.add_titled(box, "nix", "Fichier")

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
        txt = p.read_text() if p.exists() else ""
        self.nix_view.get_buffer().set_text(txt)
        self.nix_text = self.nix_buffer_text()

    def blocked(self) -> bool:
        if self.page_name() != "nix" and self.nix_dirty():
            self.toast("Modifications non sauvegardées dans « Mon -custom.nix » : sauvegarde-les d'abord.")
            return True
        return False

    def save_nix(self) -> None:
        text = self.nix_buffer_text()
        ok, msg = nix_parse_check(text)
        if not ok:
            self.toast(f"Non sauvegardé — erreur Nix : {msg}")
            return
        p = custom_path()
        if p.exists():
            (p.with_name(p.name + ".bak")).write_text(p.read_text())
        p.write_text(text)
        self.nix_text = text
        self.data = load_data()
        self.render_all()
        self.toast(f"Sauvegardé ({msg}). Rebuild requis.")

    # ── rendering ──
    def render_all(self) -> None:
        self.render_rules()
        self.render_screens()
        self.render_binds()

    def row(self, title: str, subtitle: str, on_edit, on_delete=None) -> Adw.ActionRow:
        r = Adw.ActionRow(title=title, subtitle=subtitle, activatable=True, tooltip_text="Cliquer pour modifier")
        plain(r)
        r.set_subtitle_lines(2)
        r.connect("activated", lambda *_: on_edit())
        if on_delete:
            r.add_suffix(icon_button("user-trash-symbolic", "Supprimer", on_delete))
        r.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        return r

    def render_rules(self) -> None:
        clear(self.rules_list)
        rules = self.rules()
        if not rules:
            self.rules_list.append(Adw.ActionRow(title="Aucune règle",
                                                 subtitle="Ajoute-en une avec le bouton +"))
        for i, r in enumerate(rules):
            m = r["match"]
            title = m.get("app_id", "") or m.get("title", "")
            sub = rule_summary(r) + (f"  ·  titre : {m['title']}" if "app_id" in m and "title" in m else "")
            self.rules_list.append(self.row(title, sub, lambda i=i: self.edit_rule(i), lambda i=i: self.delete_rule(i)))

    def render_screens(self) -> None:
        clear(self.screens_list)
        eff = effective_outputs(self.live(), get_overrides(self.data))
        ov = get_overrides(self.data).get("output", {})
        for n in self.screen_names():
            c = eff.get(n, {})
            ws = c.get("workspaces")
            sub = (f"{c.get('mode', 'auto')} · échelle {c.get('scale', 1)} · rotation {c.get('transform', 'normal')}"
                   f"\nworkspaces : {' '.join(ws) if isinstance(ws, list) else (ws or 'dynamiques')}")
            title = n + ("  ✎" if n in ov else "")
            r = self.row(title, sub, lambda n=n: self.edit_output(n))
            if n in ov:
                btn = Gtk.Button(label="Défaut", tooltip_text="Remettre les valeurs par défaut de cet écran",
                                 valign=Gtk.Align.CENTER)
                btn.add_css_class("flat")
                btn.connect("clicked", lambda *_, n=n: self.reset_output(n))
                r.add_prefix(btn)
            self.screens_list.append(r)

    def render_binds(self) -> None:
        clear(self.binds_list)
        self._bind_rows: list[tuple[str, Adw.ActionRow]] = []
        for k, v in self.binds().items():
            r = self.row(k, bind_action(v), lambda k=k: self.edit_bind(k), lambda k=k: self.delete_bind(k))
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
            self.toast("Raccourcis remis par défaut — rebuild requis.")

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
            self.toast("Règle enregistrée — rebuild requis.")
        RuleDialog(self, sources, list_outputs(), initial, done).present()

    def delete_rule(self, index) -> None:
        if self.blocked():
            return
        del self.rules()[index]
        self.persist()
        self.render_rules()
        self.toast("Règle supprimée — rebuild requis.")

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
            self.toast(f"{n} enregistré — rebuild requis.")
        OutputDialog(self, name, names, eff, list_outputs_full(), done).present()

    def reset_output(self, name) -> None:
        if self.blocked():
            return
        reset_override("output", name)
        self.reload()
        self.render_screens()
        self.toast(f"{name} remis par défaut — rebuild requis.")

    def edit_bind(self, key) -> None:
        if self.blocked():
            return
        table = self.binds()
        known = sorted({bind_action(v) for v in table.values()})
        action = bind_action(table[key]) if key in table else ""

        def done(res):
            k, a = res
            try:
                new = set_bind(table, k, a, old_key=key)
            except ValueError as e:
                self.toast(str(e))
                return
            save_binds_override(new)
            self.reload()
            self.render_binds()
            self.toast(f"{k} → {a} enregistré — rebuild requis.")
        BindDialog(self, key or "", action, known, done).present()

    def delete_bind(self, key) -> None:
        if self.blocked():
            return
        table = self.binds()
        table.pop(key, None)
        save_binds_override(table)
        self.reload()
        self.render_binds()
        self.toast(f"{key} supprimé — rebuild requis.")


# ───────────────────────── application ─────────────────────────

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.win = None

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
                self.win = self.unavailable(f"Impossible de préparer umbriel-custom.nix : {e}")
                self.win.present()
                return
            self.win = ConfigWindow(self, msgs)
        self.win.present()

    def unavailable(self, reason: str) -> Adw.ApplicationWindow:
        win = Adw.ApplicationWindow(application=self, title="Roudix Config", default_width=520, default_height=360)
        page = Adw.StatusPage(icon_name="dialog-information-symbolic", title="Non disponible", description=reason)
        view = Adw.ToolbarView(content=page)
        view.add_top_bar(Adw.HeaderBar())
        win.set_content(view)
        return win


def main() -> int:
    return App().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

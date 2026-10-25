#!/usr/bin/env python3
# roudix-firewall — GTK4/Adwaita GUI to manage the NixOS firewall on Roudix.
#
# Python take on nix-firewall-mngt (GLF-OS, Rust). Everything it changes lives in
# ONE gitignored file, hosts/<host>/firewall.local.nix, imported by the host's
# configuration.nix when it exists: `git pull` and roudix-autoupdate never
# overwrite it, and it can never block a fast-forward. The logic (model, Nix
# generation/parsing, atomic writes) is in roudix_firewall_core.py, GTK-free.

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

# package layout ($out/bin → $out/lib/roudix-firewall), then a plain checkout
_here = Path(__file__).resolve().parent
for _p in (_here.parent / "lib" / "roudix-firewall", _here):
    sys.path.insert(0, str(_p))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk, Pango  # noqa: E402

import roudix_firewall_core as fw  # noqa: E402

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR = os.path.expanduser("~/.local/share/roudix-firewall")
LOG_FILE = os.path.join(LOG_DIR, "firewall.log")
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

log = logging.getLogger("roudix-firewall")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)],
    )


# ── translations (gettext) ───────────────────────────────────────────────────
# Messages are written in English: tr("…"). Catalogs live in po/<lang>.po and the Nix
# package compiles them to share/locale/<lang>/LC_MESSAGES/roudix-firewall.mo. The
# language comes from LANGUAGE / LC_ALL / LC_MESSAGES / LANG; a missing catalog falls
# back to English.
import gettext as _gettext  # noqa: E402
import glob as _glob  # noqa: E402

_DOMAIN = "roudix-firewall"


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
tr = _translation.gettext          # tr("text")
tr_noop = fw.tr_noop               # marks a string for extraction, translated later with tr()


def port_error_text(exc: Exception) -> str:
    if isinstance(exc, fw.EmptyPortsError):
        return tr("Enter at least one port.")
    if isinstance(exc, fw.BadPortError):
        return tr("Not a valid port or range: {token} (ports go from 1 to 65535).").format(token=exc.token)
    return str(exc)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def make_row(title: str, subtitle: str = "") -> Adw.ActionRow:
    """ActionRow whose texts are shown literally (rule names are user input:
    no Pango markup, so an '&' or '<' in a name cannot break the row)."""
    row = Adw.ActionRow()
    row.set_use_markup(False)
    row.set_title(title)
    if subtitle:
        row.set_subtitle(subtitle)
    return row


def icon_button(icon: str, tooltip: str) -> Gtk.Button:
    btn = Gtk.Button.new_from_icon_name(icon)
    btn.set_tooltip_text(tooltip)
    btn.set_valign(Gtk.Align.CENTER)
    btn.add_css_class("flat")
    return btn


# ── Add / edit a rule ─────────────────────────────────────────────────────────

class RuleDialog(Adw.Dialog):
    def __init__(self, rule: fw.Rule | None, taken: set, on_done):
        super().__init__()
        self._taken = taken            # keys (proto, ports) of the OTHER rules
        self._on_done = on_done
        self._enabled = rule.enabled if rule else True
        self.set_title(tr("Edit rule") if rule else tr("New rule"))
        self.set_content_width(440)

        self._name = Adw.EntryRow(title=tr("Name"))
        self._proto = Adw.ComboRow(title=tr("Protocol"))
        self._proto.set_model(Gtk.StringList.new([fw.PROTO_LABEL[p] for p in fw.PROTOS]))
        self._ports = Adw.EntryRow(title=tr("Ports (e.g. 80, 443, 8000-8010)"))
        self._error = Gtk.Label(xalign=0, wrap=True)
        self._error.add_css_class("error")
        self._error.set_visible(False)

        if rule:
            self._name.set_text(rule.name)
            self._proto.set_selected(fw.PROTOS.index(rule.proto))
            self._ports.set_text(rule.ports_text())

        group = Adw.PreferencesGroup()
        for row in (self._name, self._proto, self._ports):
            group.add(row)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for m in ("top", "bottom", "start", "end"):
            getattr(box, f"set_margin_{m}")(18)
        box.append(group)
        box.append(self._error)

        cancel = Gtk.Button(label=tr("Cancel"))
        cancel.connect("clicked", lambda _b: self.close())
        save = Gtk.Button(label=tr("Save"))
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save)
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)
        header.pack_start(cancel)
        header.pack_end(save)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(box)
        self.set_child(toolbar)
        self.set_default_widget(save)
        self._name.connect("entry-activated", lambda _r: self._ports.grab_focus())
        self._ports.connect("entry-activated", self._on_save)

    def _fail(self, msg: str):
        self._error.set_label(msg)
        self._error.set_visible(True)

    def _on_save(self, _w):
        try:
            name = fw.clean_name(self._name.get_text())
        except fw.FirewallError:
            return self._fail(tr("Give the rule a name."))
        try:
            spec = fw.parse_port_spec(self._ports.get_text())
        except fw.FirewallError as e:
            return self._fail(port_error_text(e))
        proto = fw.PROTOS[self._proto.get_selected()]
        rule = fw.Rule(name, proto, spec, self._enabled)
        if rule.key() in self._taken:
            return self._fail(tr("Another rule already uses this protocol and these ports."))
        self._on_done(rule)
        self.close()


# ── Presets ───────────────────────────────────────────────────────────────────

class PresetsDialog(Adw.Dialog):
    def __init__(self, existing_keys, on_add):
        super().__init__()
        self._on_add = on_add
        self.set_title(tr("Presets"))
        self.set_content_width(480)
        self.set_content_height(560)
        page = Adw.PreferencesPage()
        groups: dict[str, Adw.PreferencesGroup] = {}
        for cat, name, proto, ports in fw.PRESETS:
            if cat not in groups:
                groups[cat] = Adw.PreferencesGroup(title=tr(cat))
                page.add(groups[cat])
            spec = fw.parse_port_spec(ports)
            row = make_row(tr(name), f"{fw.PROTO_LABEL[proto]} · {fw.format_port_spec(spec)}")
            btn = Gtk.Button(valign=Gtk.Align.CENTER)
            if (proto, tuple(spec)) in existing_keys:
                btn.set_label(tr("Added"))
                btn.set_sensitive(False)
            else:
                btn.set_label(tr("Add"))
                btn.connect("clicked", self._clicked, fw.Rule(tr(name), proto, spec))
            row.add_suffix(btn)
            groups[cat].add(row)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(page)
        self.set_child(toolbar)

    def _clicked(self, btn, rule):
        if self._on_add(rule):
            btn.set_label(tr("Added"))
            btn.set_sensitive(False)


# ── Rebuild (log window) ──────────────────────────────────────────────────────

class RebuildDialog(Adw.Dialog):
    """Runs `nh os switch` and streams its output. Cannot be closed while it runs."""

    def __init__(self, on_finished):
        super().__init__()
        self._on_finished = on_finished
        self.set_title(tr("Applying the firewall"))
        self.set_content_width(680)
        self.set_content_height(460)
        self.set_can_close(False)

        self._spinner = Gtk.Spinner(spinning=True)
        self._status = Gtk.Label(label=tr("Rebuilding… this can take a few minutes."), xalign=0, hexpand=True)
        self._status.set_wrap(True)
        top = Gtk.Box(spacing=12)
        top.append(self._spinner)
        top.append(self._status)

        self._view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                  wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._buf = self._view.get_buffer()
        self._buf.create_tag("error", foreground="#bf616a")
        self._buf.create_tag("ok", foreground="#a3be8c")
        self._buf.create_tag("dim", scale=0.9, weight=Pango.Weight.LIGHT)
        self._scroll = Gtk.ScrolledWindow(vexpand=True)
        self._scroll.add_css_class("card")
        self._scroll.set_child(self._view)

        self._close = Gtk.Button(label=tr("Close"))
        self._close.set_sensitive(False)
        self._close.connect("clicked", lambda _b: self.close())
        bottom = Gtk.Box(halign=Gtk.Align.END)
        bottom.append(self._close)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for m in ("top", "bottom", "start", "end"):
            getattr(box, f"set_margin_{m}")(18)
        box.append(top)
        box.append(self._scroll)
        box.append(bottom)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(box)
        self.set_child(toolbar)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _line(self, text: str, tag: str | None = None):
        end = self._buf.get_end_iter()
        if tag:
            self._buf.insert_with_tags_by_name(end, text + "\n", tag)
        else:
            self._buf.insert(end, text + "\n")
        GLib.idle_add(self._scroll_to_end)
        return False

    def _scroll_to_end(self):
        adj = self._scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def _pick_tag(self, line: str) -> str | None:
        lo = line.lower()
        if any(w in lo for w in ("error", "failed", "✗")):
            return "error"
        return None

    def _run(self):
        cmd = fw.rebuild_command()
        log.info("Running: %s", " ".join(cmd))
        GLib.idle_add(self._line, "$ " + " ".join(cmd), "dim")
        rc = 1
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            pending = b""
            while True:
                chunk = os.read(proc.stdout.fileno(), 4096)
                if not chunk:
                    break
                pending += chunk
                # \r = progress bars redrawing themselves: keep only the last state
                parts = re.split(rb"\r?\n", pending)
                pending = parts.pop()
                if len(pending) > 8192:
                    pending = pending.split(b"\r")[-1]
                for raw in parts:
                    line = strip_ansi(raw.decode("utf-8", "replace").split("\r")[-1]).rstrip()
                    if line:
                        log.info(line)
                        GLib.idle_add(self._line, line, self._pick_tag(line))
            tail = strip_ansi(pending.decode("utf-8", "replace").split("\r")[-1]).strip()
            if tail:
                GLib.idle_add(self._line, tail, self._pick_tag(tail))
            rc = proc.wait()
        except FileNotFoundError:
            log.error("nh not found")
            GLib.idle_add(self._line, tr("ERROR: 'nh' not found in PATH."), "error")
            rc = 127
        except Exception as e:  # noqa: BLE001 — shown to the user, then reported as a failure
            log.exception("rebuild crashed")
            GLib.idle_add(self._line, tr("ERROR: {error}").format(error=e), "error")
        GLib.idle_add(self._done, rc)

    def _done(self, rc: int):
        self._spinner.set_visible(False)
        self.set_can_close(True)
        self._close.set_sensitive(True)
        self._close.grab_focus()
        if rc == 0:
            self._status.set_label(tr("✓ Firewall applied."))
            self._line("", None)
            self._line(tr("✓ Rebuild completed successfully."), "ok")
        else:
            self._status.set_label(tr("✗ The rebuild failed (exit {rc}). Your previous firewall file was restored.").format(rc=rc))
            self._line("", None)
            self._line(tr("✗ Rebuild failed (exit code {rc}).").format(rc=rc), "error")
        self._on_finished(rc == 0)
        return False


# ── Main window ───────────────────────────────────────────────────────────────

class FirewallWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=tr("Roudix Firewall"))
        self.set_default_size(640, 800)
        self._cfg = fw.load()
        self._saved_snapshot = self._cfg.snapshot()
        self._saved_enabled = self._cfg.enabled
        self._file_exists = os.path.exists(fw.firewall_file())
        self._busy = False
        self._force_close = False
        self._rule_rows: list[Gtk.Widget] = []
        self._iface_rows: list[Gtk.Widget] = []
        self._suggest_rows: list[Gtk.Widget] = []
        log.info("host=%s file=%s origin=%s", fw.ROUDIX_HOST, fw.firewall_file(), self._cfg.origin)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=tr("Roudix Firewall"), subtitle=fw.ROUDIX_HOST))

        # ── banners (shown only when relevant, see _refresh_banners) ──
        self._banners = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._b_host = self._banner(tr("Host directory not found: {path}. Set ROUDIX_HOST to the name of your hosts/ directory.").format(path=fw.host_dir()))
        self._b_import = self._banner(tr("This host's configuration.nix does not import firewall.local.nix yet: nothing saved here will apply. Update Roudix first."))
        self._b_hand = self._banner(tr("This file was edited by hand and has been read back from its Nix. Saving will regenerate it."))
        self._b_local = self._banner("")

        # ── page ──
        page = Adw.PreferencesPage()

        main = Adw.PreferencesGroup()
        main.set_description(GLib.markup_escape_text(
            tr("Saved in {path}, which git ignores: git pull and the auto-update never overwrite it.")
            .format(path=fw.firewall_file())))
        self._switch = Adw.SwitchRow(title=tr("Firewall"),
                                     subtitle=tr("Block incoming connections that are not allowed below"))
        self._switch.set_active(self._cfg.enabled)
        self._switch.connect("notify::active", self._on_enable_toggled)
        main.add(self._switch)
        page.add(main)

        self._rules_group = Adw.PreferencesGroup(
            title=tr("Allowed ports"),
            description=tr("Incoming connections on these ports are allowed."))
        add_btn = Gtk.Button(label=tr("Add rule"))
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", lambda _b: self._open_rule_dialog(None))
        presets_btn = Gtk.Button(label=tr("Presets"))
        presets_btn.connect("clicked", self._open_presets)
        suffix = Gtk.Box(spacing=6)
        suffix.append(presets_btn)
        suffix.append(add_btn)
        self._rules_group.set_header_suffix(suffix)
        page.add(self._rules_group)

        self._ifaces_group = Adw.PreferencesGroup(
            title=tr("Trusted interfaces"),
            description=tr("All traffic coming in on these interfaces is allowed (containers, VMs, VPN…)."))
        self._iface_entry = Adw.EntryRow(title=tr("Add an interface (e.g. docker0)"))
        self._iface_entry.set_show_apply_button(True)
        self._iface_entry.connect("apply", self._on_iface_apply)
        self._ifaces_group.add(self._iface_entry)
        page.add(self._ifaces_group)
        self._suggest_group = Adw.PreferencesGroup()
        self._suggest = Adw.ExpanderRow(title=tr("Suggestions"))
        self._suggest.set_use_markup(False)
        self._suggest_group.add(self._suggest)
        page.add(self._suggest_group)

        # ── action bar ──
        self._status = Gtk.Label(xalign=0, hexpand=True)
        self._status.add_css_class("dim-label")
        self._save_btn = Gtk.Button(label=tr("Save"))
        self._save_btn.connect("clicked", lambda _b: self._on_save(False))
        self._apply_btn = Gtk.Button(label=tr("Save & apply"))
        self._apply_btn.add_css_class("suggested-action")
        self._apply_btn.connect("clicked", lambda _b: self._on_save(True))
        bar = Gtk.ActionBar()
        bar.pack_start(self._status)
        bar.pack_end(self._apply_btn)
        bar.pack_end(self._save_btn)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.add_top_bar(self._banners)
        toolbar.set_content(page)
        toolbar.add_bottom_bar(bar)
        self._toasts = Adw.ToastOverlay()
        self._toasts.set_child(toolbar)
        self.set_content(self._toasts)
        self.connect("close-request", self._on_close_request)

        self._refresh_all()

    # ── helpers ──
    def _banner(self, title: str) -> Adw.Banner:
        b = Adw.Banner(title=title)
        b.set_use_markup(False)
        b.set_revealed(False)
        self._banners.append(b)
        return b

    def _toast(self, text: str):
        self._toasts.add_toast(Adw.Toast(title=text))

    def _rule_keys(self, skip: fw.Rule | None = None) -> set:
        return {r.key() for r in self._cfg.rules if r is not skip}

    def _dirty(self) -> bool:
        return self._cfg.snapshot() != self._saved_snapshot

    # ── refreshing the UI from self._cfg ──
    def _refresh_all(self):
        self._refresh_rules()
        self._refresh_ifaces()
        self._refresh_banners()
        self._refresh_state()

    def _refresh_banners(self):
        lines = fw.local_nix_firewall_lines()
        self._b_host.set_revealed(not os.path.isdir(fw.host_dir()))
        self._b_import.set_revealed(not fw.host_imports_firewall_file())
        self._b_hand.set_revealed(self._file_exists and self._cfg.origin == "nix" and not self._dirty())
        if lines:
            self._b_local.set_title(tr(
                "local.nix also sets networking.firewall options ({n} line(s)). They keep working and add up "
                "to the ones below, but cannot be edited here.").format(n=len(lines)))
        self._b_local.set_revealed(bool(lines))

    def _refresh_state(self):
        dirty = self._dirty()
        self._status.set_label(tr("Unsaved changes") if dirty else "")
        self._save_btn.set_sensitive(dirty and not self._busy)
        self._apply_btn.set_sensitive(not self._busy)
        # the hand-edit banner only makes sense until the first change
        self._b_hand.set_revealed(self._file_exists and self._cfg.origin == "nix" and not dirty)

    def _refresh_rules(self):
        for row in self._rule_rows:
            self._rules_group.remove(row)
        self._rule_rows = []
        if not self._cfg.rules:
            row = make_row(tr("No rules yet"), tr("Add a rule or pick a preset."))
            self._rules_group.add(row)
            self._rule_rows.append(row)
            return
        for rule in self._cfg.rules:
            sub = f"{fw.PROTO_LABEL[rule.proto]} · {rule.ports_text()}"
            if not rule.enabled:
                sub += " · " + tr("disabled")
            row = make_row(rule.name, sub)
            sw = Gtk.Switch(valign=Gtk.Align.CENTER, active=rule.enabled)
            sw.set_tooltip_text(tr("Enable or disable this rule"))
            sw.connect("notify::active", self._on_rule_toggled, rule)
            edit = icon_button("document-edit-symbolic", tr("Edit"))
            edit.connect("clicked", lambda _b, r=rule: self._open_rule_dialog(r))
            delete = icon_button("user-trash-symbolic", tr("Delete"))
            delete.connect("clicked", lambda _b, r=rule: self._delete_rule(r))
            for w in (sw, edit, delete):
                row.add_suffix(w)
            self._rules_group.add(row)
            self._rule_rows.append(row)

    def _refresh_ifaces(self):
        for row in self._iface_rows:
            self._ifaces_group.remove(row)
        self._iface_rows = []
        known = dict(fw.INTERFACE_PRESETS)
        for name in self._cfg.trusted_interfaces:
            row = make_row(name, tr(known[name]) if name in known else "")
            delete = icon_button("user-trash-symbolic", tr("Remove"))
            delete.connect("clicked", lambda _b, n=name: self._remove_iface(n))
            row.add_suffix(delete)
            self._ifaces_group.add(row)
            self._iface_rows.append(row)
        for row in self._suggest_rows:
            self._suggest.remove(row)
        self._suggest_rows = []
        for name, label in fw.INTERFACE_PRESETS:
            if name in self._cfg.trusted_interfaces:
                continue
            row = make_row(name, tr(label))
            add = icon_button("list-add-symbolic", tr("Add"))
            add.connect("clicked", lambda _b, n=name: self._add_iface(n))
            row.add_suffix(add)
            self._suggest.add_row(row)
            self._suggest_rows.append(row)
        self._suggest_group.set_visible(bool(self._suggest_rows))

    # ── rule actions ──
    def _open_rule_dialog(self, rule: fw.Rule | None):
        def done(new: fw.Rule):
            if rule is None:
                self._cfg.rules.append(new)
            else:
                new.enabled = rule.enabled
                idx = next(i for i, r in enumerate(self._cfg.rules) if r is rule)
                self._cfg.rules[idx] = new
            self._refresh_rules()
            self._refresh_state()
        RuleDialog(rule, self._rule_keys(skip=rule), done).present(self)

    def _open_presets(self, _btn):
        PresetsDialog(self._rule_keys(), self._add_preset).present(self)

    def _add_preset(self, rule: fw.Rule) -> bool:
        if rule.key() in self._rule_keys():
            return False
        self._cfg.rules.append(rule)
        self._refresh_rules()
        self._refresh_state()
        return True

    def _delete_rule(self, rule: fw.Rule):
        self._cfg.rules = [r for r in self._cfg.rules if r is not rule]
        self._refresh_rules()
        self._refresh_state()

    def _on_rule_toggled(self, sw, _param, rule: fw.Rule):
        if rule.enabled == sw.get_active():
            return
        rule.enabled = sw.get_active()
        self._refresh_state()
        GLib.idle_add(self._refresh_rules_idle)

    def _refresh_rules_idle(self):
        self._refresh_rules()
        return False

    def _on_enable_toggled(self, row, _param):
        self._cfg.enabled = row.get_active()
        self._refresh_state()

    # ── interface actions ──
    def _add_iface(self, name: str) -> bool:
        if not fw.valid_interface(name):
            self._toast(tr("Invalid interface name: {name}").format(name=name))
            return False
        if name not in self._cfg.trusted_interfaces:
            self._cfg.trusted_interfaces.append(name)
            self._refresh_ifaces()
            self._refresh_state()
        return True

    def _remove_iface(self, name: str):
        self._cfg.trusted_interfaces.remove(name)
        self._refresh_ifaces()
        self._refresh_state()

    def _on_iface_apply(self, entry):
        if self._add_iface(entry.get_text().strip()):
            entry.set_text("")

    # ── saving / applying ──
    def _on_save(self, apply: bool):
        if not self._cfg.enabled and self._saved_enabled:
            dlg = Adw.AlertDialog()
            dlg.set_heading(tr("Turn the firewall off?"))
            dlg.set_body(tr("With the firewall off, every port of this machine is reachable from the network."))
            dlg.add_response("cancel", tr("Cancel"))
            dlg.add_response("off", tr("Turn off"))
            dlg.set_response_appearance("off", Adw.ResponseAppearance.DESTRUCTIVE)
            dlg.set_default_response("cancel")
            dlg.set_close_response("cancel")
            dlg.connect("response", lambda _d, r: r == "off" and self._do_save(apply))
            dlg.present(self)
            return
        self._do_save(apply)

    def _do_save(self, apply: bool):
        previous = fw.read_previous()
        try:
            fw.save(self._cfg)
        except (fw.FirewallError, OSError) as e:
            log.error("save failed: %s", e)
            self._toast(tr("Could not save: {error}").format(error=e))
            return
        log.info("saved %s (apply=%s)", fw.firewall_file(), apply)
        self._saved_snapshot = self._cfg.snapshot()
        self._saved_enabled = self._cfg.enabled
        self._file_exists = True
        self._refresh_banners()
        self._refresh_state()
        if not apply:
            self._toast(tr("Saved. It takes effect at the next rebuild (or use Save & apply)."))
            return
        self._busy = True
        self._refresh_state()
        dlg = RebuildDialog(lambda ok: self._rebuild_finished(ok, previous))
        dlg.present(self)
        dlg.start()

    def _rebuild_finished(self, ok: bool, previous: str | None):
        self._busy = False
        if not ok:
            # A file that breaks the build would also break the auto-update: put it back.
            try:
                fw.restore(previous)
                restored = fw.load()
                self._saved_snapshot = restored.snapshot()
                self._saved_enabled = restored.enabled
                self._file_exists = os.path.exists(fw.firewall_file())
            except OSError as e:
                log.error("restore failed: %s", e)
                self._toast(tr("Could not restore the previous file: {error}").format(error=e))
        self._refresh_state()

    # ── closing ──
    def _on_close_request(self, _win):
        if self._busy:
            return True
        if self._force_close or not self._dirty():
            return False
        dlg = Adw.AlertDialog()
        dlg.set_heading(tr("Discard unsaved changes?"))
        dlg.set_body(tr("Your changes have not been saved."))
        dlg.add_response("cancel", tr("Cancel"))
        dlg.add_response("discard", tr("Discard"))
        dlg.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.set_default_response("cancel")
        dlg.set_close_response("cancel")
        dlg.connect("response", self._on_discard_response)
        dlg.present(self)
        return True

    def _on_discard_response(self, _dlg, response):
        if response == "discard":
            self._force_close = True
            self.close()


# ── Application ───────────────────────────────────────────────────────────────

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.firewall", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = app.get_active_window() or FirewallWindow(app)
        win.present()


def main():
    setup_logging()
    log.info("=== Roudix Firewall started ===")
    log.info("NH_FLAKE: %s", fw.NH_FLAKE)
    return App().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

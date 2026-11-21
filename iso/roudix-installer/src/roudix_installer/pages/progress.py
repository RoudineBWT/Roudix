import subprocess
import threading

from gi.repository import Adw, Gdk, GLib, Gtk, Pango

from roudix_installer.i18n import tr
from roudix_installer.runner import InstallRunner, classify_line
from roudix_installer.ui_helpers import page_with_header

# Roudix palette (Roudix.json, dark), same as the rest of Roudix's theming.
_BASE = "#211a15"
_MANTLE = "#17120f"
_SURFACE0 = "#2a211b"
_TEXT = "#eadbcb"
_BLUE = "#7fa3b5"
_RED = "#e5604d"
_YELLOW = "#f2b05e"
_GREEN = "#a8b86a"

_TERMINAL_CSS = f"""
textview.roudix-terminal,
textview.roudix-terminal text {{
  background-color: {_BASE};
  color: {_TEXT};
  caret-color: {_TEXT};
}}
textview.roudix-terminal {{
  font-family: "JetBrainsMono Nerd Font", "Fira Code", monospace;
  font-size: 11pt;
  padding: 10px 14px;
}}
box.roudix-terminal-frame {{
  border-radius: 12px;
  border: 1px solid {_SURFACE0};
}}
box.roudix-terminal-titlebar {{
  background-color: {_MANTLE};
  padding: 8px 12px;
}}
box.roudix-term-dot {{
  border-radius: 999px;
  min-width: 11px;
  min-height: 11px;
}}
box.roudix-term-dot.dot-red {{ background-color: {_RED}; }}
box.roudix-term-dot.dot-yellow {{ background-color: {_YELLOW}; }}
box.roudix-term-dot.dot-green {{ background-color: {_GREEN}; }}
"""

_css_loaded = False


def _ensure_terminal_css():
    # Scoped by unique CSS class names, so it's safe to load once for the
    # whole app rather than per-page — guarded so repeated ProgressPage
    # construction (shouldn't happen, main.py caches pages, but just in
    # case) never stacks duplicate providers.
    global _css_loaded
    if _css_loaded:
        return
    provider = Gtk.CssProvider()
    provider.load_from_string(_TERMINAL_CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    _css_loaded = True


class ProgressPage(Adw.NavigationPage):
    def __init__(self, state):
        super().__init__(title=tr("Installation"), can_pop=False)
        self.state = state
        # The callbacks run on the worker thread: hop to the GTK main loop.
        self.runner = InstallRunner(
            state,
            log=lambda text: GLib.idle_add(self._log, text),
            status=lambda label, fraction: GLib.idle_add(self._set_status, label, fraction),
        )
        _ensure_terminal_css()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=32, margin_bottom=32, margin_start=32, margin_end=32,
                       vexpand=True)

        self.status_label = Gtk.Label(label=tr("Preparing…"), css_classes=["title-3"],
                                       halign=Gtk.Align.START)
        self.progress = Gtk.ProgressBar(show_text=False)
        box.append(self.status_label)
        box.append(self.progress)

        # ── "terminal" ────────────────────────────────────────────────────
        term_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True,
                              css_classes=["roudix-terminal-frame"])
        term_frame.set_overflow(Gtk.Overflow.HIDDEN)  # clips children to the rounded corners

        titlebar = Gtk.Box(spacing=10, css_classes=["roudix-terminal-titlebar"])
        dots = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        for dot_class in ("dot-red", "dot-yellow", "dot-green"):
            dots.append(Gtk.Box(css_classes=["roudix-term-dot", dot_class]))
        titlebar.append(dots)
        titlebar.append(Gtk.Label(label=tr("Installation log"),
                                   css_classes=["dim-label"], valign=Gtk.Align.CENTER))
        titlebar.append(Gtk.Box(hexpand=True))  # spacer, pushes the copy button to the right
        copy_btn = Gtk.Button(icon_name="edit-copy-symbolic", css_classes=["flat"],
                               valign=Gtk.Align.CENTER,
                               tooltip_text=tr("Copy log"))
        copy_btn.connect("clicked", self._on_copy_log_clicked)
        titlebar.append(copy_btn)
        term_frame.append(titlebar)

        self.log_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                      css_classes=["roudix-terminal"])
        self._init_log_tags()

        self.log_scroller = Gtk.ScrolledWindow(vexpand=True, min_content_height=340)
        self.log_scroller.set_child(self.log_view)
        term_frame.append(self.log_scroller)

        # Whether new output should auto-scroll the view to the bottom.
        # Set in _log() right before each insert (based on whether the
        # user was already at the bottom), then actually applied once the
        # adjustment's `upper` catches up with the new content — see
        # _on_log_extent_changed().
        self._log_follow_tail = True
        log_vadj = self.log_scroller.get_vadjustment()
        if log_vadj is not None:
            log_vadj.connect("notify::upper", self._on_log_extent_changed)

        box.append(term_frame)

        bottom_row = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, margin_top=4)
        self.reboot_check = Gtk.CheckButton(label=tr("Reboot now"), active=True)
        self.reboot_check.set_visible(False)
        bottom_row.append(self.reboot_check)

        self.finish_btn = Gtk.Button(label=tr("Finish"),
                                      css_classes=["suggested-action", "pill"])
        self.finish_btn.connect("clicked", self._on_finish_clicked)
        self.finish_btn.set_visible(False)
        bottom_row.append(self.finish_btn)

        # Shown after a simulation: nothing was installed, so go back to Summary.
        self.back_btn = Gtk.Button(label=tr("Back to summary"), css_classes=["pill"])
        self.back_btn.connect("clicked", self._on_back_clicked)
        self.back_btn.set_visible(False)
        bottom_row.append(self.back_btn)
        box.append(bottom_row)

        self.set_child(page_with_header(tr("Installation"), box))
        self.connect("shown", lambda *_: self._start())

    def _init_log_tags(self):
        buf = self.log_view.get_buffer()
        buf.create_tag("cmd", foreground=_BLUE, weight=Pango.Weight.BOLD)
        buf.create_tag("error", foreground=_RED, weight=Pango.Weight.BOLD)
        buf.create_tag("success", foreground=_GREEN, weight=Pango.Weight.BOLD)

    def _on_copy_log_clicked(self, _btn):
        buf = self.log_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
            self.log_view.get_clipboard().set(text)
        except Exception:  # noqa: BLE001 — clipboard access is best-effort, never worth crashing over
            pass

    def _on_back_clicked(self, _btn):
        nav = self.get_ancestor(Adw.NavigationView)
        if nav is not None:
            nav.pop()

    def _on_finish_clicked(self, _btn):
        if self.reboot_check.get_active():
            GLib.idle_add(self._log, tr("Rebooting…"))
            # Installed NixOS: logind lets the active session reboot without root.
            subprocess.Popen(self.runner.priv(["systemctl", "reboot"],
                                              root=not self.runner.existing))
        else:
            self.get_root().get_application().quit()

    _tag_for_line = staticmethod(classify_line)

    def _log(self, text: str):
        buf = self.log_view.get_buffer()

        # Only auto-follow the tail if the user was already scrolled to the
        # bottom before this line arrived — if they scrolled up to read
        # something, new output shouldn't yank the view back down.
        vadj = self.log_scroller.get_vadjustment()
        if vadj is not None:
            self._log_follow_tail = vadj.get_value() >= (vadj.get_upper() - vadj.get_page_size() - 8)

        tag_name = self._tag_for_line(text)
        end_iter = buf.get_end_iter()
        if tag_name:
            buf.insert_with_tags_by_name(end_iter, text + "\n", tag_name)
        else:
            buf.insert(end_iter, text + "\n")

        # Try scrolling right away — this works when the view's layout is
        # already up to date. If it isn't yet (GTK only recomputes
        # vadj.upper on its next layout pass, which can lag when nothing
        # else is forcing a redraw — e.g. the mouse never enters the
        # terminal), _on_log_extent_changed() below catches it the moment
        # the adjustment actually grows, so the log never looks stuck.
        if self._log_follow_tail and vadj is not None:
            self._scroll_log_to_bottom()

    def _on_log_extent_changed(self, _vadj, _pspec):
        if self._log_follow_tail:
            self._scroll_log_to_bottom()

    def _scroll_log_to_bottom(self):
        vadj = self.log_scroller.get_vadjustment()
        if vadj is not None:
            vadj.set_value(max(0.0, vadj.get_upper() - vadj.get_page_size()))

    def _set_status(self, label: str, fraction: float):
        self.status_label.set_label(label)
        self.progress.set_fraction(fraction)

    def _start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        # The steps live in runner.py (shared with the TUI); this thread only
        # turns its result into buttons.
        ok = self.runner.run()
        if self.runner.is_dry_run():
            GLib.idle_add(self.back_btn.set_visible, True)
        elif ok:
            GLib.idle_add(self.reboot_check.set_visible, True)
            GLib.idle_add(self.finish_btn.set_visible, True)
        else:
            GLib.idle_add(self.reboot_check.set_active, False)
            GLib.idle_add(self.finish_btn.set_visible, True)

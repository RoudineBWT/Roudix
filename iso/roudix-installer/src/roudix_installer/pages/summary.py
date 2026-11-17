from gi.repository import Adw, Gtk

from roudix_installer import existing_nixos
from roudix_installer.i18n import tr
from roudix_installer.summary_rows import summary_rows
from roudix_installer.ui_helpers import page_with_header


class SummaryPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=tr("Summary"))
        self.state = state
        self.on_next = on_next

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.group = Adw.PreferencesGroup(title=tr("Check before starting the install"))
        self._rows: list[Adw.ActionRow] = []
        box.append(self.group)

        existing = state.mode == existing_nixos.MODE_EXISTING
        buttons = Gtk.Box(spacing=12, halign=Gtk.Align.END, margin_top=12)
        # "Simulate" = the dry run: every check that can run without touching
        # the system (config generation, option verification, Nix evaluation).
        sim_btn = Gtk.Button(label=tr("Simulate (nothing is written)"), css_classes=["pill"],
                              tooltip_text=tr("Generates the configuration in a temporary folder and checks that "
                                              "it evaluates. Nothing is partitioned, installed or modified."))
        sim_btn.connect("clicked", lambda *_: self._go(dry_run=True))
        buttons.append(sim_btn)
        # Fresh install wipes a disk (red button); converting a NixOS does not.
        install_btn = Gtk.Button(
            label=tr("Convert this NixOS to Roudix") if existing else tr("Install Roudix"),
            css_classes=["suggested-action" if existing else "destructive-action", "pill"])
        install_btn.connect("clicked", lambda *_: self._go(dry_run=False))
        buttons.append(install_btn)
        box.append(buttons)

        self.set_child(page_with_header(tr("Summary"), scroller))
        self.connect("shown", lambda *_: self._refresh())

    def _go(self, dry_run: bool):
        self.state.dry_run = dry_run
        self.on_next()

    def _refresh(self):
        # Same Adw.PreferencesGroup gotcha as disk.py's partition list:
        # get_first_child()/get_next_sibling() on the group walks its
        # internal structure, not the rows added via .add(), so this
        # never actually removed anything — every visit to Summary was
        # stacking a fresh set of rows under the old ones.
        for row in self._rows:
            self.group.remove(row)
        self._rows.clear()

        rows = summary_rows(self.state)
        for title, value in rows:
            row = Adw.ActionRow(title=title, subtitle=value)
            self.group.add(row)
            self._rows.append(row)

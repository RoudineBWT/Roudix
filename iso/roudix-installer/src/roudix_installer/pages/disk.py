import subprocess

from gi.repository import Adw, Gtk


def list_disks() -> list[dict]:
    """Query real block devices via lsblk. Excludes the live/install medium."""
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,MODEL,TYPE,TRAN"],
        capture_output=True, text=True, check=True,
    ).stdout
    import json
    data = json.loads(out)
    disks = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") == "disk":
            disks.append({
                "path": f"/dev/{dev['name']}",
                "size": dev.get("size", "?"),
                "model": dev.get("model") or "Disque inconnu",
            })
    return disks


class DiskPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Disque")
        self.state = state
        self.on_next = on_next

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)

        warn = Adw.Banner(
            title="⚠ Le disque sélectionné sera entièrement effacé (mode simple)",
            revealed=True,
        )
        box.append(warn)

        self.mode_row = Adw.ComboRow(
            title="Mode de partitionnement",
            model=Gtk.StringList.new(["Simple (EFI + swap + root)", "Avancé (fichier disko.nix custom)"]),
        )
        self.mode_row.connect("notify::selected", self._on_mode_changed)
        box.append(self.mode_row)

        self.disk_group = Adw.PreferencesGroup(title="Choisis un disque")
        self.disk_rows: list[Adw.ActionRow] = []
        self.selected_disk = None

        try:
            disks = list_disks()
        except Exception:
            disks = []

        for d in disks:
            row = Adw.ActionRow(title=d["path"], subtitle=f"{d['model']} — {d['size']}")
            check = Gtk.CheckButton()
            if self.disk_rows:
                check.set_group(self.disk_rows[0].get_activatable_widget())
            row.add_prefix(check)
            row.set_activatable_widget(check)
            check.connect("toggled", self._on_disk_toggled, d["path"])
            self.disk_group.add(row)
            self.disk_rows.append(row)

        box.append(self.disk_group)

        self.advanced_group = Adw.PreferencesGroup(title="Fichier disko.nix")
        self.advanced_row = Adw.ActionRow(title="Aucun fichier sélectionné")
        pick_btn = Gtk.Button(label="Parcourir…", valign=Gtk.Align.CENTER)
        pick_btn.connect("clicked", self._pick_disko_file)
        self.advanced_row.add_suffix(pick_btn)
        self.advanced_group.add(self.advanced_row)
        self.advanced_group.set_visible(False)
        box.append(self.advanced_group)

        next_btn = Gtk.Button(label="Continuer", css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(box)

    def _on_mode_changed(self, row, _pspec):
        advanced = row.get_selected() == 1
        self.state.disk.mode = "advanced" if advanced else "simple"
        self.disk_group.set_visible(not advanced)
        self.advanced_group.set_visible(advanced)

    def _on_disk_toggled(self, check, path):
        if check.get_active():
            self.selected_disk = path
            self.state.disk.device = path

    def _pick_disko_file(self, _btn):
        dialog = Gtk.FileChooserNative.new(
            "Sélectionner un disko.nix", self.get_root(),
            Gtk.FileChooserAction.OPEN, "Choisir", "Annuler",
        )

        def on_response(dlg, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = dlg.get_file().get_path()
                self.state.disk.advanced_disko_path = path
                self.advanced_row.set_title(path)
            dlg.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def _validate(self, _btn):
        # Real app: block "Continuer" + show a toast if no disk / no file chosen.
        self.on_next()

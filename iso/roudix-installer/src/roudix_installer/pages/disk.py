import json
import subprocess

from gi.repository import Adw, GLib, Gtk

MOUNTPOINT_CHOICES = ["Ignorer", "/", "/boot (EFI)", "swap"]
MOUNTPOINT_TO_STATE = {"/": "/", "/boot (EFI)": "/boot", "swap": "swap"}


def list_disks() -> list[dict]:
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,MODEL,TYPE"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    return [
        {"path": f"/dev/{d['name']}", "size": d.get("size", "?"),
         "model": d.get("model") or "Disque inconnu"}
        for d in data.get("blockdevices", []) if d.get("type") == "disk"
    ]


def list_partitions(disk_path: str) -> list[dict]:
    name = disk_path.removeprefix("/dev/")
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,FSTYPE,TYPE", f"/dev/{name}"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    parts = []
    for d in data.get("blockdevices", []):
        for child in d.get("children", []):
            if child.get("type") == "part":
                parts.append({
                    "path": f"/dev/{child['name']}",
                    "size": child.get("size", "?"),
                    "fstype": child.get("fstype") or "?",
                })
    return parts


class DiskPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title="Disque")
        self.state = state
        self.on_next = on_next
        self.selected_disk = None
        self.partition_dropdowns: dict[str, Gtk.DropDown] = {}

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.warn_banner = Adw.Banner(
            title="⚠ Le disque sélectionné sera entièrement effacé (mode simple)",
            revealed=True,
        )
        box.append(self.warn_banner)

        self.mode_row = Adw.ComboRow(
            title="Mode de partitionnement",
            model=Gtk.StringList.new([
                "Simple (EFI + swap + root, efface tout)",
                "Avancé (fichier disko.nix custom)",
                "Manuel (partitionner soi-même avec GParted)",
            ]),
        )
        self.mode_row.connect("notify::selected", self._on_mode_changed)
        box.append(self.mode_row)

        # ── mode simple ──
        self.disk_group = Adw.PreferencesGroup(title="Choisis un disque")
        box.append(self.disk_group)

        # ── mode avancé ──
        self.advanced_group = Adw.PreferencesGroup(title="Fichier disko.nix")
        self.advanced_row = Adw.ActionRow(title="Aucun fichier sélectionné")
        pick_btn = Gtk.Button(label="Parcourir…", valign=Gtk.Align.CENTER)
        pick_btn.connect("clicked", self._pick_disko_file)
        self.advanced_row.add_suffix(pick_btn)
        self.advanced_group.add(self.advanced_row)
        self.advanced_group.set_visible(False)
        box.append(self.advanced_group)

        # ── mode manuel ──
        self.manual_group = Adw.PreferencesGroup(title="Partitionnement manuel")
        self.manual_disk_row = Adw.ComboRow(title="Disque à partitionner")
        self.manual_group.add(self.manual_disk_row)

        gparted_btn = Gtk.Button(label="Ouvrir GParted", css_classes=["pill"],
                                  halign=Gtk.Align.START, margin_top=6, margin_bottom=6)
        gparted_btn.connect("clicked", self._launch_gparted)
        self.manual_group.add(gparted_btn)

        self.partitions_group = Adw.PreferencesGroup(
            title="Assigner les points de montage",
            description="Une fois GParted fermé, associe chaque partition à un point de montage.",
        )
        self.manual_group.add(self.partitions_group)
        self.manual_group.set_visible(False)
        box.append(self.manual_group)

        # Populated last: fills both disk_group (checkboxes) and
        # manual_disk_row (dropdown) — both must already exist.
        self._populate_disk_group()

        next_btn = Gtk.Button(label="Continuer", css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(scroller)

    def _populate_disk_group(self):
        try:
            self.disks = list_disks()
        except Exception:
            self.disks = []

        self.disk_names = Gtk.StringList.new([f"{d['path']} — {d['model']} ({d['size']})" for d in self.disks])
        self.manual_disk_row.set_model(self.disk_names)

        first_group_check = None
        for d in self.disks:
            row = Adw.ActionRow(title=d["path"], subtitle=f"{d['model']} — {d['size']}")
            check = Gtk.CheckButton()
            if first_group_check is None:
                first_group_check = check
            else:
                check.set_group(first_group_check)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            check.connect("toggled", self._on_disk_toggled, d["path"])
            self.disk_group.add(row)

    def _on_mode_changed(self, row, _pspec):
        idx = row.get_selected()
        self.state.disk.mode = ["simple", "advanced", "manual"][idx]
        self.warn_banner.set_visible(idx == 0)
        self.disk_group.set_visible(idx == 0)
        self.advanced_group.set_visible(idx == 1)
        self.manual_group.set_visible(idx == 2)

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

    def _launch_gparted(self, _btn):
        idx = self.manual_disk_row.get_selected()
        if idx == Gtk.INVALID_LIST_POSITION or not self.disks:
            return
        disk_path = self.disks[idx]["path"]

        # GParted needs root — same sudo/NOPASSWD live-user setup used to
        # elevate roudix-installer itself. Runs blocking in a thread so the
        # UI doesn't freeze while GParted is open.
        import threading

        def run():
            subprocess.run(["sudo", "-n", "gparted", disk_path])
            GLib.idle_add(self._refresh_partitions, disk_path)

        threading.Thread(target=run, daemon=True).start()

    def _refresh_partitions(self, disk_path: str):
        child = self.partitions_group.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.partitions_group.remove(child)
            child = nxt
        self.partition_dropdowns.clear()

        try:
            parts = list_partitions(disk_path)
        except Exception:
            parts = []

        for p in parts:
            row = Adw.ActionRow(title=p["path"], subtitle=f"{p['fstype']} — {p['size']}")
            dropdown = Gtk.DropDown.new_from_strings(MOUNTPOINT_CHOICES)
            dropdown.set_valign(Gtk.Align.CENTER)
            row.add_suffix(dropdown)
            self.partitions_group.add(row)
            self.partition_dropdowns[p["path"]] = dropdown

    def _validate(self, _btn):
        if self.state.disk.mode == "manual":
            mapping = {}
            for path, dropdown in self.partition_dropdowns.items():
                choice = MOUNTPOINT_CHOICES[dropdown.get_selected()]
                if choice != "Ignorer":
                    mapping[path] = MOUNTPOINT_TO_STATE[choice]
            self.state.disk.manual_partitions = mapping
        # Real app: block "Continuer" + toast if nothing usable was chosen
        # (no disk / no file / no "/" mountpoint assigned).
        self.on_next()

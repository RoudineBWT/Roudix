import json
import subprocess
import threading

from gi.repository import Adw, GLib, Gtk

from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

# index-based, not string-based, so the mapping doesn't depend on language
MOUNTPOINT_VALUES = [None, "/", "/boot", "swap"]


def list_disks() -> list[dict]:
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,MODEL,TYPE"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    return [
        {"path": f"/dev/{d['name']}", "size": d.get("size", "?"),
         "model": d.get("model") or L("Disque inconnu", "Unknown disk")}
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
        super().__init__(title=L("Disque", "Disk"))
        self.state = state
        self.on_next = on_next
        self.selected_disk = None
        self.partition_dropdowns: dict[str, Gtk.DropDown] = {}
        self.mountpoint_choices = [
            L("Ignorer", "Skip"), "/", L("/boot (EFI)", "/boot (EFI)"), L("swap", "swap"),
        ]

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        scroller.set_child(box)

        self.warn_banner = Adw.Banner(
            title=L("⚠ Le disque sélectionné sera entièrement effacé (mode simple)",
                     "⚠ The selected disk will be completely wiped (simple mode)"),
            revealed=True,
        )
        box.append(self.warn_banner)

        self.mode_row = Adw.ComboRow(
            title=L("Mode de partitionnement", "Partitioning mode"),
            model=Gtk.StringList.new([
                L("Simple (EFI + swap + root, efface tout)", "Simple (EFI + swap + root, wipes everything)"),
                L("Avancé (fichier disko.nix custom)", "Advanced (custom disko.nix file)"),
                L("Manuel (partitionner soi-même)", "Manual (partition it yourself)"),
            ]),
        )
        self.mode_row.connect("notify::selected", self._on_mode_changed)
        box.append(self.mode_row)

        # ── options du mode simple : filesystem, taille /boot, swap ──
        self.simple_options_group = Adw.PreferencesGroup(title=L("Options", "Options"))

        self.filesystem_row = Adw.ComboRow(
            title=L("Système de fichiers", "Filesystem"),
            model=Gtk.StringList.new([
                L("ext4 (simple)", "ext4 (simple)"),
                L("btrfs (subvolumes @, @home, @nix, @log + zstd)", "btrfs (@, @home, @nix, @log subvolumes + zstd)"),
            ]),
        )
        self.simple_options_group.add(self.filesystem_row)

        self.boot_size_row = Adw.SpinRow.new_with_range(2, 16, 1)
        self.boot_size_row.set_title(L("Taille de /boot (Go)", "/boot size (GB)"))
        self.boot_size_row.set_subtitle(L(
            "4G recommandé avec CachyOS + plusieurs générations Limine — 2G minimum",
            "4G recommended with CachyOS + multiple Limine generations — 2G minimum",
        ))
        self.boot_size_row.set_value(4)
        self.simple_options_group.add(self.boot_size_row)

        self.swap_row = Adw.SwitchRow(title=L("Ajouter une partition swap", "Add a swap partition"))
        self.swap_row.set_subtitle(L(
            "Désactivé par défaut — zram fait déjà ce travail",
            "Off by default — zram already covers this",
        ))
        self.swap_row.set_active(False)
        self.swap_row.connect("notify::active", lambda *_: self._sync_swap_size_row())
        self.simple_options_group.add(self.swap_row)

        self.swap_size_row = Adw.SpinRow.new_with_range(1, 64, 1)
        self.swap_size_row.set_title(L("Taille du swap (Go)", "Swap size (GB)"))
        self.swap_size_row.set_value(8)
        self.swap_size_row.set_visible(False)
        self.simple_options_group.add(self.swap_size_row)

        box.append(self.simple_options_group)

        # ── mode simple ──
        self.disk_group = Adw.PreferencesGroup(title=L("Choisis un disque", "Choose a disk"))
        box.append(self.disk_group)

        # ── mode avancé ──
        self.advanced_group = Adw.PreferencesGroup(title=L("Fichier disko.nix", "disko.nix file"))
        self.advanced_row = Adw.ActionRow(title=L("Aucun fichier sélectionné", "No file selected"))
        pick_btn = Gtk.Button(label=L("Parcourir…", "Browse…"), valign=Gtk.Align.CENTER)
        pick_btn.connect("clicked", self._pick_disko_file)
        self.advanced_row.add_suffix(pick_btn)
        self.advanced_group.add(self.advanced_row)
        self.advanced_group.set_visible(False)
        box.append(self.advanced_group)

        # ── mode manuel ──
        self.manual_group = Adw.PreferencesGroup(title=L("Partitionnement manuel", "Manual partitioning"))
        self.manual_disk_row = Adw.ComboRow(title=L("Disque à partitionner", "Disk to partition"))
        self.manual_disk_row.connect("notify::selected", self._on_manual_disk_selected)
        self.manual_group.add(self.manual_disk_row)

        gparted_row = Adw.ActionRow(title=L("Partitionner", "Partition it"))
        gparted_btn = Gtk.Button(label=L("Ouvrir GParted", "Open GParted"), valign=Gtk.Align.CENTER)
        gparted_btn.connect("clicked", self._launch_gparted)
        refresh_btn = Gtk.Button(
            label=L("Rafraîchir", "Refresh"), valign=Gtk.Align.CENTER,
            tooltip_text=L(
                "Si tu as déjà partitionné toi-même (fdisk, cfdisk…) dans un terminal",
                "If you already partitioned it yourself (fdisk, cfdisk…) in a terminal",
            ),
        )
        refresh_btn.connect("clicked", self._on_refresh_clicked)
        button_box = Gtk.Box(spacing=6)
        button_box.append(gparted_btn)
        button_box.append(refresh_btn)
        gparted_row.add_suffix(button_box)
        self.manual_group.add(gparted_row)

        self.partitions_group = Adw.PreferencesGroup(
            title=L("Assigner les points de montage", "Assign mountpoints"),
            description=L(
                "Une fois le partitionnement fait, associe chaque partition à un point de montage.",
                "Once partitioning is done, assign each partition to a mountpoint.",
            ),
        )
        self.manual_group.add(self.partitions_group)
        self.manual_group.set_visible(False)
        box.append(self.manual_group)

        # Populated last: fills both disk_group (checkboxes) and
        # manual_disk_row (dropdown) — both must already exist.
        self._populate_disk_group()

        next_btn = Gtk.Button(label=L("Continuer", "Continue"), css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(page_with_header(L("Disque", "Disk"), scroller))

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
        self.simple_options_group.set_visible(idx == 0)
        self.disk_group.set_visible(idx == 0)
        self.advanced_group.set_visible(idx == 1)
        self.manual_group.set_visible(idx == 2)

    def _sync_swap_size_row(self):
        self.swap_size_row.set_visible(self.swap_row.get_active())

    def _on_disk_toggled(self, check, path):
        if check.get_active():
            self.selected_disk = path
            self.state.disk.device = path

    def _pick_disko_file(self, _btn):
        dialog = Gtk.FileChooserNative.new(
            L("Sélectionner un disko.nix", "Select a disko.nix"), self.get_root(),
            Gtk.FileChooserAction.OPEN, L("Choisir", "Choose"), L("Annuler", "Cancel"),
        )

        def on_response(dlg, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = dlg.get_file().get_path()
                self.state.disk.advanced_disko_path = path
                self.advanced_row.set_title(path)
            dlg.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def _on_manual_disk_selected(self, row, _pspec):
        idx = row.get_selected()
        if idx != Gtk.INVALID_LIST_POSITION and self.disks:
            self._refresh_partitions(self.disks[idx]["path"])

    def _on_refresh_clicked(self, _btn):
        idx = self.manual_disk_row.get_selected()
        if idx != Gtk.INVALID_LIST_POSITION and self.disks:
            self._refresh_partitions(self.disks[idx]["path"])

    def _launch_gparted(self, _btn):
        idx = self.manual_disk_row.get_selected()
        if idx == Gtk.INVALID_LIST_POSITION or not self.disks:
            return
        disk_path = self.disks[idx]["path"]

        # GParted needs root — same sudo/NOPASSWD live-user setup used to
        # elevate roudix-installer itself. Runs blocking in a thread so the
        # UI doesn't freeze while GParted is open.
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
            dropdown = Gtk.DropDown.new_from_strings(self.mountpoint_choices)
            dropdown.set_valign(Gtk.Align.CENTER)
            row.add_suffix(dropdown)
            self.partitions_group.add(row)
            self.partition_dropdowns[p["path"]] = dropdown

    def _validate(self, _btn):
        if self.state.disk.mode == "simple":
            self.state.disk.filesystem = "btrfs" if self.filesystem_row.get_selected() == 1 else "ext4"
            self.state.disk.boot_size_gb = int(self.boot_size_row.get_value())
            self.state.disk.enable_swap = self.swap_row.get_active()
            self.state.disk.swap_size_gb = int(self.swap_size_row.get_value())
        elif self.state.disk.mode == "manual":
            mapping = {}
            for path, dropdown in self.partition_dropdowns.items():
                value = MOUNTPOINT_VALUES[dropdown.get_selected()]
                if value is not None:
                    mapping[path] = value
            self.state.disk.manual_partitions = mapping
        # Real app: block "Continuer"/"Continue" + toast if nothing usable
        # was chosen (no disk / no file / no "/" mountpoint assigned).
        self.on_next()

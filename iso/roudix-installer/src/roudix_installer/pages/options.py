from gi.repository import Adw, Gtk


class OptionsPage(Adw.NavigationPage):
    """
    Same choices roudix-installer.sh already asks for, just as combo
    rows instead of a read -p loop. Nothing here should surprise you —
    it's your script's option list, rendered.
    """

    DESKTOPS = ["niri", "hyprland", "gnome", "plasma"]
    SHELLS = ["noctalia", "dms", "caelestia", "none"]
    KERNELS = ["cachyos-auto", "cachyos-lts", "vanilla"]
    BOOTLOADERS = ["limine", "systemd-boot"]
    BROWSERS = ["brave", "firefox"]
    MATRIX = ["none", "element", "cinny"]

    def __init__(self, state, on_next):
        super().__init__(title="Options")
        self.state = state
        self.on_next = on_next

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)

        group = Adw.PreferencesGroup(title="Système")
        self.hostname_row = Adw.EntryRow(title="Nom de machine")
        self.hostname_row.set_text(state.hostname)
        self.username_row = Adw.EntryRow(title="Utilisateur")
        self.username_row.set_text(state.username)
        group.add(self.hostname_row)
        group.add(self.username_row)
        box.append(group)

        env_group = Adw.PreferencesGroup(title="Environnement")
        self.desktop_row = self._combo("Compositeur / bureau", self.DESKTOPS, state.desktop)
        self.shell_row = self._combo("Shell graphique", self.SHELLS, state.shell)
        self.kernel_row = self._combo("Kernel", self.KERNELS, state.kernel)
        self.bootloader_row = self._combo("Bootloader", self.BOOTLOADERS, state.bootloader)
        self.browser_row = self._combo("Navigateur", self.BROWSERS, state.browser)
        for r in (self.desktop_row, self.shell_row, self.kernel_row,
                  self.bootloader_row, self.browser_row):
            env_group.add(r)
        box.append(env_group)

        extra_group = Adw.PreferencesGroup(title="Extras")
        self.matrix_row = self._combo("Client Matrix", self.MATRIX, state.matrix_client)
        extra_group.add(self.matrix_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)

        next_btn = Gtk.Button(label="Continuer", css_classes=["suggested-action", "pill"],
                               halign=Gtk.Align.END, margin_top=12)
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(box)

    def _combo(self, title, options, current):
        row = Adw.ComboRow(title=title, model=Gtk.StringList.new(options))
        row.set_selected(options.index(current) if current in options else 0)
        return row

    def _validate(self, _btn):
        s = self.state
        s.hostname = self.hostname_row.get_text()
        s.username = self.username_row.get_text()
        s.desktop = self.DESKTOPS[self.desktop_row.get_selected()]
        s.shell = self.SHELLS[self.shell_row.get_selected()]
        s.kernel = self.KERNELS[self.kernel_row.get_selected()]
        s.bootloader = self.BOOTLOADERS[self.bootloader_row.get_selected()]
        s.browser = self.BROWSERS[self.browser_row.get_selected()]
        s.matrix_client = self.MATRIX[self.matrix_row.get_selected()]
        s.waydroid_enable = self.waydroid_row.get_active()
        self.on_next()

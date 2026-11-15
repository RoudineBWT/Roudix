from gi.repository import Adw, Gtk

from roudix_installer import existing_nixos, host_defaults, host_profile, multiboot
from roudix_installer.state import valid_username
from roudix_installer.hardware_detect import detect_cpu, detect_gpu, detect_laptop, detect_thinkpad, detect_vm, detect_main_screen, detect_screen_count, is_bios_boot
from roudix_installer.i18n import tr, tr_noop
from roudix_installer.ui_helpers import page_with_header

# Option lists: see choices.py (GTK-free, shared with the TUI).
from roudix_installer.choices import (  # noqa: F401 — option lists live in choices.py (shared with the TUI)
    _cpus,
    _gpus,
    _laptop_backends,
    _memory_types,
    _mesa_git_sources,
    _nvidia_driver_sources,
    _nvidia_kernel_sources,
    _video_editors,
    _zen_variants,
    seed_allowed,
    _kernels,
    _kernels_chaotic,
    _browsers,
    _brave_variants,
    _desktops,
    _mark_detected,
    _shells,
    _latest_title,
    _default_shells,
    _terminals,
    _file_managers,
    _editors,
    _desktop_integrations,
    _rgb_options,
    _bootloaders,
    _plymouth_themes,
    _eac_vendors,
    _boot_aspects,
    _boot_resolutions,
    _branches,
    _matrix,
    _discord,
    _telegram,
    _video_player,
    _torrent_client,
    _music_player,
    _fluxer_channel,
    _mail_client,
    _password_manager,
    _office,
    _spicetify_themes,
    _timezones,
    _locales,
    _keymaps,
    _gfx_keyboard_layouts,
    LATEST_DESKTOPS,
    LATEST_SHELLS,
)


class OptionsPage(Adw.NavigationPage):
    def __init__(self, state, on_next):
        super().__init__(title=tr("Options"))
        self.state = state
        self.on_next = on_next
        self._rows = {}  # id(row) -> value list

        scroller = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        scroller.set_child(box)

        # ── Utilisateur ──
        user_group = Adw.PreferencesGroup(title=tr("User"))
        self.username_row = Adw.EntryRow(title=tr("Username"))
        self.username_row.set_text(state.username)
        user_group.add(self.username_row)


        self.password_row = Adw.PasswordEntryRow(title=tr("Password"))
        user_group.add(self.password_row)
        # Already-installed NixOS: the account exists and keeps its password,
        # so the password rows are not asked at all.
        self._existing = state.mode == existing_nixos.MODE_EXISTING

        self.password_confirm_row = Adw.PasswordEntryRow(
            title=tr("Confirm password")
        )
        user_group.add(self.password_confirm_row)
        if self._existing:
            self.password_row.set_visible(False)
            self.password_confirm_row.set_visible(False)
            self.username_row.set_editable(False)

        self.password_warning = Gtk.Label(
            css_classes=["error", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )
        box.append(user_group)
        box.append(self.password_warning)

        # ── Answers pre-filled from the chosen profile ──
        # For a profile that lists its options (nixie), start from the values
        # of its local.nix.example instead of the wizard's generic defaults.
        # Done before hardware detection below, so a detected GPU/CPU still
        # wins over the example's (which describes one specific machine).
        seeded = host_defaults.seed_state(state, state.hostname, allowed=self._seed_allowed())
        if seeded:
            box.append(Gtk.Label(
                label=tr("Answers pre-filled with the “{hostname}” profile's values.").format(hostname=state.hostname),
                css_classes=["dim-label", "caption"], wrap=True, xalign=0,
            ))

        # ── Hardware ──
        gpu_detected, nvidia_laptop_detected = detect_gpu()
        cpu_detected = detect_cpu()
        # Detection only picks a sensible default — never overrides a
        # value the user already set on a prior visit to this page (this
        # page is only ever built once per session, so at this point
        # `state` still holds nothing but its dataclass defaults).
        if gpu_detected:
            state.gpu = gpu_detected
            state.nvidia_laptop = nvidia_laptop_detected
        if cpu_detected:
            state.cpu = cpu_detected
        # Laptop (TLP) / ThinkPad: only ever switched ON by detection, so a
        # profile that seeded them (hosts/nixie) is never turned off.
        if nvidia_laptop_detected or detect_laptop():
            state.laptop = True
        if detect_thinkpad():
            state.laptop = True
            state.laptop_thinkpad = True
        # Inside a VM: the old bash installer pre-enabled the guest tweaks too.
        if detect_vm():
            state.vm_guest = True

        hw_group = Adw.PreferencesGroup(title=tr("Hardware"))
        self.gpu_row = self._combo(
            tr("GPU"),
            _mark_detected(_gpus(), gpu_detected),
            state.gpu,
        )
        hw_group.add(self.gpu_row)

        self.nvidia_laptop_row = Adw.SwitchRow(
            title=tr("Optimus laptop (Intel/AMD + NVIDIA dGPU)")
        )
        self.nvidia_laptop_row.set_active(state.nvidia_laptop)
        hw_group.add(self.nvidia_laptop_row)

        self.laptop_row = Adw.SwitchRow(
            title=tr("Laptop (TLP)")
        )
        self.laptop_row.set_active(state.laptop)
        hw_group.add(self.laptop_row)

        # roudix.laptop.enable force-disables tuned (see
        # modules/system/power/laptop.nix) — surface the same trade-off
        # here that the gaming module warns about at eval time.
        self.laptop_gaming_note = Gtk.Label(
            label=tr("Disables tuned in favor of TLP: if gaming is also enabled, "
                "game-performance will still launch games normally but "
                "without the roudix-gaming CPU profile. On a gaming laptop, "
                "pick tuned above instead."),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )

        self.laptop_backend_row = self._combo(
            tr("Laptop power manager"),
            _laptop_backends(),
            state.laptop_backend,
        )
        hw_group.add(self.laptop_backend_row)

        self.thinkpad_row = Adw.SwitchRow(
            title=tr("ThinkPad (40/80% battery charge thresholds)")
        )
        self.thinkpad_row.set_active(state.laptop_thinkpad)
        hw_group.add(self.thinkpad_row)

        self.undervolt_row = Adw.SwitchRow(
            title=tr("AMD GPU undervolting (lact, amdgpu.ppfeaturemask)")
        )
        self.undervolt_row.set_active(state.undervolt_enable)
        hw_group.add(self.undervolt_row)

        self.cpu_row = self._combo(
            "CPU",
            _mark_detected(_cpus(), cpu_detected),
            state.cpu,
        )
        hw_group.add(self.cpu_row)

        self.kernel_row = self._combo(tr("Kernel"), _kernels(), state.kernel)
        hw_group.add(self.kernel_row)

        # Nvidia only (see _sync_nvidia_row): where the kernel and the driver
        # come from, and the beta driver.
        self.nvidia_kernel_source_row = self._combo(
            tr("Kernel source (Nvidia)"),
            _nvidia_kernel_sources(),
            state.nvidia_kernel_source,
        )
        self.nvidia_kernel_source_row.set_subtitle(
            tr("Chaotic-Nyx: precompiled Nvidia module. xddxdd: more kernels, Nvidia module built locally.")
        )
        hw_group.add(self.nvidia_kernel_source_row)

        self.nvidia_driver_source_row = self._combo(
            tr("Nvidia driver source"),
            _nvidia_driver_sources(),
            state.nvidia_driver_source,
        )
        self.nvidia_driver_source_row.set_subtitle(
            tr("nixpkgs: always built locally against your kernel.")
        )
        hw_group.add(self.nvidia_driver_source_row)

        self.nvidia_open_row = Adw.SwitchRow(title=tr("Open kernel modules"))
        self.nvidia_open_row.set_subtitle(
            tr("RTX 20xx and newer. Turn off for GTX 10xx / 16xx cards.")
        )
        self.nvidia_open_row.set_active(state.nvidia_open)
        hw_group.add(self.nvidia_open_row)

        self.nvidia_beta_row = Adw.SwitchRow(title=tr("Nvidia beta driver (built locally)"))
        self.nvidia_beta_row.set_active(state.nvidia_beta)
        hw_group.add(self.nvidia_beta_row)
        box.append(hw_group)
        box.append(self.laptop_gaming_note)

        if gpu_detected or cpu_detected:
            hw_note = Gtk.Label(
                label=tr("GPU / CPU auto-detected — change them above if needed."),
                css_classes=["dim-label", "caption"],
                wrap=True,
                xalign=0,
            )
            box.append(hw_note)

        self._sync_nvidia_row()
        self._sync_undervolt_row()
        self._sync_kernel_row()

        # ── Navigateur ──
        browser_group = Adw.PreferencesGroup(title=tr("Browser"))
        browsers = _browsers()
        self.browser_row = self._combo(
            tr("Browser"),
            browsers,
            state.browser if state.browser in dict(browsers) else "brave",
        )
        browser_group.add(self.browser_row)

        self.brave_variant_row = self._combo(
            tr("Brave variant"), _brave_variants(), "brave"
        )
        browser_group.add(self.brave_variant_row)

        self.zen_row = Adw.SwitchRow(
            title=tr("Also install Zen Browser")
        )
        self.zen_row.set_active(state.zen_browser)
        browser_group.add(self.zen_row)

        self.zen_variant_row = self._combo(
            tr("Zen channel"),
            _zen_variants(),
            state.zen_variant,
        )
        browser_group.add(self.zen_variant_row)

        self.zen_mods_row = Adw.EntryRow(
            title=tr("Zen mods (comma-separated)")
        )
        self.zen_mods_row.set_text(", ".join(state.zen_mods))
        browser_group.add(self.zen_mods_row)

        self.zen_sine_row = Adw.SwitchRow(
            title=tr("Enable Sine (Zen mod engine)")
        )
        self.zen_sine_row.set_active(state.zen_sine_enable)
        browser_group.add(self.zen_sine_row)

        self.zen_sine_mods_row = Adw.EntryRow(
            title=tr("Sine mods (comma-separated)")
        )
        self.zen_sine_mods_row.set_text(", ".join(state.zen_sine_mods))
        browser_group.add(self.zen_sine_mods_row)
        box.append(browser_group)
        self._sync_brave_row()
        self._sync_zen_rows()

        # ── Bureau ──
        desktop_group = Adw.PreferencesGroup(title=tr("Desktop"))
        self.desktop_row = self._combo(
            tr("Compositor / desktop"),
            _desktops(),
            state.desktop,
        )
        desktop_group.add(self.desktop_row)

        self.shell_row = self._combo(
            tr("Graphical shell (bar/UI)"),
            _shells(state.desktop),
            state.desktop_shell,
        )
        desktop_group.add(self.shell_row)

        # roudix.desktop.latest.<id>: off (default) = nixpkgs version, on =
        # latest version from the project's flake. One row for the chosen
        # compositor, one for the chosen shell; each is only shown while that
        # compositor / shell is selected (see _sync_latest_rows).
        self.latest_de_row = Adw.SwitchRow(
            title=_latest_title("Niri"),
            subtitle=tr("Off: nixpkgs version"),
        )
        self.latest_de_row.set_active(False)
        desktop_group.add(self.latest_de_row)

        self.latest_shell_row = Adw.SwitchRow(
            title=_latest_title("Noctalia"),
            subtitle=tr("Off: nixpkgs version"),
        )
        self.latest_shell_row.set_active(False)
        desktop_group.add(self.latest_shell_row)

        self.latest_note = Gtk.Label(
            label=tr("⚠ Roudix configurations are written for the flake (latest) "
                "versions first. On the nixpkgs version, a configuration error "
                "saying that an option, a setting or a key \"does not exist\" is "
                "normal: it was added after the nixpkgs version. Wait for nixpkgs "
                "to catch up, or turn the latest version on."),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
            visible=False,
        )
        self.latest_note.set_margin_start(12)
        self.latest_note.set_margin_end(12)
        self.latest_note.set_margin_top(6)
        self.latest_note.set_margin_bottom(6)
        desktop_group.add(self.latest_note)

        self.default_shell_row = self._combo(
            tr("Default shell"),
            _default_shells(),
            state.default_shell,
        )
        desktop_group.add(self.default_shell_row)

        self.terminal_row = self._combo(
            tr("Terminal"), _terminals(), state.terminal
        )
        desktop_group.add(self.terminal_row)

        self.file_manager_row = self._combo(
            tr("File manager"),
            _file_managers(),
            state.file_manager,
        )
        desktop_group.add(self.file_manager_row)

        self.editor_row = self._combo(
            tr("Code editor"),
            _editors(),
            state.editor,
        )
        desktop_group.add(self.editor_row)

        self.desktop_integration_row = self._combo(
            tr("Keyring / xdg-desktop-portal"),
            _desktop_integrations(),
            state.desktop_integration,
        )
        desktop_group.add(self.desktop_integration_row)
        box.append(desktop_group)
        self._sync_shell_row()
        self._sync_latest_rows()
        self._sync_file_manager_row()
        self._sync_desktop_integration_row()
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_file_manager_row()
        )
        self.desktop_row.connect(
            "notify::selected", lambda *_: self._sync_desktop_integration_row()
        )

        # ── System ──
        sys_group = Adw.PreferencesGroup(title=tr("System"))
        self.vm_guest_row = Adw.SwitchRow(
            title=tr("Installing inside a VM")
        )
        self.vm_guest_row.set_active(state.vm_guest)
        sys_group.add(self.vm_guest_row)

        self.gaming_row = Adw.SwitchRow(
            title=tr("Gaming packages (Steam, Wine, Lutris…)")
        )
        self.gaming_row.set_active(state.gaming)
        sys_group.add(self.gaming_row)

        self.ananicy_row = Adw.SwitchRow(
            title=tr("Ananicy (automatic gaming scheduling)")
        )
        self.ananicy_row.set_active(state.ananicy_enable)
        sys_group.add(self.ananicy_row)

        self.millennium_row = Adw.SwitchRow(
            title=tr("Millennium (modded Steam client: themes and plugins)"),
            subtitle=tr("Unofficial mod — off = stock Steam"),
        )
        self.millennium_row.set_active(state.gaming_steam_millennium)
        sys_group.add(self.millennium_row)

        self.gaming_apps_rows = {}
        for attr, title, default in (
            ("lutris", tr_noop("Lutris"), state.gaming_apps_lutris),
            ("heroic", tr_noop("Heroic Games Launcher (Epic/GOG/Amazon)"), state.gaming_apps_heroic),
            ("faugus", tr_noop("Faugus Launcher"), state.gaming_apps_faugus),
            ("prismlauncher", tr_noop("Prism Launcher (Minecraft)"), state.gaming_apps_prismlauncher),
            ("modrinth", tr_noop("Modrinth App (alternative to Prism)"), state.gaming_apps_modrinth),
            ("vintagestory", tr_noop("Vintage Story"), state.gaming_apps_vintagestory),
            ("mangohud", tr_noop("MangoHud (in-game perf overlay)"), state.gaming_apps_mangohud),
        ):
            row = Adw.SwitchRow(title=tr(title))
            row.set_active(default)
            sys_group.add(row)
            self.gaming_apps_rows[attr] = row

        self.mesa_git_row = Adw.SwitchRow(
            title=tr("Mesa git (bleeding-edge graphics drivers)")
        )
        self.mesa_git_row.set_active(state.mesa_use_git)
        sys_group.add(self.mesa_git_row)

        self.mesa_git_source_row = self._combo(
            tr("Mesa git source"),
            _mesa_git_sources(),
            state.mesa_git_source,
        )
        sys_group.add(self.mesa_git_source_row)
        self.mesa_git_row.connect("notify::active", lambda *_: self._sync_mesa_row())
        self._sync_mesa_row()

        self.timezone_row = self._combo(
            tr("Timezone"), _timezones(), state.timezone
        )
        sys_group.add(self.timezone_row)

        self.locale_row = self._combo(
            tr("System language"), _locales(), state.locale
        )
        sys_group.add(self.locale_row)

        self.keymap_row = self._combo(
            tr("Keyboard layout (console)"),
            _keymaps(),
            state.keymap,
        )
        sys_group.add(self.keymap_row)

        _initial_gfx_value = (
            f"{state.keyboard_layout}:{state.keyboard_variant}"
            if state.keyboard_variant
            else f"{state.keyboard_layout}:"
        )
        self.gfx_keyboard_row = self._combo(
            tr("Graphical keyboard layout (Wayland)"),
            _gfx_keyboard_layouts(),
            _initial_gfx_value,
        )
        sys_group.add(self.gfx_keyboard_row)
        box.append(sys_group)
        self._sync_ananicy_row()

        # ── RGB ──
        rgb_group = Adw.PreferencesGroup(title="RGB")
        self.rgb_row = self._combo(
            tr("RGB controller"), _rgb_options(), state.rgb
        )
        rgb_group.add(self.rgb_row)

        self.memory_rgb_row = Adw.SwitchRow(
            title=tr("RAM RGB (Corsair DDR4/DDR5)")
        )
        self.memory_rgb_row.set_active(state.memory_rgb_enable)
        rgb_group.add(self.memory_rgb_row)

        self.memory_type_row = self._combo(
            tr("RAM type"),
            _memory_types(),
            state.memory_type,
        )
        rgb_group.add(self.memory_type_row)

        self.memory_smbus_row = Adw.EntryRow(
            title=tr("SMBus (e.g. i2c-1)")
        )
        self.memory_smbus_row.set_text(state.memory_smbus)
        rgb_group.add(self.memory_smbus_row)

        self.memory_sku_row = Adw.EntryRow(
            title=tr("RAM SKU (part number)")
        )
        self.memory_sku_row.set_text(state.memory_sku)
        rgb_group.add(self.memory_sku_row)
        box.append(rgb_group)
        self._sync_memory_rows()

        self.rgb_note = rgb_note = Gtk.Label(
            label=tr("SMBus / RAM SKU aren't auto-detected — find them via "
                "\"i2cdetect -l\" and \"sudo dmidecode -t memory | grep 'Part Number'\"."),
            css_classes=["dim-label", "caption"],
            wrap=True,
            xalign=0,
        )
        box.append(rgb_note)

        # ── Extras ──
        extra_group = Adw.PreferencesGroup(title=tr("Extras"))
        self.gta_fix_row = Adw.SwitchRow(
            title=tr("GTA Online fix (blocks the Linux anti-cheat IP)")
        )
        self.gta_fix_row.set_active(state.gta_fix)
        extra_group.add(self.gta_fix_row)

        self.flatpak_row = Adw.SwitchRow(title="Flatpak")
        self.flatpak_row.set_active(state.flatpak)
        extra_group.add(self.flatpak_row)

        self.virt_row = Adw.SwitchRow(
            title=tr("Virtualization (libvirt, virt-manager)")
        )
        self.virt_row.set_active(state.virtualization)
        extra_group.add(self.virt_row)

        self.autoupdate_row = Adw.SwitchRow(
            title=tr("Automatic updates")
        )
        self.autoupdate_row.set_active(state.autoupdate)
        extra_group.add(self.autoupdate_row)

        self.autoupdate_interval_row = Adw.EntryRow(
            title=tr("Interval (e.g. 1h, 6h, 24h)")
        )
        self.autoupdate_interval_row.set_text(state.autoupdate_interval)
        extra_group.add(self.autoupdate_interval_row)

        self.branch_row = self._combo(
            tr("Branch (install + updates)"),
            _branches(), state.branch,
        )
        extra_group.add(self.branch_row)

        self.bootloader_row = self._combo(
            tr("Bootloader"), _bootloaders(), state.bootloader
        )
        extra_group.add(self.bootloader_row)

        self.plymouth_row = self._combo(
            tr("Boot splash"), _plymouth_themes(), state.plymouth_theme
        )
        extra_group.add(self.plymouth_row)

        # Limine stretches its wallpaper to the screen: the format must match
        # the MAIN screen = the connected one with the highest resolution.
        # Detection only pre-selects an entry, the user can always change it.
        screen_res, aspect_detected = detect_main_screen()
        if aspect_detected:
            state.boot_aspect = aspect_detected
        self.boot_aspect_row = self._combo(
            tr("Boot wallpaper format (Limine)"),
            _mark_detected(_boot_aspects(), aspect_detected),
            state.boot_aspect,
        )
        self.boot_aspect_row.set_subtitle(
            tr("Main screen detected: {res}").format(res=screen_res) if screen_res
            else tr("Pick the one closest to your main screen (the biggest one)")
        )
        extra_group.add(self.boot_aspect_row)

        # With several screens of different sizes Limine can pick the smaller one
        # (menu and wallpaper then use that resolution): recommend the main
        # screen's. With a single screen "auto" is fine, so that stays the default.
        screen_count = detect_screen_count()
        if screen_res and screen_count >= 2:
            state.boot_resolution = screen_res
        self.boot_resolution_row = self._combo(
            tr("Limine menu resolution"),
            _boot_resolutions(screen_res), state.boot_resolution,
        )
        self.boot_resolution_row.set_subtitle(
            tr("{count} screens detected: Limine can use the smaller one — pick your main "
               "screen's resolution.").format(count=screen_count) if screen_count >= 2
            else tr("Only useful with several screens of different sizes.")
        )
        extra_group.add(self.boot_resolution_row)

        # Secure Boot (Limine and systemd-boot) + EAC Linux v2 boot entry
        # (Limine only) — experimental, off by default. See docs/secure-boot-eac.md.
        self.secure_boot_row = Adw.SwitchRow(title=tr("Secure Boot (sign the bootloader)"))
        self.secure_boot_row.set_subtitle(
            tr("Keys are created during the install; enrolling them in the firmware is "
               "done afterwards (docs/secure-boot-eac.md).")
        )
        self.secure_boot_row.set_active(state.secure_boot)
        extra_group.add(self.secure_boot_row)

        self.eac_row = Adw.SwitchRow(title=tr("EAC Linux v2 boot entry (experimental)"))
        self.eac_row.set_subtitle(
            tr("Separate “NixOS EAC” entry on a Fedora/Bazzite-signed kernel. Needs Secure Boot "
               "and a TPM 2.0; Epic has not confirmed it accepts this yet.")
        )
        self.eac_row.set_active(state.eac_enable)
        extra_group.add(self.eac_row)

        self.eac_vendor_row = self._combo(
            tr("EAC kernel"), _eac_vendors(), state.eac_vendor
        )
        extra_group.add(self.eac_vendor_row)

        # Other systems found in the firmware boot menu (EFI NVRAM), offered to Limine.
        # Same detection as the terminal wizard (multiboot.py); nothing is shown when
        # there is nothing to offer (BIOS boot, no efibootmgr, only Roudix installed).
        self.other_os_header_row = Adw.ActionRow(
            title=tr("Other systems"),
            subtitle=tr("Found in the EFI NVRAM: switch on the ones to add to Limine's boot menu."),
        )
        extra_group.add(self.other_os_header_row)
        self.other_os_rows = []   # [(multiboot.BootEntry, Adw.SwitchRow)]
        chosen = {tuple(e) for e in state.other_os}
        for entry in ([] if is_bios_boot() else multiboot.detect()):
            row = Adw.SwitchRow(title=entry.label, subtitle=f"{entry.efi_path} — {entry.partuuid}")
            row.set_active(tuple(entry) in chosen)
            extra_group.add(row)
            self.other_os_rows.append((entry, row))

        self.matrix_row = self._combo(
            tr("Matrix client"), _matrix(), state.matrix_client
        )
        extra_group.add(self.matrix_row)

        self.discord_row = self._combo(
            tr("Discord"), _discord(), state.discord
        )
        extra_group.add(self.discord_row)

        self.telegram_row = self._combo(
            "Telegram", _telegram(), state.telegram
        )
        extra_group.add(self.telegram_row)

        self.video_player_row = self._combo(
            tr("Video player"), _video_player(), state.video_player
        )
        extra_group.add(self.video_player_row)

        self.torrent_client_row = self._combo(
            tr("Torrent client"), _torrent_client(), state.torrent_client
        )
        extra_group.add(self.torrent_client_row)

        self.music_player_row = self._combo(
            tr("Music player"), _music_player(), state.music_player
        )
        extra_group.add(self.music_player_row)

        self.mail_client_row = self._combo(
            tr("Mail client"), _mail_client(), state.mail_client
        )
        extra_group.add(self.mail_client_row)

        self.password_manager_row = self._combo(
            tr("Password manager"), _password_manager(), state.password_manager
        )
        extra_group.add(self.password_manager_row)

        self.office_row = self._combo(tr("Office suite"), _office(), state.office)
        extra_group.add(self.office_row)

        self.office_dictionaries_row = Adw.EntryRow(
            title=tr("Office dictionaries (comma-separated: en, fr, es, de, it, pt)")
        )
        self.office_dictionaries_row.set_text(", ".join(state.office_dictionaries))
        extra_group.add(self.office_dictionaries_row)

        self.printing_enable_row = Adw.SwitchRow(title=tr("Printing (CUPS)"))
        self.printing_enable_row.set_subtitle(
            tr("Common printer drivers and network printer discovery.")
        )
        self.printing_enable_row.set_active(state.printing_enable)
        extra_group.add(self.printing_enable_row)

        self.printing_scanners_row = Adw.SwitchRow(title=tr("Scanners (SANE)"))
        self.printing_scanners_row.set_active(state.printing_scanners)
        extra_group.add(self.printing_scanners_row)

        self.vpn_openvpn_row = Adw.SwitchRow(title=tr("OpenVPN (NetworkManager plugin)"))
        self.vpn_openvpn_row.set_active(state.vpn_openvpn)
        extra_group.add(self.vpn_openvpn_row)

        self.waydroid_row = Adw.SwitchRow(title="Waydroid (Android)")
        self.waydroid_row.set_active(state.waydroid_enable)
        extra_group.add(self.waydroid_row)
        box.append(extra_group)
        self._sync_autoupdate_row()
        self._sync_laptop_row()

        # ── Apps ──
        apps_group = Adw.PreferencesGroup(
            title="Apps",
            description=tr("Turn on the ones you want preinstalled."),
        )
        self.app_gimp_row = Adw.SwitchRow(title="GIMP")
        self.app_gimp_row.set_active(state.app_gimp)
        apps_group.add(self.app_gimp_row)

        self.app_inkscape_row = Adw.SwitchRow(title="Inkscape")
        self.app_inkscape_row.set_active(state.app_inkscape)
        apps_group.add(self.app_inkscape_row)

        self.spicetify_theme_row = self._combo(
            tr("Spicetify theme"), _spicetify_themes(), state.spicetify_theme
        )
        apps_group.add(self.spicetify_theme_row)

        self.spicetify_color_scheme_row = Adw.EntryRow(
            title=tr("Spicetify color scheme (empty = theme default)")
        )
        self.spicetify_color_scheme_row.set_text(state.spicetify_color_scheme)
        apps_group.add(self.spicetify_color_scheme_row)

        self.spicetify_adblock_row = Adw.SwitchRow(
            title=tr("Adblock extension (Spicetify)")
        )
        self.spicetify_adblock_row.set_active(state.spicetify_adblock)
        apps_group.add(self.spicetify_adblock_row)

        self.spicetify_hide_podcasts_row = Adw.SwitchRow(
            title=tr("Hide podcasts (Spicetify)")
        )
        self.spicetify_hide_podcasts_row.set_active(state.spicetify_hide_podcasts)
        apps_group.add(self.spicetify_hide_podcasts_row)

        self.spicetify_marketplace_row = Adw.SwitchRow(title="Spicetify Marketplace")
        self.spicetify_marketplace_row.set_active(state.spicetify_marketplace)
        apps_group.add(self.spicetify_marketplace_row)

        self.app_songrec_row = Adw.SwitchRow(title="SongRec")
        self.app_songrec_row.set_active(state.app_songrec)
        apps_group.add(self.app_songrec_row)

        self.app_easyeffects_row = Adw.SwitchRow(title="EasyEffects (+ rnnoise)")
        self.app_easyeffects_row.set_active(state.app_easyeffects)
        apps_group.add(self.app_easyeffects_row)

        self.app_signal_row = Adw.SwitchRow(
            title="Signal",
            subtitle=tr("End-to-end encrypted messenger"),
        )
        self.app_signal_row.set_active(state.app_signal)
        apps_group.add(self.app_signal_row)

        self.app_zapzap_row = Adw.SwitchRow(
            title="ZapZap",
            subtitle=tr("Unofficial WhatsApp client"),
        )
        self.app_zapzap_row.set_active(state.app_zapzap)
        apps_group.add(self.app_zapzap_row)

        self.app_fluxer_row = Adw.SwitchRow(
            title="Fluxer",
            subtitle=tr("Self-hostable Discord alternative (independent of the Discord choice above)"),
        )
        self.app_fluxer_row.set_active(state.app_fluxer)
        apps_group.add(self.app_fluxer_row)

        self.app_fluxer_channel_row = self._combo(
            tr("Fluxer channel"), _fluxer_channel(), state.app_fluxer_channel
        )
        apps_group.add(self.app_fluxer_channel_row)
        self.app_fluxer_channel_row.set_sensitive(state.app_fluxer)
        self.app_fluxer_row.connect(
            "notify::active",
            lambda *_: self.app_fluxer_channel_row.set_sensitive(self.app_fluxer_row.get_active()),
        )

        self.app_cressida_row = Adw.SwitchRow(
            title="Cressida",
            subtitle=tr("Native Wayland Discord client (unofficial, early development)"),
        )
        self.app_cressida_row.set_active(state.app_cressida)
        apps_group.add(self.app_cressida_row)

        box.append(apps_group)
        self._sync_spicetify_rows()

        # ── Content Creation ──
        cc_group = Adw.PreferencesGroup(title=tr("Content Creation"))
        self.content_creation_row = Adw.SwitchRow(
            title=tr("Enable content-creation tooling")
        )
        self.content_creation_row.set_active(state.content_creation_enable)
        cc_group.add(self.content_creation_row)

        self.obs_row = Adw.SwitchRow(title="OBS Studio")
        self.obs_row.set_active(state.obs_enable)
        cc_group.add(self.obs_row)

        # One switch per OBS plugin (like the gaming apps) — Aitum
        # Multistream replaces obs-multi-rtmp as the multistreaming
        # option (actively maintained successor from the Aitum team,
        # independent encoders/bitrate per platform).
        self.obs_plugin_rows = {}
        for attr, title, default in (
            ("vkcapture", tr_noop("VKCapture (Vulkan/OpenGL game capture)"), state.obs_plugin_vkcapture),
            ("pipewire_audio", tr_noop("Pipewire Audio Capture (per-app audio)"), state.obs_plugin_pipewire_audio_capture),
            ("background_removal", tr_noop("Background Removal (AI virtual background)"), state.obs_plugin_background_removal),
            ("move_transition", tr_noop("Move Transition (source animations)"), state.obs_plugin_move_transition),
            ("aitum_multistream", tr_noop("Aitum Multistream (multi-platform streaming)"), state.obs_plugin_aitum_multistream),
            ("gstreamer", tr_noop("GStreamer (extra sources/outputs)"), state.obs_plugin_gstreamer),
            ("composite_blur", tr_noop("Composite Blur (blur/glass filters)"), state.obs_plugin_composite_blur),
            ("advanced_scene_switcher", tr_noop("Advanced Scene Switcher (automated scene switching)"), state.obs_plugin_advanced_scene_switcher),
            ("input_overlay", tr_noop("Input Overlay (on-screen keyboard/mouse/gamepad)"), state.obs_plugin_input_overlay),
            ("waveform", tr_noop("Waveform (audio waveform/spectrum)"), state.obs_plugin_waveform),
        ):
            row = Adw.SwitchRow(title=tr(title))
            row.set_active(default)
            cc_group.add(row)
            self.obs_plugin_rows[attr] = row

        self.video_editor_row = self._combo(
            tr("Video editor"),
            _video_editors(),
            state.video_editor,
        )
        cc_group.add(self.video_editor_row)

        self.virtual_camera_row = Adw.SwitchRow(
            title=tr("Virtual camera (v4l2loopback)")
        )
        self.virtual_camera_row.set_active(state.virtual_camera_enable)
        cc_group.add(self.virtual_camera_row)

        self.chatterino_row = Adw.SwitchRow(
            title=tr("Chatterino2 (third-party Twitch chat)")
        )
        self.chatterino_row.set_active(state.chatterino_enable)
        cc_group.add(self.chatterino_row)
        box.append(cc_group)
        self._sync_content_creation_rows()

        # Connected here (not right after each row's creation above) because
        # ComboRow/SwitchRow can fire their notify signal synchronously while
        # still being constructed — connecting early meant these handlers could
        # run before the widgets they toggle existed yet, throwing a silently-
        # swallowed AttributeError instead of actually syncing visibility.
        self.bootloader_row.connect("notify::selected", lambda *_: self._sync_boot_aspect_row())
        self._sync_boot_aspect_row()
        self.bootloader_row.connect("notify::selected", lambda *_: self._sync_boot_resolution_row())
        self._sync_boot_resolution_row()
        self.bootloader_row.connect("notify::selected", lambda *_: self._sync_boot_security_rows())
        self.eac_row.connect("notify::active", lambda *_: self._sync_boot_security_rows())
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_boot_security_rows())
        self._sync_boot_security_rows()
        self.bootloader_row.connect("notify::selected", lambda *_: self._sync_other_os_rows())
        self._sync_other_os_rows()
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_nvidia_row())
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_undervolt_row())
        self.gpu_row.connect("notify::selected", lambda *_: self._sync_kernel_row())
        self.nvidia_kernel_source_row.connect("notify::selected", lambda *_: self._sync_kernel_row())
        self.laptop_row.connect("notify::active", lambda *_: self._sync_laptop_row())
        self.laptop_backend_row.connect("notify::selected", lambda *_: self._sync_laptop_row())
        self.gaming_row.connect("notify::active", lambda *_: self._sync_laptop_row())
        self.browser_row.connect("notify::selected", lambda *_: self._sync_brave_row())
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_shell_row())
        self.desktop_row.connect("notify::selected", lambda *_: self._sync_latest_rows())
        self.shell_row.connect("notify::selected", lambda *_: self._sync_latest_rows())
        self.rgb_row.connect("notify::selected", lambda *_: self._sync_memory_rows())
        self.memory_rgb_row.connect("notify::active", lambda *_: self._sync_memory_rows())
        self.zen_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.zen_sine_row.connect("notify::active", lambda *_: self._sync_zen_rows())
        self.music_player_row.connect("notify::selected", lambda *_: self._sync_spicetify_rows())
        self.content_creation_row.connect(
            "notify::active", lambda *_: self._sync_content_creation_rows()
        )
        self.gaming_row.connect("notify::active", lambda *_: self._sync_ananicy_row())
        self.autoupdate_row.connect(
            "notify::active", lambda *_: self._sync_autoupdate_row()
        )

        self._init_host_filter({
            "hw_group": hw_group, "browser_group": browser_group,
            "desktop_group": desktop_group, "sys_group": sys_group,
            "rgb_group": rgb_group, "extra_group": extra_group,
            "apps_group": apps_group, "cc_group": cc_group,
        })

        next_btn = Gtk.Button(
            label=tr("Continue"),
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.END,
            margin_top=12,
        )
        next_btn.connect("clicked", self._validate)
        box.append(next_btn)

        self.set_child(page_with_header(tr("Options"), scroller))


    # ── per-host question filter (see host_profile.py) ───────────────────
    # row attribute -> nix option(s) it sets. A row is shown when any of
    # its options is listed in the host's local.nix.example.
    HOST_ROW_KEYS = {
        "gpu_row": ["hardware.myGpu"], "nvidia_laptop_row": ["hardware.nvidiaLaptop"],
        "laptop_row": ["roudix.laptop.enable"], "thinkpad_row": ["roudix.laptop.thinkpad"],
        "laptop_backend_row": ["roudix.laptop.backend"],
        "laptop_gaming_note": ["roudix.gaming.enable"],
        "undervolt_row": ["roudix.undervolt.only-amd.enable"], "cpu_row": ["hardware.myCpu"],
        "kernel_row": ["hardware.myKernel", "hardware.myKernelChaotic"],
        "nvidia_kernel_source_row": ["hardware.nvidiaKernelSource"],
        "nvidia_driver_source_row": ["hardware.nvidiaDriverSource"],
        "nvidia_beta_row": ["hardware.nvidiaBeta"], "nvidia_open_row": ["hardware.nvidiaOpen"],
        "browser_row": ["roudix.browsers"], "brave_variant_row": ["roudix.browsers"],
        "zen_row": ["roudix.zen.enable"], "zen_variant_row": ["roudix.zen.variant"],
        "zen_mods_row": ["roudix.zen.mods"], "zen_sine_row": ["roudix.zen.sine.enable"],
        "zen_sine_mods_row": ["roudix.zen.sine.mods"],
        "desktop_row": ["roudix.desktop.type"], "shell_row": ["roudix.desktop.shell"],
        "latest_de_row": [],
        "latest_shell_row": ["roudix.desktop.latest.noctalia", "roudix.desktop.latest.dms", "roudix.desktop.latest.caelestia"],
        "latest_note": ["roudix.desktop.latest.noctalia", "roudix.desktop.latest.dms", "roudix.desktop.latest.caelestia"],
        "default_shell_row": ["roudix.shell"], "terminal_row": ["roudix.terminal"],
        "file_manager_row": ["roudix.fileManager"], "editor_row": ["roudix.editor"],
        "desktop_integration_row": ["roudix.desktopIntegration"],
        "vm_guest_row": ["roudix.vmGuest.enable"], "gaming_row": ["roudix.gaming.enable"],
        "ananicy_row": ["roudix.gaming.ananicy.enable"],
        "millennium_row": ["roudix.gaming.steam.millennium.enable"],
        "mesa_git_row": ["roudix.mesa.useGit"], "mesa_git_source_row": ["roudix.mesa.gitSource"],
        "timezone_row": ["time.timeZone"],
        "locale_row": ["i18n.defaultLocale"], "keymap_row": ["console.keyMap"],
        "gfx_keyboard_row": ["roudix.keyboardLayout"],
        "rgb_row": ["roudix.rgb"], "rgb_note": ["roudix.rgb"],
        "memory_rgb_row": ["roudix.memory.enable"], "memory_type_row": ["roudix.memory.type"],
        "memory_smbus_row": ["roudix.memory.smBus"], "memory_sku_row": ["roudix.memory.sku"],
        "gta_fix_row": ["roudix.hosts.gtaFix.enable"], "flatpak_row": ["roudix.flatpak.enable"],
        "virt_row": ["roudix.virtualization.enable"], "autoupdate_row": ["roudix.autoupdate.enable"],
        "autoupdate_interval_row": ["roudix.autoupdate.interval"],
        "branch_row": ["roudix.autoupdate.branch"], "bootloader_row": ["roudix.boot.bootloader"],
        "boot_aspect_row": ["roudix.boot.wallpaperAspect"],
        "boot_resolution_row": ["roudix.boot.menuResolution"],
        "secure_boot_row": ["roudix.boot.secureBoot.enable"],
        "eac_row": ["roudix.boot.eac.enable"], "eac_vendor_row": ["roudix.boot.eac.vendor"],
        "matrix_row": ["roudix.matrixClient"], "discord_row": ["roudix.discord"],
        "telegram_row": ["roudix.telegram"], "video_player_row": ["roudix.videoPlayer"],
        "torrent_client_row": ["roudix.torrentClient"], "music_player_row": ["roudix.musicPlayer"],
        "mail_client_row": ["roudix.mailClient"], "password_manager_row": ["roudix.passwordManager"],
        "office_row": ["roudix.office"], "office_dictionaries_row": ["roudix.officeDictionaries"],
        "printing_enable_row": ["roudix.printing.enable"],
        "plymouth_row": ["roudix.boot.plymouth.theme"],
        "printing_scanners_row": ["roudix.printing.scanners.enable"],
        "vpn_openvpn_row": ["roudix.vpn.openvpn.enable"],
        "waydroid_row": ["roudix.waydroid.enable"],
        "app_gimp_row": ["roudix.apps.gimp.enable"], "app_inkscape_row": ["roudix.apps.inkscape.enable"],
        "app_songrec_row": ["roudix.apps.songrec.enable"], "app_easyeffects_row": ["roudix.apps.easyeffects.enable"],
        "app_signal_row": ["roudix.apps.signal.enable"], "app_zapzap_row": ["roudix.apps.zapzap.enable"],
        "app_fluxer_row": ["roudix.apps.fluxer.enable"],
        "app_fluxer_channel_row": ["roudix.apps.fluxer.channel"],
        "app_cressida_row": ["roudix.apps.cressida.enable"],
        "spicetify_theme_row": ["roudix.spicetify.theme"],
        "spicetify_color_scheme_row": ["roudix.spicetify.colorScheme"],
        "spicetify_adblock_row": ["roudix.spicetify.extensions.adblock.enable"],
        "spicetify_hide_podcasts_row": ["roudix.spicetify.extensions.hidePodcasts.enable"],
        "spicetify_marketplace_row": ["roudix.spicetify.marketplace.enable"],
        "content_creation_row": ["roudix.contentCreation.enable"], "obs_row": ["roudix.contentCreation.obs.enable"],
        "video_editor_row": ["roudix.contentCreation.videoEditor"],
        "virtual_camera_row": ["roudix.contentCreation.virtualCamera.enable"],
        "chatterino_row": ["roudix.contentCreation.streaming.chatterino.enable"],
    }
    # group -> rows it contains (a group with no visible row is hidden too)
    HOST_GROUP_ROWS = {
        "hw_group": ["gpu_row", "nvidia_laptop_row", "laptop_row", "laptop_backend_row", "thinkpad_row", "undervolt_row", "cpu_row", "kernel_row", "nvidia_kernel_source_row", "nvidia_driver_source_row", "nvidia_open_row", "nvidia_beta_row"],
        "browser_group": ["browser_row", "brave_variant_row", "zen_row", "zen_variant_row", "zen_mods_row", "zen_sine_row", "zen_sine_mods_row"],
        "desktop_group": ["desktop_row", "shell_row", "latest_de_row", "latest_shell_row", "latest_note", "default_shell_row", "terminal_row", "file_manager_row", "editor_row", "desktop_integration_row"],
        "sys_group": ["vm_guest_row", "gaming_row", "ananicy_row", "millennium_row", "mesa_git_row", "mesa_git_source_row", "timezone_row", "locale_row", "keymap_row", "gfx_keyboard_row"],
        "rgb_group": ["rgb_row", "memory_rgb_row", "memory_type_row", "memory_smbus_row", "memory_sku_row"],
        "extra_group": ["gta_fix_row", "flatpak_row", "virt_row", "autoupdate_row", "autoupdate_interval_row", "branch_row", "bootloader_row", "plymouth_row", "boot_aspect_row", "boot_resolution_row", "secure_boot_row", "eac_row", "eac_vendor_row", "matrix_row", "discord_row", "telegram_row", "video_player_row", "torrent_client_row", "music_player_row", "mail_client_row", "password_manager_row", "office_row", "office_dictionaries_row", "printing_enable_row", "printing_scanners_row", "vpn_openvpn_row", "waydroid_row"],
        "apps_group": ["app_gimp_row", "app_inkscape_row", "spicetify_theme_row", "spicetify_color_scheme_row", "spicetify_adblock_row", "spicetify_hide_podcasts_row", "spicetify_marketplace_row", "app_songrec_row", "app_easyeffects_row", "app_signal_row", "app_zapzap_row", "app_fluxer_row", "app_fluxer_channel_row", "app_cressida_row"],
        "cc_group": ["content_creation_row", "obs_row", "video_editor_row", "virtual_camera_row", "chatterino_row"],
    }

    @staticmethod
    def _seed_allowed():
        return seed_allowed()  # choices.py: shared with the TUI

    @staticmethod
    def _make_hideable(widget):
        """The _sync_* methods keep calling widget.set_visible(...) to show or
        hide rows depending on other answers; wrap it so a row hidden by the
        host profile stays hidden whatever they ask for."""
        if getattr(widget, "_host_hideable", False):
            return
        original = widget.set_visible
        widget._host_hidden = False
        widget._host_original_set_visible = original
        widget._host_hideable = True
        widget.set_visible = lambda visible, _w=widget, _o=original: _o(False if _w._host_hidden else visible)

    def _init_host_filter(self, groups):
        self._host_groups = groups
        self._host_widgets = []          # (widget, [option keys])
        for attr, keys in self.HOST_ROW_KEYS.items():
            w = getattr(self, attr, None)
            if w is not None:
                self._make_hideable(w)
                self._host_widgets.append((w, keys))
        # rows built in loops
        for attr, row in getattr(self, "gaming_apps_rows", {}).items():
            self._make_hideable(row)
            self._host_widgets.append((row, [f"roudix.gaming.apps.{attr}.enable"]))
        for row in getattr(self, "obs_plugin_rows", {}).values():
            self._make_hideable(row)
            self._host_widgets.append((row, ["roudix.contentCreation.obs.enable"]))
        # other systems for Limine: a profile that hides the bootloader question hides them too
        for row in [self.other_os_header_row] + [r for _e, r in self.other_os_rows]:
            self._make_hideable(row)
            self._host_widgets.append((row, ["roudix.boot.bootloader"]))
        self._on_hostname_changed()

    def _on_hostname_changed(self):
        # The host (hosts/<name>/, also networking.hostName) is chosen on the
        # Welcome page, before this page is built.
        listed = host_profile.listed_options(self.state.hostname or "roudix")
        for widget, keys in self._host_widgets:
            hidden = listed is not None and not any(k in listed for k in keys)
            widget._host_hidden = hidden
            widget._host_original_set_visible(not hidden)
        # let the existing sync methods recompute the dynamic rows
        for name in ("_sync_nvidia_row", "_sync_undervolt_row", "_sync_laptop_row", "_sync_kernel_row", "_sync_mesa_row",
                     "_sync_brave_row", "_sync_shell_row", "_sync_latest_rows", "_sync_desktop_integration_row",
                     "_sync_file_manager_row", "_sync_memory_rows", "_sync_zen_rows",
                     "_sync_spicetify_rows", "_sync_ananicy_row", "_sync_content_creation_rows",
                     "_sync_autoupdate_row", "_sync_boot_aspect_row", "_sync_boot_resolution_row",
                     "_sync_boot_security_rows", "_sync_other_os_rows"):
            try:
                getattr(self, name)()
            except Exception:
                pass
        for gname, group in self._host_groups.items():
            rows = [getattr(self, r, None) for r in self.HOST_GROUP_ROWS[gname]]
            group.set_visible(any(r is not None and not getattr(r, "_host_hidden", False) for r in rows))

    # ── helpers ──────────────────────────────────────────────────────────

    def _combo(self, title, pairs, current_value):
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        row = Adw.ComboRow(title=title, model=Gtk.StringList.new(labels))
        row.set_selected(values.index(current_value) if current_value in values else 0)
        self._rows[id(row)] = values
        return row

    def _selected_value(self, row):
        return self._rows[id(row)][row.get_selected()]

    def _set_combo_value(self, row, value):
        values = self._rows[id(row)]
        if value in values:
            row.set_selected(values.index(value))

    @staticmethod
    def _split_list(text):
        return [part.strip() for part in text.split(",") if part.strip()]

    def _sync_boot_resolution_row(self):
        # Only Limine has a menu to size, and only if we could read a screen.
        self.boot_resolution_row.set_visible(
            self._selected_value(self.bootloader_row) == "limine"
            and len(self._rows[id(self.boot_resolution_row)]) > 1
        )

    def _sync_boot_security_rows(self):
        # Secure Boot signing works with Limine and systemd-boot; the EAC entry is
        # Limine-only, and the EAC kernel choice only matters once it is on. All of
        # it is UEFI-only: hidden when the ISO was booted in legacy BIOS mode.
        bios = is_bios_boot()
        limine = self._selected_value(self.bootloader_row) == "limine"
        self.secure_boot_row.set_visible(not bios)
        self.eac_row.set_visible(limine and not bios)
        self.eac_vendor_row.set_visible(limine and not bios and self.eac_row.get_active())
        # Fedora ships no signed NVIDIA modules: on NVIDIA only Bazzite's kernel works.
        nvidia = self._selected_value(self.gpu_row) == "nvidia"
        if nvidia:
            self._set_combo_value(self.eac_vendor_row, "bazzite")
        self.eac_vendor_row.set_sensitive(not nvidia)
        self.eac_vendor_row.set_subtitle(
            tr("NVIDIA GPU: only Bazzite ships signed NVIDIA modules") if nvidia else ""
        )

    def _sync_other_os_rows(self):
        """Only Limine on UEFI chainloads other systems (modules/system/boot, boot.local.nix)."""
        show = (self._selected_value(self.bootloader_row) == "limine" and not is_bios_boot()
                and bool(self.other_os_rows))
        self.other_os_header_row.set_visible(show)
        for _entry, row in self.other_os_rows:
            row.set_visible(show)

    def _sync_boot_aspect_row(self):
        # Only Limine shows a wallpaper (systemd-boot has none).
        self.boot_aspect_row.set_visible(
            self._selected_value(self.bootloader_row) == "limine"
        )

    def _sync_nvidia_row(self):
        is_nvidia = self._selected_value(self.gpu_row) == "nvidia"
        self.nvidia_laptop_row.set_visible(is_nvidia)
        for row in (self.nvidia_kernel_source_row, self.nvidia_driver_source_row,
                    self.nvidia_open_row, self.nvidia_beta_row):
            row.set_visible(is_nvidia)

    def _sync_mesa_row(self):
        self.mesa_git_source_row.set_visible(self.mesa_git_row.get_active())

    def _sync_undervolt_row(self):
        self.undervolt_row.set_visible(
            self._selected_value(self.gpu_row) in ("amd", "amd-legacy")
        )

    def _sync_laptop_row(self):
        self.thinkpad_row.set_visible(self.laptop_row.get_active())
        self.laptop_backend_row.set_visible(self.laptop_row.get_active())
        self.laptop_gaming_note.set_visible(
            self.laptop_row.get_active() and self.gaming_row.get_active()
            and self._selected_value(self.laptop_backend_row) == "tlp"
        )

    def _sync_kernel_row(self):
        is_nvidia = self._selected_value(self.gpu_row) == "nvidia"
        # Chaotic-Nyx list on nvidia unless the user opted into xddxdd's
        use_chaotic = is_nvidia and (
            self._selected_value(self.nvidia_kernel_source_row) == "chaotic"
        )
        pairs = _kernels_chaotic() if use_chaotic else _kernels()
        current = self.state.kernel_chaotic if use_chaotic else self.state.kernel
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        self.kernel_row.set_title(
            tr("Kernel (Chaotic-Nyx)")
            if use_chaotic
            else tr("Kernel (xddxdd)")
        )
        self.kernel_row.set_model(Gtk.StringList.new(labels))
        self.kernel_row.set_selected(values.index(current) if current in values else 0)
        self._rows[id(self.kernel_row)] = values

    def _sync_brave_row(self):
        self.brave_variant_row.set_visible(
            self._selected_value(self.browser_row) == "brave"
        )

    def _sync_shell_row(self):
        desktop = self._selected_value(self.desktop_row)
        self.shell_row.set_visible(desktop in ("niri", "hyprland", "mangowc", "umbriel"))

        pairs = _shells(desktop)
        values = [v for v, _ in pairs]
        labels = [l for _, l in pairs]
        # Keep whatever the user already had selected if it's still a valid
        # choice for this compositor (e.g. switching mangowc → niri keeps
        # "dms"); otherwise fall back to noctalia rather than leaving a
        # now-invalid selection (e.g. "caelestia" surviving a switch away
        # from hyprland, or anything but noctalia surviving a switch to
        # umbriel).
        try:
            current = self._selected_value(self.shell_row)
        except (KeyError, IndexError):
            current = self.state.desktop_shell
        self.shell_row.set_model(Gtk.StringList.new(labels))
        self.shell_row.set_selected(values.index(current) if current in values else 0)
        self._rows[id(self.shell_row)] = values

    def _sync_latest_rows(self):
        """Show the nixpkgs/latest switch of the selected compositor and of
        the selected shell, and only those (Hyprland has no flake version)."""
        desktop = self._selected_value(self.desktop_row)
        has_shell = desktop in ("niri", "hyprland", "mangowc", "umbriel")
        try:
            shell = self._selected_value(self.shell_row) if has_shell else None
        except (KeyError, IndexError):
            # shell_row's model is being rebuilt by _sync_shell_row: the
            # final call (after it finishes) will see a consistent state.
            shell = None

        de_visible = desktop in LATEST_DESKTOPS
        shell_visible = shell in LATEST_SHELLS
        self.latest_de_row.set_visible(de_visible)
        self.latest_shell_row.set_visible(shell_visible)
        if de_visible:
            self.latest_de_row.set_title(_latest_title(LATEST_DESKTOPS[desktop]))
            self.latest_de_row.set_active(getattr(self.state, f"latest_{desktop}", False))
        if shell_visible:
            self.latest_shell_row.set_title(_latest_title(LATEST_SHELLS[shell]))
            self.latest_shell_row.set_active(getattr(self.state, f"latest_{shell}", False))
        self.latest_note.set_visible(de_visible or shell_visible)

    def _sync_desktop_integration_row(self):
        # GNOME/KDE manage their own keyring/portal stack — this option
        # only matters for the "bare" compositors.
        desktop = self._selected_value(self.desktop_row)
        self.desktop_integration_row.set_visible(
            desktop in ("niri", "hyprland", "mangowc", "umbriel")
        )

    def _sync_file_manager_row(self):
        # GNOME/KDE have one obvious native file manager, so hide the
        # question entirely and lock the value to it — matches
        # the old bash installer, which doesn't even ask on those desktops.
        # niri/hyprland/mangowc/umbriel don't ship an opinionated file manager, so
        # show the row and leave whatever the user already picked
        # untouched when landing on one of those.
        desktop = self._selected_value(self.desktop_row)
        if desktop == "gnome":
            self._set_combo_value(self.file_manager_row, "nautilus")
            self.file_manager_row.set_visible(False)
        elif desktop == "kde":
            self._set_combo_value(self.file_manager_row, "dolphin")
            self.file_manager_row.set_visible(False)
        elif desktop == "cinnamon":
            self._set_combo_value(self.file_manager_row, "nemo")
            self.file_manager_row.set_visible(False)
        elif desktop == "cosmic":
            # COSMIC Files ships with the desktop; Roudix has no choice to make.
            self.file_manager_row.set_visible(False)
        else:
            self.file_manager_row.set_visible(True)

    def _sync_memory_rows(self):
        is_openlinkhub = self._selected_value(self.rgb_row) == "openlinkhub"
        self.memory_rgb_row.set_visible(is_openlinkhub)
        memory_rgb_active = is_openlinkhub and self.memory_rgb_row.get_active()
        self.memory_type_row.set_visible(memory_rgb_active)
        self.memory_smbus_row.set_visible(memory_rgb_active)
        self.memory_sku_row.set_visible(memory_rgb_active)

    def _sync_zen_rows(self):
        zen_active = self.zen_row.get_active()
        self.zen_variant_row.set_visible(zen_active)
        self.zen_mods_row.set_visible(zen_active)
        self.zen_sine_row.set_visible(zen_active)
        self.zen_sine_mods_row.set_visible(zen_active and self.zen_sine_row.get_active())

    def _sync_spicetify_rows(self):
        spotify_active = self._selected_value(self.music_player_row) == "spotify"
        for row in (
            self.spicetify_theme_row,
            self.spicetify_color_scheme_row,
            self.spicetify_adblock_row,
            self.spicetify_hide_podcasts_row,
            self.spicetify_marketplace_row,
        ):
            row.set_visible(spotify_active)

    def _sync_ananicy_row(self):
        self.ananicy_row.set_visible(self.gaming_row.get_active())
        self.millennium_row.set_visible(self.gaming_row.get_active())
        for row in self.gaming_apps_rows.values():
            row.set_visible(self.gaming_row.get_active())

    def _sync_content_creation_rows(self):
        active = self.content_creation_row.get_active()
        for row in (
            self.obs_row,
            self.video_editor_row,
            self.virtual_camera_row,
            self.chatterino_row,
        ):
            row.set_visible(active)
        for row in self.obs_plugin_rows.values():
            row.set_visible(active)

    def _sync_autoupdate_row(self):
        self.autoupdate_interval_row.set_visible(self.autoupdate_row.get_active())

    def _validate(self, _btn):
        password = self.password_row.get_text()
        confirm = self.password_confirm_row.get_text()
        if not valid_username(self.username_row.get_text()):
            self.password_warning.set_label(
                tr("Invalid username: use letters, digits, '_', '-' or '.', starting with a letter or '_' (max 32)."))
            self.password_warning.set_visible(True)
            return
        if self._existing:
            if not existing_nixos.user_exists(self.username_row.get_text()):
                self.password_warning.set_label(
                    tr("This user doesn't exist on this system — run the installer from the account you want to keep."))
                self.password_warning.set_visible(True)
                return
            password = confirm = ""  # nothing to set: the account keeps its password
        elif not password:
            self.password_warning.set_label(
                tr("Password can't be empty.")
            )
            self.password_warning.set_visible(True)
            return
        if not self._existing and password != confirm:
            self.password_warning.set_label(
                tr("Passwords don't match.")
            )
            self.password_warning.set_visible(True)
            return
        self.password_warning.set_visible(False)

        s = self.state
        s.username = self.username_row.get_text()
        s.password = password
        s.gpu = self._selected_value(self.gpu_row)
        s.nvidia_laptop = self.nvidia_laptop_row.get_active()
        s.laptop = self.laptop_row.get_active()
        s.laptop_thinkpad = self.thinkpad_row.get_active()
        s.laptop_backend = self._selected_value(self.laptop_backend_row)
        s.undervolt_enable = self.undervolt_row.get_active()
        s.cpu = self._selected_value(self.cpu_row)
        kernel_value = self._selected_value(self.kernel_row)
        s.nvidia_kernel_source = self._selected_value(self.nvidia_kernel_source_row)
        s.nvidia_driver_source = self._selected_value(self.nvidia_driver_source_row)
        s.nvidia_beta = self.nvidia_beta_row.get_active()
        s.nvidia_open = self.nvidia_open_row.get_active()
        if s.gpu == "nvidia" and s.nvidia_kernel_source == "chaotic":
            s.kernel_chaotic = kernel_value
        else:
            s.kernel = kernel_value

        browser = self._selected_value(self.browser_row)
        s.browser = (
            self._selected_value(self.brave_variant_row)
            if browser == "brave"
            else browser
        )
        s.zen_browser = self.zen_row.get_active()
        s.zen_variant = self._selected_value(self.zen_variant_row)
        s.zen_sine_enable = self.zen_sine_row.get_active()
        s.zen_mods = self._split_list(self.zen_mods_row.get_text())
        s.zen_sine_mods = self._split_list(self.zen_sine_mods_row.get_text())

        s.desktop = self._selected_value(self.desktop_row)
        s.desktop_shell = self._selected_value(self.shell_row)
        # nixpkgs (False) / latest-flake (True): only the compositor and the
        # shell actually chosen keep their switch; the others fall back to
        # the nixpkgs default so a stale answer is never written.
        for _name in ("niri", "mangowc", "umbriel", "noctalia", "dms", "caelestia"):
            setattr(s, f"latest_{_name}", False)
        if self.latest_de_row.get_visible() and s.desktop in LATEST_DESKTOPS:
            setattr(s, f"latest_{s.desktop}", self.latest_de_row.get_active())
        if self.latest_shell_row.get_visible() and s.desktop_shell in LATEST_SHELLS:
            setattr(s, f"latest_{s.desktop_shell}", self.latest_shell_row.get_active())
        s.default_shell = self._selected_value(self.default_shell_row)
        s.terminal = self._selected_value(self.terminal_row)
        s.file_manager = self._selected_value(self.file_manager_row)
        s.editor = self._selected_value(self.editor_row)
        s.desktop_integration = self._selected_value(self.desktop_integration_row)

        s.vm_guest = self.vm_guest_row.get_active()
        s.gaming = self.gaming_row.get_active()
        s.ananicy_enable = self.ananicy_row.get_active()
        s.gaming_steam_millennium = self.millennium_row.get_active()
        s.gaming_apps_lutris = self.gaming_apps_rows["lutris"].get_active()
        s.gaming_apps_heroic = self.gaming_apps_rows["heroic"].get_active()
        s.gaming_apps_faugus = self.gaming_apps_rows["faugus"].get_active()
        s.gaming_apps_prismlauncher = self.gaming_apps_rows["prismlauncher"].get_active()
        s.gaming_apps_modrinth = self.gaming_apps_rows["modrinth"].get_active()
        s.gaming_apps_vintagestory = self.gaming_apps_rows["vintagestory"].get_active()
        s.gaming_apps_mangohud = self.gaming_apps_rows["mangohud"].get_active()
        s.mesa_use_git = self.mesa_git_row.get_active()
        s.mesa_git_source = self._selected_value(self.mesa_git_source_row)
        s.timezone = self._selected_value(self.timezone_row)
        s.locale = self._selected_value(self.locale_row)
        s.keymap = self._selected_value(self.keymap_row)
        gfx_value = self._selected_value(self.gfx_keyboard_row)
        s.keyboard_layout, s.keyboard_variant = gfx_value.split(":", 1)

        s.rgb = self._selected_value(self.rgb_row)
        s.memory_rgb_enable = self.memory_rgb_row.get_active()
        s.memory_type = self._selected_value(self.memory_type_row)
        s.memory_smbus = self.memory_smbus_row.get_text()
        s.memory_sku = self.memory_sku_row.get_text()

        s.gta_fix = self.gta_fix_row.get_active()
        s.flatpak = self.flatpak_row.get_active()
        s.virtualization = self.virt_row.get_active()
        s.autoupdate = self.autoupdate_row.get_active()
        s.autoupdate_interval = self.autoupdate_interval_row.get_text()
        s.branch = self._selected_value(self.branch_row)
        s.bootloader = self._selected_value(self.bootloader_row)
        s.plymouth_theme = self._selected_value(self.plymouth_row)
        s.boot_aspect = self._selected_value(self.boot_aspect_row)
        s.boot_resolution = self._selected_value(self.boot_resolution_row)
        # Hidden (so never wanted) in legacy BIOS mode, whatever the host defaults say.
        s.secure_boot = self.secure_boot_row.get_active() and not is_bios_boot()
        s.eac_enable = self.eac_row.get_active() and not is_bios_boot()
        s.eac_vendor = self._selected_value(self.eac_vendor_row)
        # Only the entries actually on offer (Limine, UEFI, not hidden by the profile).
        s.other_os = [tuple(entry) for entry, row in self.other_os_rows
                      if row.get_active() and row.get_visible()]
        s.matrix_client = self._selected_value(self.matrix_row)
        s.discord = self._selected_value(self.discord_row)
        s.telegram = self._selected_value(self.telegram_row)
        s.video_player = self._selected_value(self.video_player_row)
        s.torrent_client = self._selected_value(self.torrent_client_row)
        s.music_player = self._selected_value(self.music_player_row)
        s.mail_client = self._selected_value(self.mail_client_row)
        s.password_manager = self._selected_value(self.password_manager_row)
        s.office = self._selected_value(self.office_row)
        s.office_dictionaries = self._split_list(self.office_dictionaries_row.get_text())
        s.printing_enable = self.printing_enable_row.get_active()
        s.printing_scanners = self.printing_scanners_row.get_active()
        s.vpn_openvpn = self.vpn_openvpn_row.get_active()
        s.waydroid_enable = self.waydroid_row.get_active()
        s.app_gimp = self.app_gimp_row.get_active()
        s.app_inkscape = self.app_inkscape_row.get_active()
        s.spicetify_theme = self._selected_value(self.spicetify_theme_row)
        s.spicetify_color_scheme = self.spicetify_color_scheme_row.get_text().strip()
        s.spicetify_adblock = self.spicetify_adblock_row.get_active()
        s.spicetify_hide_podcasts = self.spicetify_hide_podcasts_row.get_active()
        s.spicetify_marketplace = self.spicetify_marketplace_row.get_active()
        s.app_songrec = self.app_songrec_row.get_active()
        s.app_easyeffects = self.app_easyeffects_row.get_active()
        s.app_signal = self.app_signal_row.get_active()
        s.app_zapzap = self.app_zapzap_row.get_active()
        s.app_fluxer = self.app_fluxer_row.get_active()
        s.app_fluxer_channel = self._selected_value(self.app_fluxer_channel_row)
        s.app_cressida = self.app_cressida_row.get_active()

        s.content_creation_enable = self.content_creation_row.get_active()
        s.obs_enable = self.obs_row.get_active()
        s.obs_plugin_vkcapture = self.obs_plugin_rows["vkcapture"].get_active()
        s.obs_plugin_pipewire_audio_capture = self.obs_plugin_rows["pipewire_audio"].get_active()
        s.obs_plugin_background_removal = self.obs_plugin_rows["background_removal"].get_active()
        s.obs_plugin_move_transition = self.obs_plugin_rows["move_transition"].get_active()
        s.obs_plugin_aitum_multistream = self.obs_plugin_rows["aitum_multistream"].get_active()
        s.obs_plugin_gstreamer = self.obs_plugin_rows["gstreamer"].get_active()
        s.obs_plugin_composite_blur = self.obs_plugin_rows["composite_blur"].get_active()
        s.obs_plugin_advanced_scene_switcher = self.obs_plugin_rows["advanced_scene_switcher"].get_active()
        s.obs_plugin_input_overlay = self.obs_plugin_rows["input_overlay"].get_active()
        s.obs_plugin_waveform = self.obs_plugin_rows["waveform"].get_active()
        s.video_editor = self._selected_value(self.video_editor_row)
        s.virtual_camera_enable = self.virtual_camera_row.get_active()
        s.chatterino_enable = self.chatterino_row.get_active()

        self.on_next()

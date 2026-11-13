"""
Patches hosts/roudix/local.nix the same way roudix-installer.sh does:
copy from local.nix.example, then regex-replace each value in place.
Same option keys, same regex targets — just Python re.sub instead of
sed, so it's easy to diff against the bash script when it changes.
"""
import re
import shutil
from pathlib import Path

from roudix_installer.hardware_detect import detect_prime_bus_ids
from roudix_installer.host_profile import FIXED, restore_fixed_lines
from roudix_installer.state import InstallState, valid_hostname, valid_username

# roudix.officeDictionaries accepts exactly these codes (modules/system/apps/utilities/office.nix)
OFFICE_DICTIONARIES = ("en", "fr", "es", "de", "it", "pt")


def _sub_string(text: str, key: str, value: str) -> str:
    """key = "...";  ->  key = "value";  (keeps original indentation/spacing)"""
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)"[^"]*"')
    return pattern.sub(lambda m: f'{m.group(1)}"{value}"', text)


def _sub_bool(text: str, key: str, value: bool) -> str:
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)(true|false)')
    return pattern.sub(lambda m: f"{m.group(1)}{'true' if value else 'false'}", text)


def _sub_list_single(text: str, key: str, value: str) -> str:
    """key = [ ... ];  ->  key = ["value"];
    "none" (or empty) -> key = [];  — "none" is not a member of the
    roudix.browsers enum, writing ["none"] made the build fail."""
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)\[[^\]]*\]')
    replacement = "[]" if value in ("", "none") else f'["{value}"]'
    return pattern.sub(lambda m: f'{m.group(1)}{replacement}', text)


def _sub_list(text: str, key: str, values: list) -> str:
    """key = [ ... ];  ->  key = ["a" "b" ...];  (Nix list, space-separated, no commas)
    Empty list -> key = [];  — used for roudix.zen.mods / roudix.zen.sine.mods."""
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)\[[^\]]*\]')
    joined = " ".join(f'"{v}"' for v in values)
    return pattern.sub(lambda m: f'{m.group(1)}[{joined}]', text)


def _set_kernel_option(text: str, key: str, active: bool, value: str) -> str:
    """
    hardware.myKernel / hardware.myKernelChaotic are mutually exclusive —
    only one should be uncommented at a time (see local.nix.example). This
    toggles the leading '# ' marker to match `active` and, only when
    active, rewrites the value. Matches the line whether it's currently
    commented or not, so it's idempotent across repeated installer runs.
    An inactive line still gets its value written (harmless since it's
    commented out) — simpler than trying to preserve whatever was there.
    """
    pattern = re.compile(rf'^(\s*)(#\s*)?({re.escape(key)}\s*=\s*)"[^"]*"(.*)$', re.MULTILINE)

    def repl(m):
        indent, _hash, assign, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        prefix = "" if active else "# "
        return f'{indent}{prefix}{assign}"{value}"{tail}'

    return pattern.sub(repl, text)


def _set_bool_option(text: str, key: str, value: bool) -> str:
    """
    Same idea as _set_kernel_option but for a bare true/false option that
    ships commented-out in local.nix.example (e.g. roudix.gaming.apps.*) —
    always uncomments the line and writes `value`.
    """
    pattern = re.compile(rf'^(\s*)(#\s*)?({re.escape(key)}\s*=\s*)(true|false)(.*)$', re.MULTILINE)

    def repl(m):
        indent, _hash, assign, _old, tail = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        return f'{indent}{assign}{"true" if value else "false"}{tail}'

    return pattern.sub(repl, text)


def _set_string_option(text: str, key: str, value: str) -> str:
    """
    Same idea as _set_bool_option but for a `key = "value";` option that
    ships commented-out in local.nix.example (e.g. roudix.spicetify.theme).
    """
    pattern = re.compile(rf'^(\s*)(#\s*)?({re.escape(key)}\s*=\s*)"[^"]*"(.*)$', re.MULTILINE)

    def repl(m):
        indent, _hash, assign, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        return f'{indent}{assign}"{value}"{tail}'

    return pattern.sub(repl, text)


def _set_nullable_string_option(text: str, key: str, value: str) -> str:
    """
    Same as _set_string_option, but writes `null` (no quotes) when `value`
    is empty — used for roudix.spicetify.colorScheme, which ships as
    `= "..."` (a placeholder value, not the literal `null`) in
    local.nix.example.
    """
    pattern = re.compile(rf'^(\s*)(#\s*)?({re.escape(key)}\s*=\s*)(?:null|"[^"]*")(.*)$', re.MULTILINE)

    def repl(m):
        indent, _hash, assign, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        written = f'"{value}"' if value else "null"
        return f'{indent}{assign}{written}{tail}'

    return pattern.sub(repl, text)


def _set_list_option(text: str, key: str, values: list) -> str:
    """
    Same idea as _set_bool_option but for a `key = [ ... ];` option that
    ships commented-out in local.nix.example (e.g.
    roudix.contentCreation.obs.plugins) — always uncomments the line and
    writes `values` (Nix list, space-separated, no commas).
    """
    pattern = re.compile(rf'^(\s*)(#\s*)?({re.escape(key)}\s*=\s*)\[[^\]]*\](.*)$', re.MULTILINE)
    joined = " ".join(f'"{v}"' for v in values)

    def repl(m):
        indent, _hash, assign, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        return f'{indent}{assign}[{joined}]{tail}'

    return pattern.sub(repl, text)


def _eac_vendor(state: InstallState) -> str:
    """Fedora ships no signed NVIDIA modules: on NVIDIA the EAC entry must use Bazzite's."""
    return "bazzite" if state.gpu == "nvidia" else state.eac_vendor


def _bios_device(state: InstallState) -> str:
    """roudix.boot.biosDevice as written: the DISK Limine goes on in legacy BIOS
    mode (the one picked on the Disk page, whatever the partitioning mode),
    \"\" = UEFI. A BIOS install with no known disk is caught by
    check_bios_support(), never silently written as a UEFI config."""
    d = state.disk
    return d.device if d.bios else ""


def _bootloader(state: InstallState) -> str:
    """BIOS machines can only boot Limine here (systemd-boot is UEFI only)."""
    return "limine" if _bios_device(state) else state.bootloader


_BIOS_KEY = "roudix.boot.biosDevice"


def _ensure_bios_line(text: str, value: str) -> str:
    """_sub_string is a silent no-op when the line is missing from local.nix.example
    (an example older than BIOS support). In BIOS mode that would write a UEFI config
    and the install would die at the very end, so add the line after bootloader."""
    if not value or re.search(rf"^[ \t]*#?[ \t]*{re.escape(_BIOS_KEY)}[ \t]*=", text, re.M):
        return text
    line = f'  {_BIOS_KEY} = "{value}";  # legacy BIOS: disk Limine is installed on\n'
    pattern = re.compile(r"^([ \t]*roudix\.boot\.bootloader[ \t]*=[^\n]*\n)", re.M)
    if pattern.search(text):
        return pattern.sub(lambda m: m.group(1) + line, text, count=1)
    return text.rstrip("\n") + "\n" + line  # last resort: a bare option line is valid in a module


def check_bios_support(state: InstallState, config_root: Path) -> None:
    """Fail BEFORE nixos-install (which builds for a long time) when the target
    config cannot do a BIOS install. The configuration is NOT the installer's:
    /iso-cfg is a snapshot of `main` taken when the ISO was built, other branches
    are cloned from GitHub, so either can predate BIOS support (no
    roudix.boot.biosDevice) and would then crash in efibootmgr at the very end."""
    if not state.disk.bios:
        return
    if not _bios_device(state):
        raise RuntimeError(
            "Legacy BIOS boot detected but no target disk is known "
            "(advanced mode needs the disk chosen on the Disk page): "
            "refusing to write a UEFI configuration.")
    boot_nix = config_root / "modules" / "system" / "boot" / "boot.nix"
    if boot_nix.is_file() and "biosDevice" not in boot_nix.read_text():
        raise RuntimeError(
            "Legacy BIOS boot detected, but this configuration (branch "
            f"'{state.branch}') has no roudix.boot.biosDevice, so it can only "
            "install in UEFI mode and would fail at the bootloader step. "
            "Use a branch / an ISO that includes BIOS support, or boot the "
            "installer in UEFI mode.")


def _boot_security(state: InstallState) -> tuple:
    """(secure_boot, eac) as actually written: Secure Boot needs UEFI (Limine
    with sbctl, systemd-boot with lanzaboote); the EAC entry needs UEFI and Limine."""
    uefi = not (state.disk.bios or _bios_device(state))
    limine = _bootloader(state) == "limine" and uefi
    return (state.secure_boot and uefi, state.eac_enable and limine)


def patch_local_nix(state: InstallState, local_nix_text: str) -> str:
    t = local_nix_text
    t = _sub_string(t, "roudix.rgb", state.rgb)
    t = _sub_string(t, "hardware.myGpu", state.gpu)
    t = _sub_bool(t, "hardware.nvidiaLaptop", state.nvidia_laptop)
    # Optimus laptop: PRIME bus IDs, detected on the target machine (the
    # installer runs on it). Written as `null` for everything else.
    prime_ids = detect_prime_bus_ids() if (state.gpu == "nvidia" and state.nvidia_laptop) else {}
    for key in ("nvidiaBusId", "intelBusId", "amdgpuBusId"):
        t = _set_nullable_string_option(t, f"roudix.nvidia_config.{key}", prime_ids.get(key, ""))
    t = _sub_bool(t, "roudix.laptop.enable", state.laptop)
    t = _sub_bool(t, "roudix.laptop.thinkpad", state.laptop_thinkpad)
    t = _sub_string(t, "roudix.laptop.backend", state.laptop_backend)
    t = _sub_bool(t, "roudix.undervolt.only-amd.enable", state.undervolt_enable)
    t = _sub_string(t, "hardware.myCpu", state.cpu)
    is_nvidia = state.gpu == "nvidia"
    # nvidia hosts take the Chaotic-Nyx kernels unless they opted into xddxdd's
    use_chaotic = is_nvidia and state.nvidia_kernel_source == "chaotic"
    t = _set_kernel_option(t, "hardware.myKernel", not use_chaotic, state.kernel)
    t = _set_kernel_option(t, "hardware.myKernelChaotic", use_chaotic, state.kernel_chaotic)
    if is_nvidia:
        t = _set_string_option(t, "hardware.nvidiaKernelSource", state.nvidia_kernel_source)
        t = _set_string_option(t, "hardware.nvidiaDriverSource", state.nvidia_driver_source)
        t = _set_bool_option(t, "hardware.nvidiaBeta", state.nvidia_beta)
        t = _set_bool_option(t, "hardware.nvidiaOpen", state.nvidia_open)
    t = _sub_list_single(t, "roudix.browsers", state.browser)
    t = _sub_bool(t, "roudix.zen.enable", state.zen_browser)
    t = _sub_string(t, "roudix.zen.variant", state.zen_variant)
    t = _sub_bool(t, "roudix.zen.sine.enable", state.zen_sine_enable)
    t = _sub_list(t, "roudix.zen.mods", state.zen_mods)
    t = _sub_list(t, "roudix.zen.sine.mods", state.zen_sine_mods)
    t = _sub_string(t, "roudix.desktop.type", state.desktop)
    t = _sub_string(t, "roudix.desktop.shell", state.desktop_shell)
    for component in ("noctalia", "dms", "caelestia"):
        t = _set_bool_option(t, f"roudix.desktop.latest.{component}", getattr(state, f"latest_{component}"))
    t = _sub_string(t, "roudix.editor", state.editor)
    t = _sub_string(t, "roudix.desktopIntegration", state.desktop_integration)
    t = _sub_string(t, "roudix.terminal", state.terminal)
    t = _sub_string(t, "roudix.fileManager", state.file_manager)
    t = _sub_string(t, "roudix.shell", state.default_shell)
    t = _sub_bool(t, "roudix.vmGuest.enable", state.vm_guest)
    t = _sub_bool(t, "roudix.gaming.enable", state.gaming)
    t = _sub_bool(t, "roudix.gaming.ananicy.enable", state.ananicy_enable)
    if state.gaming:
        t = _set_bool_option(t, "roudix.gaming.apps.lutris.enable", state.gaming_apps_lutris)
        t = _set_bool_option(t, "roudix.gaming.apps.heroic.enable", state.gaming_apps_heroic)
        t = _set_bool_option(t, "roudix.gaming.apps.faugus.enable", state.gaming_apps_faugus)
        t = _set_bool_option(t, "roudix.gaming.apps.prismlauncher.enable", state.gaming_apps_prismlauncher)
        t = _set_bool_option(t, "roudix.gaming.apps.modrinth.enable", state.gaming_apps_modrinth)
        t = _set_bool_option(t, "roudix.gaming.apps.vintagestory.enable", state.gaming_apps_vintagestory)
        t = _set_bool_option(t, "roudix.gaming.apps.mangohud.enable", state.gaming_apps_mangohud)
        t = _set_bool_option(t, "roudix.gaming.steam.millennium.enable", state.gaming_steam_millennium)
    t = _sub_bool(t, "roudix.mesa.useGit", state.mesa_use_git)
    if state.mesa_use_git:
        t = _set_string_option(t, "roudix.mesa.gitSource", state.mesa_git_source)
    t = _sub_string(t, "time.timeZone", state.timezone)
    t = _sub_string(t, "environment.sessionVariables.TZ", state.timezone)
    t = _sub_string(t, "i18n.defaultLocale", state.locale)
    t = _sub_string(t, "console.keyMap", state.keymap)
    t = _sub_string(t, "roudix.keyboardLayout", state.keyboard_layout)
    t = _sub_string(t, "roudix.keyboardVariant", state.keyboard_variant)
    t = _sub_bool(t, "roudix.hosts.gtaFix.enable", state.gta_fix)
    t = _sub_bool(t, "roudix.flatpak.enable", state.flatpak)
    t = _sub_bool(t, "roudix.virtualization.enable", state.virtualization)
    t = _sub_bool(t, "roudix.autoupdate.enable", state.autoupdate)
    t = _sub_string(t, "roudix.autoupdate.interval", state.autoupdate_interval)
    t = _sub_string(t, "roudix.autoupdate.branch", state.branch)
    t = _sub_string(t, "roudix.boot.bootloader", _bootloader(state))
    t = _sub_string(t, _BIOS_KEY, _bios_device(state))
    t = _ensure_bios_line(t, _bios_device(state))
    t = _sub_string(t, "roudix.boot.wallpaperAspect", state.boot_aspect)
    t = _sub_string(t, "roudix.boot.menuResolution", state.boot_resolution)
    # Secure Boot needs UEFI (Limine or systemd-boot); the EAC entry needs UEFI and
    # Limine (the module asserts it): never written on otherwise. Keys are generated on the target at
    # install time; enrolling them in the firmware stays manual (docs/secure-boot-eac.md).
    sb_on, eac_on = _boot_security(state)
    t = _sub_bool(t, "roudix.boot.secureBoot.enable", sb_on)
    t = _sub_bool(t, "roudix.boot.secureBoot.autoGenerateKeys", sb_on)
    t = _sub_bool(t, "roudix.boot.eac.enable", eac_on)
    t = _sub_string(t, "roudix.boot.eac.vendor", _eac_vendor(state))
    t = _sub_string(t, "roudix.matrixClient", state.matrix_client)
    t = _sub_string(t, "roudix.discord", state.discord)
    t = _sub_string(t, "roudix.telegram", state.telegram)
    t = _sub_string(t, "roudix.videoPlayer", state.video_player)
    t = _sub_string(t, "roudix.torrentClient", state.torrent_client)
    t = _sub_string(t, "roudix.musicPlayer", state.music_player)
    t = _sub_string(t, "roudix.mailClient", state.mail_client)
    t = _sub_string(t, "roudix.passwordManager", state.password_manager)
    t = _sub_string(t, "roudix.office", state.office)
    # unknown codes would fail the Nix enum check at build time: keep known ones only
    t = _sub_list(t, "roudix.officeDictionaries",
                  [d for d in dict.fromkeys(state.office_dictionaries) if d in OFFICE_DICTIONARIES])
    t = _sub_bool(t, "roudix.printing.enable", state.printing_enable)
    t = _sub_bool(t, "roudix.printing.scanners.enable", state.printing_scanners)
    # "none" switches the splash off and leaves the theme alone
    t = _sub_bool(t, "roudix.boot.plymouth.enable", state.plymouth_theme != "none")
    if state.plymouth_theme != "none":
        t = _sub_string(t, "roudix.boot.plymouth.theme", state.plymouth_theme)
    t = _sub_bool(t, "roudix.vpn.openvpn.enable", state.vpn_openvpn)
    t = _sub_bool(t, "roudix.waydroid.enable", state.waydroid_enable)

    t = _set_bool_option(t, "roudix.apps.gimp.enable", state.app_gimp)
    t = _set_bool_option(t, "roudix.apps.inkscape.enable", state.app_inkscape)
    t = _set_bool_option(t, "roudix.apps.songrec.enable", state.app_songrec)
    t = _set_bool_option(t, "roudix.apps.easyeffects.enable", state.app_easyeffects)
    t = _set_bool_option(t, "roudix.apps.signal.enable", state.app_signal)
    t = _set_bool_option(t, "roudix.apps.zapzap.enable", state.app_zapzap)
    t = _set_bool_option(t, "roudix.apps.fluxer.enable", state.app_fluxer)
    t = _set_string_option(t, "roudix.apps.fluxer.channel", state.app_fluxer_channel)
    t = _set_bool_option(t, "roudix.apps.cressida.enable", state.app_cressida)

    if state.music_player == "spotify":
        t = _set_string_option(t, "roudix.spicetify.theme", state.spicetify_theme)
        t = _set_nullable_string_option(t, "roudix.spicetify.colorScheme", state.spicetify_color_scheme)
        t = _set_bool_option(t, "roudix.spicetify.extensions.adblock.enable", state.spicetify_adblock)
        t = _set_bool_option(t, "roudix.spicetify.extensions.hidePodcasts.enable", state.spicetify_hide_podcasts)
        t = _set_bool_option(t, "roudix.spicetify.marketplace.enable", state.spicetify_marketplace)

    t = _sub_bool(t, "roudix.contentCreation.enable", state.content_creation_enable)
    if state.content_creation_enable:
        t = _set_bool_option(t, "roudix.contentCreation.obs.enable", state.obs_enable)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.vkcapture.enable", state.obs_plugin_vkcapture)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.pipewireAudioCapture.enable", state.obs_plugin_pipewire_audio_capture)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.backgroundRemoval.enable", state.obs_plugin_background_removal)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.moveTransition.enable", state.obs_plugin_move_transition)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.aitumMultistream.enable", state.obs_plugin_aitum_multistream)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.gstreamer.enable", state.obs_plugin_gstreamer)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.compositeBlur.enable", state.obs_plugin_composite_blur)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.advancedSceneSwitcher.enable", state.obs_plugin_advanced_scene_switcher)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.inputOverlay.enable", state.obs_plugin_input_overlay)
        t = _set_bool_option(t, "roudix.contentCreation.obs.plugins.waveform.enable", state.obs_plugin_waveform)
        t = _sub_string(t, "roudix.contentCreation.videoEditor", state.video_editor)
        t = _set_bool_option(t, "roudix.contentCreation.virtualCamera.enable", state.virtual_camera_enable)
        t = _set_bool_option(t, "roudix.contentCreation.streaming.chatterino.enable", state.chatterino_enable)

    if state.rgb == "openlinkhub":
        t = _sub_bool(t, "roudix.memory.enable", state.memory_rgb_enable)
        t = _sub_string(t, "roudix.memory.type", state.memory_type)
        if state.memory_rgb_enable:
            # smBus / sku are still manually entered by the user (i2cdetect -l /
            # dmidecode), no auto-detect — but now wired through instead of being
            # left at the local.nix.example placeholder values.
            t = _sub_string(t, "roudix.memory.smBus", state.memory_smbus)
            t = _sub_string(t, "roudix.memory.sku", state.memory_sku)

    return t


def _expected_values(state: InstallState) -> list:
    """(key, kind, value) for the options patch_local_nix() always writes —
    the same set roudix-installer.sh re-checks with check_opt()."""
    strings = {
        "roudix.rgb": state.rgb, "hardware.myGpu": state.gpu, "hardware.myCpu": state.cpu,
        "roudix.desktop.type": state.desktop, "roudix.desktop.shell": state.desktop_shell,
        "roudix.editor": state.editor, "roudix.desktopIntegration": state.desktop_integration,
        "roudix.terminal": state.terminal, "roudix.fileManager": state.file_manager,
        "roudix.shell": state.default_shell, "time.timeZone": state.timezone,
        "i18n.defaultLocale": state.locale, "console.keyMap": state.keymap,
        "roudix.keyboardLayout": state.keyboard_layout, "roudix.keyboardVariant": state.keyboard_variant,
        "roudix.autoupdate.interval": state.autoupdate_interval, "roudix.autoupdate.branch": state.branch,
        "roudix.boot.bootloader": _bootloader(state), "roudix.boot.wallpaperAspect": state.boot_aspect,
        "roudix.boot.biosDevice": _bios_device(state),
        "roudix.boot.menuResolution": state.boot_resolution,
        "roudix.boot.eac.vendor": _eac_vendor(state),
        "roudix.matrixClient": state.matrix_client,
        "roudix.discord": state.discord, "roudix.telegram": state.telegram,
        "roudix.videoPlayer": state.video_player, "roudix.torrentClient": state.torrent_client,
        "roudix.musicPlayer": state.music_player, "roudix.mailClient": state.mail_client,
        "roudix.passwordManager": state.password_manager, "roudix.office": state.office,
        "roudix.apps.fluxer.channel": state.app_fluxer_channel,
        "roudix.laptop.backend": state.laptop_backend,
    }
    bools = {
        "hardware.nvidiaLaptop": state.nvidia_laptop, "roudix.laptop.enable": state.laptop,
        "roudix.laptop.thinkpad": state.laptop_thinkpad,
        "roudix.undervolt.only-amd.enable": state.undervolt_enable,
        "roudix.vmGuest.enable": state.vm_guest, "roudix.gaming.enable": state.gaming,
        "roudix.mesa.useGit": state.mesa_use_git, "roudix.hosts.gtaFix.enable": state.gta_fix,
        "roudix.flatpak.enable": state.flatpak, "roudix.virtualization.enable": state.virtualization,
        "roudix.autoupdate.enable": state.autoupdate, "roudix.waydroid.enable": state.waydroid_enable,
        "roudix.printing.enable": state.printing_enable,
        "roudix.boot.plymouth.enable": state.plymouth_theme != "none",
        "roudix.printing.scanners.enable": state.printing_scanners,
        "roudix.vpn.openvpn.enable": state.vpn_openvpn,
        "roudix.zen.enable": state.zen_browser, "roudix.contentCreation.enable": state.content_creation_enable,
        "roudix.boot.secureBoot.enable": _boot_security(state)[0],
        "roudix.boot.eac.enable": _boot_security(state)[1],
    }
    # only the options patch_local_nix() actually writes (they ship commented
    # out in local.nix.example, so an unwritten one would not match)
    if state.mesa_use_git:
        strings["roudix.mesa.gitSource"] = state.mesa_git_source
    if state.gpu == "nvidia":
        strings["hardware.nvidiaKernelSource"] = state.nvidia_kernel_source
        strings["hardware.nvidiaDriverSource"] = state.nvidia_driver_source
        bools["hardware.nvidiaBeta"] = state.nvidia_beta
        bools["hardware.nvidiaOpen"] = state.nvidia_open
    if state.plymouth_theme != "none":
        strings["roudix.boot.plymouth.theme"] = state.plymouth_theme
    out = [(k, "str", v) for k, v in strings.items()]
    out += [(k, "bool", v) for k, v in bools.items()]
    out.append(("roudix.browsers", "list1", state.browser))
    return out


def verify_local_nix(state: InstallState, example_text: str, result_text: str) -> list:
    """Keys whose value did NOT land in local.nix. Every substitution above is a
    silent no-op when its pattern stops matching (e.g. local.nix.example's
    format drifts), so check the result — what roudix-installer.sh does with
    check_opt(). Keys absent from the example (hidden for this host) and lines
    marked `roudix-installer: fixed` are legitimately left alone."""
    missing = []
    for key, kind, value in _expected_values(state):
        in_example = re.search(rf"^[ \t]*#?[ \t]*{re.escape(key)}[ \t]*=", example_text, re.M)
        if not in_example:
            continue
        if any(FIXED in line and re.match(rf"^\s*#?\s*{re.escape(key)}\s*=", line)
               for line in example_text.splitlines()):
            continue
        if kind == "str":
            rhs = f'"{re.escape(value)}"'
        elif kind == "bool":
            rhs = "true" if value else "false"
        else:  # list1 — "none" / "" -> []
            rhs = r"\[\]" if value in ("", "none") else rf'\["{re.escape(value)}"\]'
        if not re.search(rf"^[ \t]*#?[ \t]*{re.escape(key)}[ \t]*=[ \t]*{rhs}", result_text, re.M):
            missing.append(key)
    return missing


def check_identity(state: InstallState) -> None:
    """Refuse a username/hostname that could inject Nix code, shell or a path."""
    if not valid_username(state.username):
        raise ValueError(f"Invalid username: {state.username!r}")
    if not valid_hostname(state.hostname):
        raise ValueError(f"Invalid hostname: {state.hostname!r}")


def write_config(state: InstallState, config_root: Path):
    """
    config_root is the already-copied /iso-cfg tree (== /mnt/etc/nixos).
    Mirrors: username.nix, local.nix from example + sed, home/local.nix
    copied verbatim, boot.local.nix copied verbatim (EFI detection TODO).
    """
    check_identity(state)
    check_bios_support(state, config_root)
    hosts_dir = config_root / "hosts" / state.hostname
    home_dir = config_root / "modules" / "home"
    boot_local = config_root / "modules" / "system" / "boot" / "boot.local.nix"

    (hosts_dir / "username.nix").write_text(f'"{state.username}"\n')

    example = hosts_dir / "local.nix.example"
    local_nix = hosts_dir / "local.nix"
    example_text = example.read_text()
    local_nix.write_text(restore_fixed_lines(example_text, patch_local_nix(state, example_text)))

    shutil.copy(home_dir / "local.nix.example", home_dir / "local.nix")

    boot_example = config_root / "modules" / "system" / "boot" / "boot.local.nix.example"
    if boot_example.exists():
        shutil.copy(boot_example, boot_local)

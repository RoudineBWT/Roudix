"""
Patches hosts/roudix/local.nix the same way roudix-installer.sh does:
copy from local.nix.example, then regex-replace each value in place.
Same option keys, same regex targets — just Python re.sub instead of
sed, so it's easy to diff against the bash script when it changes.
"""
import re
import shutil
from pathlib import Path

from roudix_installer.state import InstallState


def _sub_string(text: str, key: str, value: str) -> str:
    """key = "...";  ->  key = "value";  (keeps original indentation/spacing)"""
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)"[^"]*"')
    return pattern.sub(lambda m: f'{m.group(1)}"{value}"', text)


def _sub_bool(text: str, key: str, value: bool) -> str:
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)(true|false)')
    return pattern.sub(lambda m: f"{m.group(1)}{'true' if value else 'false'}", text)


def _sub_list_single(text: str, key: str, value: str) -> str:
    """key = [ ... ];  ->  key = ["value"];"""
    pattern = re.compile(rf'({re.escape(key)}\s*=\s*)\[[^\]]*\]')
    return pattern.sub(lambda m: f'{m.group(1)}["{value}"]', text)


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


def patch_local_nix(state: InstallState, local_nix_text: str) -> str:
    t = local_nix_text
    t = _sub_string(t, "roudix.rgb", state.rgb)
    t = _sub_string(t, "hardware.myGpu", state.gpu)
    t = _sub_bool(t, "hardware.nvidiaLaptop", state.nvidia_laptop)
    t = _sub_bool(t, "roudix.undervolt.only-amd.enable", state.undervolt_enable)
    t = _sub_string(t, "hardware.myCpu", state.cpu)
    is_nvidia = state.gpu == "nvidia"
    t = _set_kernel_option(t, "hardware.myKernel", not is_nvidia, state.kernel)
    t = _set_kernel_option(t, "hardware.myKernelChaotic", is_nvidia, state.kernel_chaotic)
    t = _sub_list_single(t, "roudix.browsers", state.browser)
    t = _sub_bool(t, "roudix.zen.enable", state.zen_browser)
    t = _sub_string(t, "roudix.zen.variant", state.zen_variant)
    t = _sub_bool(t, "roudix.zen.sine.enable", state.zen_sine_enable)
    t = _sub_list(t, "roudix.zen.mods", state.zen_mods)
    t = _sub_list(t, "roudix.zen.sine.mods", state.zen_sine_mods)
    t = _sub_string(t, "roudix.desktop.type", state.desktop)
    t = _sub_string(t, "roudix.desktop.shell", state.desktop_shell)
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
    t = _sub_string(t, "roudix.boot.bootloader", state.bootloader)
    t = _sub_string(t, "roudix.matrixClient", state.matrix_client)
    t = _sub_string(t, "roudix.discord", state.discord)
    t = _sub_string(t, "roudix.telegram", state.telegram)
    t = _sub_string(t, "roudix.videoPlayer", state.video_player)
    t = _sub_string(t, "roudix.torrentClient", state.torrent_client)
    t = _sub_string(t, "roudix.musicPlayer", state.music_player)
    t = _sub_string(t, "roudix.mailClient", state.mail_client)
    t = _sub_string(t, "roudix.passwordManager", state.password_manager)
    t = _sub_bool(t, "roudix.waydroid.enable", state.waydroid_enable)

    t = _set_bool_option(t, "roudix.apps.gimp.enable", state.app_gimp)
    t = _set_bool_option(t, "roudix.apps.inkscape.enable", state.app_inkscape)
    t = _set_bool_option(t, "roudix.apps.songrec.enable", state.app_songrec)
    t = _set_bool_option(t, "roudix.apps.easyeffects.enable", state.app_easyeffects)
    t = _set_bool_option(t, "roudix.apps.signal.enable", state.app_signal)
    t = _set_bool_option(t, "roudix.apps.zapzap.enable", state.app_zapzap)
    t = _set_bool_option(t, "roudix.apps.fluxer.enable", state.app_fluxer)

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


def write_config(state: InstallState, config_root: Path):
    """
    config_root is the already-copied /iso-cfg tree (== /mnt/etc/nixos).
    Mirrors: username.nix, local.nix from example + sed, home/local.nix
    copied verbatim, boot.local.nix copied verbatim (EFI detection TODO).
    """
    hosts_dir = config_root / "hosts" / "roudix"
    home_dir = config_root / "modules" / "home"
    boot_local = config_root / "modules" / "system" / "boot.local.nix"

    (hosts_dir / "username.nix").write_text(f'"{state.username}"\n')

    example = hosts_dir / "local.nix.example"
    local_nix = hosts_dir / "local.nix"
    local_nix.write_text(patch_local_nix(state, example.read_text()))

    shutil.copy(home_dir / "local.nix.example", home_dir / "local.nix")

    boot_example = config_root / "modules" / "system" / "boot.local.nix.example"
    if boot_example.exists():
        shutil.copy(boot_example, boot_local)

"""
Pre-fill the wizard's answers from hosts/<n>/local.nix.example.

For a host that opted in with `# roudix-installer: only-listed` (see
host_profile.py), the example *is* the profile: its uncommented values are
what that machine should get unless the user changes them. So the wizard
starts from those values instead of its own generic defaults (nixie says
gnome + helium + systemd-boot, the wizard's defaults say niri + brave +
limine).

Hosts without the marker (hosts/roudix) are NOT seeded — their example is a
maintainer's personal config, not a set of defaults for everybody.

Rules:
  * only uncommented lines count (a commented line is an example of how to
    override something, not a value the host sets);
  * `# roudix-installer: fixed` lines are skipped (never asked, kept as-is);
  * a value the wizard can't offer (not in the row's list) is ignored rather
    than silently replaced by the first entry of the list;
  * every option field is first reset to the wizard's own default, so going
    back and switching host doesn't leak the previous host's answers.
"""
import re
from dataclasses import fields

from roudix_installer import host_profile
from roudix_installer.state import InstallState

# nix option -> InstallState attribute. Mirrors config_gen.patch_local_nix —
# keep the two in sync when an option is added there. `roudix.browsers` (a
# list) and `roudix.zen.*mods` are handled separately below.
OPTION_TO_ATTR = {
    "roudix.rgb": "rgb",
    "hardware.myGpu": "gpu",
    "hardware.nvidiaLaptop": "nvidia_laptop",
    "roudix.laptop.enable": "laptop",
    "roudix.laptop.thinkpad": "laptop_thinkpad",
    "roudix.undervolt.only-amd.enable": "undervolt_enable",
    "hardware.myCpu": "cpu",
    "hardware.myKernel": "kernel",
    "hardware.myKernelChaotic": "kernel_chaotic",
    "roudix.zen.enable": "zen_browser",
    "roudix.zen.variant": "zen_variant",
    "roudix.zen.sine.enable": "zen_sine_enable",
    "roudix.desktop.type": "desktop",
    "roudix.desktop.shell": "desktop_shell",
    "roudix.editor": "editor",
    "roudix.desktopIntegration": "desktop_integration",
    "roudix.terminal": "terminal",
    "roudix.fileManager": "file_manager",
    "roudix.shell": "default_shell",
    "roudix.vmGuest.enable": "vm_guest",
    "roudix.gaming.enable": "gaming",
    "roudix.gaming.ananicy.enable": "ananicy_enable",
    "roudix.gaming.apps.lutris.enable": "gaming_apps_lutris",
    "roudix.gaming.apps.heroic.enable": "gaming_apps_heroic",
    "roudix.gaming.apps.faugus.enable": "gaming_apps_faugus",
    "roudix.gaming.apps.prismlauncher.enable": "gaming_apps_prismlauncher",
    "roudix.gaming.apps.modrinth.enable": "gaming_apps_modrinth",
    "roudix.gaming.apps.vintagestory.enable": "gaming_apps_vintagestory",
    "roudix.gaming.apps.mangohud.enable": "gaming_apps_mangohud",
    "roudix.gaming.steam.millennium.enable": "gaming_steam_millennium",
    "roudix.mesa.useGit": "mesa_use_git",
    "time.timeZone": "timezone",
    "i18n.defaultLocale": "locale",
    "console.keyMap": "keymap",
    "roudix.keyboardLayout": "keyboard_layout",
    "roudix.keyboardVariant": "keyboard_variant",
    "roudix.hosts.gtaFix.enable": "gta_fix",
    "roudix.flatpak.enable": "flatpak",
    "roudix.virtualization.enable": "virtualization",
    "roudix.autoupdate.enable": "autoupdate",
    "roudix.autoupdate.interval": "autoupdate_interval",
    "roudix.autoupdate.branch": "branch",
    "roudix.boot.bootloader": "bootloader",
    "roudix.matrixClient": "matrix_client",
    "roudix.discord": "discord",
    "roudix.telegram": "telegram",
    "roudix.videoPlayer": "video_player",
    "roudix.torrentClient": "torrent_client",
    "roudix.musicPlayer": "music_player",
    "roudix.mailClient": "mail_client",
    "roudix.passwordManager": "password_manager",
    "roudix.waydroid.enable": "waydroid_enable",
    "roudix.apps.gimp.enable": "app_gimp",
    "roudix.apps.inkscape.enable": "app_inkscape",
    "roudix.apps.songrec.enable": "app_songrec",
    "roudix.apps.easyeffects.enable": "app_easyeffects",
    "roudix.apps.signal.enable": "app_signal",
    "roudix.apps.zapzap.enable": "app_zapzap",
    "roudix.apps.fluxer.enable": "app_fluxer",
    "roudix.spicetify.theme": "spicetify_theme",
    "roudix.spicetify.colorScheme": "spicetify_color_scheme",
    "roudix.spicetify.extensions.adblock.enable": "spicetify_adblock",
    "roudix.spicetify.extensions.hidePodcasts.enable": "spicetify_hide_podcasts",
    "roudix.spicetify.marketplace.enable": "spicetify_marketplace",
    "roudix.contentCreation.enable": "content_creation_enable",
    "roudix.contentCreation.obs.enable": "obs_enable",
    "roudix.contentCreation.obs.plugins.vkcapture.enable": "obs_plugin_vkcapture",
    "roudix.contentCreation.obs.plugins.pipewireAudioCapture.enable": "obs_plugin_pipewire_audio_capture",
    "roudix.contentCreation.obs.plugins.backgroundRemoval.enable": "obs_plugin_background_removal",
    "roudix.contentCreation.obs.plugins.moveTransition.enable": "obs_plugin_move_transition",
    "roudix.contentCreation.obs.plugins.aitumMultistream.enable": "obs_plugin_aitum_multistream",
    "roudix.contentCreation.obs.plugins.gstreamer.enable": "obs_plugin_gstreamer",
    "roudix.contentCreation.obs.plugins.compositeBlur.enable": "obs_plugin_composite_blur",
    "roudix.contentCreation.obs.plugins.advancedSceneSwitcher.enable": "obs_plugin_advanced_scene_switcher",
    "roudix.contentCreation.obs.plugins.inputOverlay.enable": "obs_plugin_input_overlay",
    "roudix.contentCreation.obs.plugins.waveform.enable": "obs_plugin_waveform",
    "roudix.contentCreation.videoEditor": "video_editor",
    "roudix.contentCreation.virtualCamera.enable": "virtual_camera_enable",
    "roudix.contentCreation.streaming.chatterino.enable": "chatterino_enable",
    "roudix.memory.enable": "memory_rgb_enable",
    "roudix.memory.type": "memory_type",
    "roudix.memory.smBus": "memory_smbus",
    "roudix.memory.sku": "memory_sku",
}

# Options whose Nix value is a list but whose wizard field isn't the same shape.
BROWSERS_KEY = "roudix.browsers"            # ["helium"] -> state.browser = "helium" ([] -> "none")
LIST_ATTRS = {"roudix.zen.mods": "zen_mods", "roudix.zen.sine.mods": "zen_sine_mods"}

_ASSIGN = re.compile(r"^\s*([A-Za-z_][\w.\-]*)\s*=\s*(.+?)\s*;")
_STRING = re.compile(r'^"([^"]*)"$')
_LIST = re.compile(r"^\[(.*)\]$")


def _parse_value(text: str):
    """Nix literal -> str | bool | None | list[str]; anything else (ints,
    expressions) -> the sentinel _UNSUPPORTED."""
    text = text.strip()
    if (m := _STRING.match(text)):
        return m.group(1)
    if text in ("true", "false"):
        return text == "true"
    if text == "null":
        return None
    if (m := _LIST.match(text)):
        return re.findall(r'"([^"]*)"', m.group(1))
    return _UNSUPPORTED


_UNSUPPORTED = object()


def example_values(hostname: str) -> dict:
    """{nix option: parsed value} for the uncommented, non-fixed assignments of
    the host's local.nix.example. Empty unless the host carries the
    `only-listed` marker (or its example can't be found)."""
    example = host_profile.find_example(hostname)
    if example is None:
        return {}
    lines = example.read_text(encoding="utf-8", errors="replace").splitlines()
    if not any(l.startswith(host_profile.MARKER) for l in lines):
        return {}
    values = {}
    for line in lines:
        if line.lstrip().startswith("#") or host_profile.FIXED in line:
            continue
        m = _ASSIGN.match(line)
        if not m:
            continue
        value = _parse_value(m.group(2))
        if value is not _UNSUPPORTED:
            values[m.group(1)] = value
    return values


def _reset_option_fields(state: InstallState):
    defaults = InstallState()
    attrs = set(OPTION_TO_ATTR.values()) | set(LIST_ATTRS.values()) | {"browser"}
    for f in fields(InstallState):
        if f.name in attrs:
            setattr(state, f.name, getattr(defaults, f.name))


def seed_state(state: InstallState, hostname: str, allowed: dict | None = None) -> dict:
    """Reset every option answer to the wizard default, then apply the host's
    example values. `allowed` maps a state attribute to the values its row can
    show (an iterable, or a callable taking the state); a value outside it is
    skipped. Returns {attribute: value} for what was applied."""
    _reset_option_fields(state)
    allowed = allowed or {}
    applied = {}

    def ok(attr, value):
        allow = allowed.get(attr)
        if callable(allow):
            allow = allow(state)
        return allow is None or value in allow

    def put(attr, value):
        if ok(attr, value):
            setattr(state, attr, value)
            applied[attr] = value

    values = example_values(hostname)
    # desktop first: the shell row's allowed values depend on it
    for option, value in sorted(values.items(), key=lambda kv: kv[0] != "roudix.desktop.type"):
        if option in OPTION_TO_ATTR:
            attr = OPTION_TO_ATTR[option]
            if attr == "spicetify_color_scheme" and value is None:
                value = ""
            if isinstance(value, list) or value is None:
                continue
            put(attr, value)
        elif option in LIST_ATTRS and isinstance(value, list):
            put(LIST_ATTRS[option], value)
        elif option == BROWSERS_KEY and isinstance(value, list):
            put("browser", value[0] if value else "none")
    return applied

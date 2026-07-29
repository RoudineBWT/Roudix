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


def patch_local_nix(state: InstallState, local_nix_text: str) -> str:
    t = local_nix_text
    t = _sub_string(t, "roudix.rgb", state.rgb)
    t = _sub_string(t, "hardware.myGpu", state.gpu)
    t = _sub_bool(t, "hardware.nvidiaLaptop", state.nvidia_laptop)
    t = _sub_string(t, "hardware.myCpu", state.cpu)
    t = _sub_string(t, "hardware.myKernel", state.kernel)
    t = _sub_string(t, "hardware.myKernelChaotic", state.kernel_chaotic)
    t = _sub_list_single(t, "roudix.browsers", state.browser)
    t = _sub_bool(t, "roudix.zen.enable", state.zen_browser)
    t = _sub_string(t, "roudix.desktop.type", state.desktop)
    t = _sub_string(t, "roudix.desktop.shell", state.desktop_shell)
    t = _sub_string(t, "roudix.shell", state.default_shell)
    t = _sub_bool(t, "roudix.vmGuest.enable", state.vm_guest)
    t = _sub_bool(t, "roudix.gaming.enable", state.gaming)
    t = _sub_string(t, "time.timeZone", state.timezone)
    t = _sub_string(t, "environment.sessionVariables.TZ", state.timezone)
    t = _sub_string(t, "i18n.defaultLocale", state.locale)
    t = _sub_string(t, "console.keyMap", state.keymap)
    t = _sub_bool(t, "roudix.hosts.gtaFix.enable", state.gta_fix)
    t = _sub_bool(t, "roudix.flatpak.enable", state.flatpak)
    t = _sub_bool(t, "roudix.virtualization.enable", state.virtualization)
    t = _sub_bool(t, "roudix.autoupdate.enable", state.autoupdate)
    t = _sub_string(t, "roudix.autoupdate.interval", state.autoupdate_interval)
    t = _sub_string(t, "roudix.boot.bootloader", state.bootloader)
    t = _sub_string(t, "roudix.matrixClient", state.matrix_client)
    t = _sub_bool(t, "roudix.waydroid.enable", state.waydroid_enable)

    if state.rgb == "openlinkhub":
        t = _sub_bool(t, "roudix.memory.enable", state.memory_rgb_enable)
        t = _sub_string(t, "roudix.memory.type", state.memory_type)
        # SMBus / SKU auto-detect not collected by the GUI yet (same TODO
        # as EFI multi-boot + btrfs auto-patch) — left at local.nix.example
        # defaults, editable by hand after install.

    return t


def write_config(state: InstallState, config_root: Path):
    """
    config_root is the already-copied /iso-cfg tree (== /mnt/etc/nixos).
    Mirrors: username.nix, local.nix from example + sed, home/local.nix
    copied verbatim, boot.local.nix copied verbatim (EFI detection TODO).
    """
    hosts_dir = config_root / "hosts" / "roudix"
    home_dir = config_root / "home"
    boot_local = config_root / "modules" / "system" / "boot.local.nix"

    (hosts_dir / "username.nix").write_text(f'"{state.username}"\n')

    example = hosts_dir / "local.nix.example"
    local_nix = hosts_dir / "local.nix"
    local_nix.write_text(patch_local_nix(state, example.read_text()))

    shutil.copy(home_dir / "local.nix.example", home_dir / "local.nix")

    boot_example = config_root / "modules" / "system" / "boot.local.nix.example"
    if boot_example.exists():
        shutil.copy(boot_example, boot_local)

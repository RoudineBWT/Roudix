"""
Best-effort hardware auto-detection for the installer (GTK and TUI).

sysfs/procfs detection (PCI vendor IDs, /proc/cpuinfo…). Runs once when the
options are built and only picks a sensible default — it never locks
anything in, the user can always override it afterwards.
"""
import re
import subprocess
from pathlib import Path

from roudix_installer.sysutil import run_maybe_root


def is_bios_boot() -> bool:
    """True when the running system was booted in legacy BIOS mode.

    The kernel only exposes /sys/firmware/efi when it was started by UEFI
    firmware, so its absence is the standard test (same one the
    rename-uefi-entry service uses). The live ISO's boot mode is the one the
    installed system will have, since the same firmware boots both.
    """
    return not Path("/sys/firmware/efi").exists()


_PCI_VENDOR_IDS = {
    "0x1002": "amd",
    "0x10de": "nvidia",
    "0x8086": "intel",
}


def _pci_display_vendors() -> set:
    """
    Scan /sys/bus/pci/devices/*/{vendor,class} for display controllers
    (PCI class 0x03xxxx) and return the set of vendors found among
    {"amd", "nvidia", "intel"}.
    """
    vendors = set()
    pci_root = Path("/sys/bus/pci/devices")
    if not pci_root.is_dir():
        return vendors

    for device in pci_root.iterdir():
        try:
            pci_class = (device / "class").read_text().strip()
            pci_vendor = (device / "vendor").read_text().strip()
        except OSError:
            continue
        if not pci_class.startswith("0x03"):
            continue
        vendor = _PCI_VENDOR_IDS.get(pci_vendor)
        if vendor:
            vendors.add(vendor)

    return vendors


def detect_gpu():
    """
    Returns (gpu, nvidia_laptop):
      gpu           -> "amd" | "nvidia" | "intel" | None (nothing detected)
      nvidia_laptop -> True if an NVIDIA dGPU was found alongside an
                       Intel/AMD iGPU (Optimus/PowerXpress laptop)

    Never returns "amd-legacy" — telling GCN 1.x/2.x apart from modern
    RDNA needs a PCI-ID generation lookup that's out of scope here, same
    as the old bash installer (which also just asks a follow-up question
    once "amd" is confirmed).
    """
    vendors = _pci_display_vendors()

    if "nvidia" in vendors:
        nvidia_laptop = "intel" in vendors or "amd" in vendors
        return "nvidia", nvidia_laptop
    if "amd" in vendors:
        return "amd", False
    if "intel" in vendors:
        return "intel", False
    return None, False


def detect_cpu():
    """Returns "amd" | "intel" | None, read from /proc/cpuinfo's vendor_id."""
    try:
        text = Path("/proc/cpuinfo").read_text()
    except OSError:
        return None

    if "AuthenticAMD" in text:
        return "amd"
    if "GenuineIntel" in text:
        return "intel"
    return None


def detect_prime_bus_ids() -> dict:
    """
    PCI bus IDs for NixOS' hardware.nvidia.prime on an Optimus laptop:
    {"nvidiaBusId": "PCI:1:0:0", "intelBusId": ..., "amdgpuBusId": ...}
    (only the keys that were found). NixOS wants the IDs in DECIMAL, sysfs
    addresses are hex: 0000:c1:00.0 -> PCI:193:0:0.
    """
    keys = {"0x10de": "nvidiaBusId", "0x8086": "intelBusId", "0x1002": "amdgpuBusId"}
    found = {}
    for dev in sorted(Path("/sys/bus/pci/devices").glob("*")):
        try:
            if not (dev / "class").read_text().startswith("0x03"):
                continue
            key = keys.get((dev / "vendor").read_text().strip())
            if key is None or key in found:
                continue
            _domain, bus, rest = dev.name.split(":")
            device, function = rest.split(".")
            found[key] = f"PCI:{int(bus, 16)}:{int(device, 16)}:{int(function, 16)}"
        except (OSError, ValueError):
            continue
    return found


# ── Screens (Limine boot wallpaper format) ───────────────────────────────────
# Same algorithm as scripts/detect-boot-aspect.sh (keep them in sync): the MAIN
# screen is the connected one with the highest resolution, and the wallpaper
# format is the roudix.boot.wallpaperAspect value whose ratio is the closest.
_DRM_ROOT = Path("/sys/class/drm")                          # (module-level so tests can point elsewhere)
_FB_SIZE = Path("/sys/class/graphics/fb0/virtual_size")
_ASPECT_RATIOS = {"16x9": 16 / 9, "16x10": 16 / 10, "21x9": 21 / 9, "4x3": 4 / 3}


def _connected_screens() -> list:
    """[(width, height)] of every connected screen (first listed DRM mode =
    preferred / native), falling back to the framebuffer size."""
    screens = []
    drm = _DRM_ROOT
    if drm.is_dir():
        for card in sorted(drm.glob("card*-*")):
            try:
                if (card / "status").read_text().strip() != "connected":
                    continue
                first = (card / "modes").read_text().splitlines()[0]
            except (OSError, IndexError):
                continue
            m = re.match(r"(\d+)x(\d+)", first)
            if m:
                screens.append((int(m.group(1)), int(m.group(2))))
    if not screens:
        try:
            w, h = _FB_SIZE.read_text().strip().split(",")
            screens.append((int(w), int(h)))
        except (OSError, ValueError):
            pass
    return screens


def aspect_of(width: int, height: int) -> str:
    """The roudix.boot.wallpaperAspect value closest to width:height."""
    ratio = width / height
    return min(_ASPECT_RATIOS, key=lambda k: abs(ratio - _ASPECT_RATIOS[k]))


def detect_screen_count() -> int:
    """How many screens are connected (0 when none could be read)."""
    return len(_connected_screens())


def detect_main_screen():
    """Returns (resolution, aspect) of the main screen ("2560x1600", "16x10")
    or (None, None) when no screen could be read. Main = highest resolution
    (width*height); the first one found wins a tie."""
    screens = _connected_screens()
    if not screens:
        return None, None
    width, height = max(screens, key=lambda wh: wh[0] * wh[1])
    return f"{width}x{height}", aspect_of(width, height)


# DMI chassis types that are portable machines: Portable, Laptop, Notebook,
# Sub Notebook, Convertible, Detachable.
_LAPTOP_CHASSIS = {8, 9, 10, 14, 31, 32}


def _read(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return ""


def detect_laptop() -> bool:
    """
    True when the machine looks like a laptop: DMI chassis type says so, or a
    system battery is present. Peripheral batteries (wireless mouse, gamepad)
    are ignored: the kernel marks them scope=Device. Best effort, only used to
    pre-select the "Laptop (TLP)" switch.
    """
    chassis = _read("/sys/class/dmi/id/chassis_type")
    if chassis.isdigit() and int(chassis) in _LAPTOP_CHASSIS:
        return True
    ps = Path("/sys/class/power_supply")
    if ps.is_dir():
        for dev in ps.iterdir():
            if (_read(f"{dev}/type") == "Battery"
                    and _read(f"{dev}/scope").lower() != "device"):
                return True
    return False


def detect_thinkpad() -> bool:
    """True on Lenovo ThinkPads (thinkpad_acpi charge thresholds)."""
    ident = " ".join(
        _read(f"/sys/class/dmi/id/{f}") for f in ("product_family", "product_version")
    )
    return "thinkpad" in ident.lower()


# ── Detection the old bash installer did (VM, RAM SMBus bus and part number) ──

_VM_DMI_HINTS = ("qemu", "kvm", "virtualbox", "vmware", "xen", "bochs", "parallels",
                 "virtual machine")


def detect_vm() -> str:
    """Name of the hypervisor ("kvm", "oracle", "vmware"…), "" on bare metal.

    `systemd-detect-virt --vm` first (containers are not VMs), then the DMI
    strings for a live system where it is missing."""
    try:
        proc = subprocess.run(["systemd-detect-virt", "--vm"], capture_output=True,
                              text=True, timeout=5, stdin=subprocess.DEVNULL)
        out = proc.stdout.strip()
        if out and out != "none":
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    ident = " ".join(_read(f"/sys/class/dmi/id/{f}") for f in ("sys_vendor", "product_name")).lower()
    return next((hint for hint in _VM_DMI_HINTS if hint in ident), "")


def detect_smbus() -> str:
    """i2c bus of the chipset SMBus ("i2c-0"…) where the RAM RGB sits, "" if unknown.
    Needs `i2cdetect` (i2c-tools)."""
    for line in run_maybe_root(["i2cdetect", "-l"]).splitlines():
        if re.search(r"smbus|i801|piix4|nforce", line, re.I) and line.split():
            return line.split()[0]
    return ""


_NO_SKU = {"", "unknown", "notspecified", "nodimm", "undefined", "[empty]", "empty"}


def detect_ram_sku() -> str:
    """Part number of the first populated memory module ("CMH64GX5M2B5200C40"), "" if unknown.
    Needs `dmidecode` and root."""
    for line in run_maybe_root(["dmidecode", "-t", "memory"]).splitlines():
        m = re.match(r"\s*Part Number:\s*(.*)$", line)
        if not m:
            continue
        sku = re.sub(r"\s+", "", m.group(1))
        if sku.lower() not in _NO_SKU:
            return sku
    return ""

"""
Best-effort hardware auto-detection for the GTK installer.

Mirrors the sysfs/procfs detection roudix-installer.sh already does
(same PCI vendor IDs, same /proc/cpuinfo check). Runs once when the
Options page is built and only picks a sensible pre-selected combo
entry — it never locks anything in, the user can always override it
in the UI afterwards, exactly like the "Confirm? [Y/n]" step in the
bash installer.
"""
import re
from pathlib import Path

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
    as roudix-installer.sh (which also just asks a follow-up question
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

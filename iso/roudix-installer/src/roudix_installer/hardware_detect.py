"""
Best-effort hardware auto-detection for the GTK installer.

Mirrors the sysfs/procfs detection roudix-installer.sh already does
(same PCI vendor IDs, same /proc/cpuinfo check). Runs once when the
Options page is built and only picks a sensible pre-selected combo
entry — it never locks anything in, the user can always override it
in the UI afterwards, exactly like the "Confirm? [Y/n]" step in the
bash installer.
"""
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

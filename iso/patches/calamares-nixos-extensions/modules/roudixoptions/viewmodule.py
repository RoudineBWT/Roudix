# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module Calamares "roudixoptions" — page Matériel (GPU/CPU/VM).

Reproduit la détection automatique du script roudix-installer.sh :
  - scan sysfs PCI (vendor/class) pour le GPU
  - /proc/cpuinfo pour le CPU
  - systemd-detect-virt pour la VM

Les résultats sont stockés dans globalstorage sous la clé "roudixHardware",
relus ensuite par le module "nixos" (main.py) pour générer hosts/roudix/local.nix.
"""
import os
import subprocess

import libcalamares


def _detect_gpu():
    vendors_found = set()
    pci_root = "/sys/bus/pci/devices"
    try:
        devices = os.listdir(pci_root)
    except OSError:
        devices = []

    for dev in devices:
        vendor_path = os.path.join(pci_root, dev, "vendor")
        class_path = os.path.join(pci_root, dev, "class")
        try:
            with open(vendor_path) as f:
                vendor = f.read().strip()
            with open(class_path) as f:
                pci_class = f.read().strip()
        except OSError:
            continue

        # PCI class 0x03xxxx = display controller
        if not pci_class.startswith("0x03"):
            continue

        if vendor == "0x1002":
            vendors_found.add("amd")
        elif vendor == "0x10de":
            vendors_found.add("nvidia")
        elif vendor == "0x8086":
            vendors_found.add("intel")

    gpu = ""
    nvidia_laptop = False

    if "nvidia" in vendors_found:
        gpu = "nvidia"
        if "intel" in vendors_found or "amd" in vendors_found:
            nvidia_laptop = True
    elif "amd" in vendors_found:
        gpu = "amd"
    elif "intel" in vendors_found:
        gpu = "intel"

    return gpu, nvidia_laptop


def _detect_cpu():
    try:
        with open("/proc/cpuinfo") as f:
            content = f.read()
    except OSError:
        return ""

    if "AuthenticAMD" in content:
        return "amd"
    elif "GenuineIntel" in content:
        return "intel"
    return ""


def _detect_vm():
    try:
        result = subprocess.run(
            ["systemd-detect-virt"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        virt = result.stdout.strip()
        return virt not in ("", "none")
    except (OSError, subprocess.SubprocessError):
        return False


class PageModel:
    def __init__(self):
        gpu, nvidia_laptop = _detect_gpu()
        self.detected = {
            "gpu": gpu,
            "nvidiaLaptop": nvidia_laptop,
            "cpu": _detect_cpu(),
            "vmGuest": _detect_vm(),
        }
        self.hardware = dict(self.detected)

    def setHardware(self, value):
        self.hardware.update(value)
        libcalamares.globalstorage.insert("roudixHardware", self.hardware)


def run():
    """
    Pas de job d'exécution : cette page ne fait que collecter des choix
    en globalstorage, consommés plus tard par le module "nixos".
    """
    return None

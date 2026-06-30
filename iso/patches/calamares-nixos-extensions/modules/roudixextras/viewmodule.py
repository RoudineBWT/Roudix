# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module Calamares "roudixextras" — page Extras.

Stocke gtaFix / flatpak / virtualization / autoupdate(+interval) /
bootloader / matrixClient / waydroid dans globalstorage sous "roudixExtras",
relu par le module "nixos".
"""
import libcalamares


class PageModel:
    def __init__(self):
        self.extras = {
            "gtaFix": False,
            "flatpak": False,
            "virtualization": False,
            "autoupdate": True,
            "autoupdateInterval": "1h",
            "bootloader": "limine",
            "matrixClient": "none",
            "waydroid": False,
        }

    def setExtras(self, value):
        self.extras.update(value)
        libcalamares.globalstorage.insert("roudixExtras", self.extras)


def run():
    return None

# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module Calamares "roudixsoftware" — page Logiciels.

Stocke kernel / browser / zen / desktop / shell / shellDefault / gaming
dans globalstorage sous "roudixSoftware", relu par le module "nixos".
"""
import libcalamares


class PageModel:
    def __init__(self):
        self.software = {
            "kernel": "cachyos-latest",
            "browser": "brave",
            "zen": False,
            "de": "niri",
            "desktopShell": "noctalia",
            "shellDefault": "fish",
            "gaming": True,
        }

    def setSoftware(self, value):
        self.software.update(value)
        libcalamares.globalstorage.insert("roudixSoftware", self.software)


def run():
    return None

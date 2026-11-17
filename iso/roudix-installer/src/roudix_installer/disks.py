"""
Disk discovery shared by the GTK disk page and the TUI. No GTK here.
"""
import json
import subprocess

from roudix_installer.i18n import tr

# index-based, not string-based, so the mapping doesn't depend on language
MOUNTPOINT_VALUES = [None, "/", "/boot", "swap"]


def list_disks() -> list[dict]:
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,MODEL,TYPE"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    return [
        {"path": f"/dev/{d['name']}", "size": d.get("size", "?"),
         "model": d.get("model") or tr("Unknown disk")}
        for d in data.get("blockdevices", [])
        # zram devices are compressed RAM (the live ISO's swap), never an install target
        if d.get("type") == "disk" and not d.get("name", "").startswith("zram")
    ]


def list_partitions(disk_path: str) -> list[dict]:
    name = disk_path.removeprefix("/dev/")
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,FSTYPE,TYPE", f"/dev/{name}"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    parts = []
    for d in data.get("blockdevices", []):
        for child in d.get("children", []):
            if child.get("type") == "part":
                parts.append({
                    "path": f"/dev/{child['name']}",
                    "size": child.get("size", "?"),
                    "fstype": child.get("fstype") or "?",
                })
    return parts

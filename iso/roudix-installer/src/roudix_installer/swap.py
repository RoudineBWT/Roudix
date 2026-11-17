"""
Temporary swap for the install — everything that does not need GTK.

`nixos-install` evaluates the whole Roudix flake and builds the system in one `nix`
process. On the live ISO the root and /nix/.rw-store are tmpfs (they live in RAM too),
so on an 8 GiB machine or VM the kernel's OOM killer ends the evaluation half way
("Killed process (nix)", exit code 137). Two things give it the room it needs for the
duration of nixos-install: a zram device (swap compressed in RAM: fast, needs no disk, and
the nix heap compresses well) used first, then a swap file on the *target* disk as the
safety net (real extra capacity).
"""
from pathlib import Path

GIB = 1024 ** 3
TARGET_GIB = 16        # RAM + swap we want while nixos-install runs
MAX_SWAP_GIB = 8       # never create more than this
MIN_SWAP_GIB = 2       # a smaller file would not change the outcome
KEEP_FREE_GIB = 12     # always leave this much free on the target for the system itself
STEP_MIB = 256
MAX_ZRAM_GIB = 8       # zram device size cap (uncompressed)
ZRAM_RAM_SHARE = 0.5   # zram may hold at most this share of the RAM as compressed data


def read_meminfo(text: str | None = None) -> tuple[int, int]:
    """(MemTotal, SwapTotal) in KiB."""
    if text is None:
        try:
            text = Path("/proc/meminfo").read_text()
        except OSError:
            return 0, 0
    values = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0])
    return values.get("MemTotal", 0), values.get("SwapTotal", 0)


def plan(mem_kib: int, swap_kib: int, free_bytes: int) -> tuple[int, str]:
    """Size of the swap file to add, in MiB, and why not when it is 0:
    "" (a file is wanted) | "no-need" (enough memory) | "no-space" (target disk too small)."""
    have_gib = (mem_kib + swap_kib) / (1024 * 1024)
    if mem_kib <= 0 or have_gib >= TARGET_GIB - 1:
        return 0, "no-need"
    size_gib = min(TARGET_GIB - have_gib, MAX_SWAP_GIB, free_bytes / GIB - KEEP_FREE_GIB)
    if size_gib < MIN_SWAP_GIB:
        return 0, "no-space"
    return int(size_gib * 1024) // STEP_MIB * STEP_MIB, ""


def low_memory(mem_kib: int, swap_kib: int) -> bool:
    """True when RAM + swap is short of what nixos-install wants (zram and/or a swap file help)."""
    return mem_kib > 0 and (mem_kib + swap_kib) / (1024 * 1024) < TARGET_GIB - 1


def zram_size_mib(mem_kib: int) -> int:
    """Uncompressed size of the zram device: as large as the RAM, at most MAX_ZRAM_GIB. What it
    really takes from RAM is the compressed data only (ZRAM_RAM_SHARE of the RAM, at most)."""
    return int(min(mem_kib / 1024, MAX_ZRAM_GIB * 1024)) // STEP_MIB * STEP_MIB


def fstype_of(path: str, mounts: str | None = None) -> str:
    """Filesystem type of the mount that holds `path` ("" if unknown)."""
    if mounts is None:
        try:
            mounts = Path("/proc/mounts").read_text()
        except OSError:
            return ""
    best, best_len = "", -1
    for line in mounts.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        mountpoint = fields[1].replace("\\040", " ")
        if (path == mountpoint or path.startswith(mountpoint.rstrip("/") + "/")) and len(mountpoint) > best_len:
            best, best_len = fields[2], len(mountpoint)
    return best

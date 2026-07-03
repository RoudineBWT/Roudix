"""
Mirrors the btrfs subvolume auto-patch block from roudix-installer.sh:
scans /proc/mounts for active btrfs mounts, extracts subvol/compress/
ssd/discard from the real mount options, and injects (or replaces) the
`options = [ ... ];` line in the matching fileSystems."<mountpoint>"
block of hardware-configuration.nix. Same logic, same defaults
(compress=zstd:1 always, ssd+discard=async only on real SSD/NVMe).
"""
import re
from pathlib import Path
from typing import Optional


def _parse_mount_opts(mountopts: str) -> dict:
    subvol = compress = noatime = ssd = discard = ""
    for opt in mountopts.split(","):
        if opt.startswith("subvol="):
            subvol = opt[len("subvol="):]
        elif opt == "compress=zstd" or opt.startswith("compress=zstd:"):
            compress = "compress=zstd:1"
        elif opt == "compress-force=zstd" or opt.startswith("compress-force=zstd:"):
            compress = "compress-force=zstd:1"
        elif opt.startswith("compress=") or opt.startswith("compress-force="):
            compress = opt
        elif opt == "noatime":
            noatime = "noatime"
        elif opt == "ssd":
            ssd = "ssd"
        elif opt in ("discard=async", "discard"):
            discard = "discard=async"
    return {"subvol": subvol, "compress": compress, "noatime": noatime, "ssd": ssd, "discard": discard}


def _base_device(dev: str) -> str:
    name = dev.rsplit("/", 1)[-1]
    return re.sub(r"p?\d*$", "", name)  # nvme0n1p2 -> nvme0n1, sda1 -> sda


def _rotational(dev: str) -> Optional[str]:
    path = Path(f"/sys/block/{_base_device(dev)}/queue/rotational")
    try:
        return path.read_text().strip()
    except OSError:
        return None


def read_btrfs_mounts() -> list[dict]:
    try:
        lines = Path("/proc/mounts").read_text().splitlines()
    except OSError:
        return []
    mounts = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 4 and parts[2] == "btrfs":
            mounts.append({"dev": parts[0], "mountpoint": parts[1], "mountopts": parts[3]})
    return mounts


def build_nix_options(mount: dict) -> Optional[list[str]]:
    parsed = _parse_mount_opts(mount["mountopts"])
    subvol = parsed["subvol"].lstrip("/")
    if not subvol:
        return None  # bare root subvol (subvol=/) needs no explicit options

    compress = parsed["compress"] or "compress=zstd:1"
    opts = [f'"subvol={subvol}"', f'"{compress}"']

    rotational = _rotational(mount["dev"])
    if rotational == "0":
        opts += ['"ssd"', '"discard=async"']
    elif parsed["discard"]:
        opts.append('"discard=async"')

    return opts


def _inject_or_replace(lines: list[str], mountpoint: str, opts_str: str) -> list[str]:
    marker = f'fileSystems."{mountpoint}"'

    block_has_options = False
    in_block = False
    for line in lines:
        if 'fileSystems."' in line:
            in_block = marker in line
        if in_block and "options = [" in line:
            block_has_options = True

    out = []
    in_block = False
    done = False
    for line in lines:
        if 'fileSystems."' in line:
            in_block = marker in line

        if in_block and not done and block_has_options and "options = [" in line:
            line = re.sub(r"options = \[[^\]]*\]", f"options = [ {opts_str} ]", line)
            done = True
        elif in_block and not done and not block_has_options and 'fsType = "btrfs"' in line:
            out.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}options = [ {opts_str} ];\n")
            done = True
            continue

        out.append(line)
    return out


def patch_hardware_config(hw_config_path: Path) -> list[str]:
    """
    In-place patch. Returns the list of mountpoints that were actually
    patched (for logging) — empty list if no btrfs mounts were found.
    """
    mounts = read_btrfs_mounts()
    if not mounts:
        return []

    text = hw_config_path.read_text()
    lines = text.splitlines(keepends=True)
    patched = []

    for mount in mounts:
        opts = build_nix_options(mount)
        if opts is None:
            continue
        mountpoint = mount["mountpoint"]
        if f'fileSystems."{mountpoint}"' not in text:
            continue
        lines = _inject_or_replace(lines, mountpoint, " ".join(opts))
        text = "".join(lines)
        patched.append(mountpoint)

    hw_config_path.write_text(text)
    return patched

#!/usr/bin/env python3
# roudix-disk — GTK4/Adwaita disk & mount-point manager for Roudix.
#
# Python take on nix-disk, adapted to how Roudix lays out its disks:
#   * the config lives in ~/.config/roudix (NH_FLAKE), the file we edit is
#     hosts/<hostname>/hardware-configuration.nix (same file roudix-installer's
#     btrfs_patch.py touches);
#   * "/", "/home", "/nix", "/var/log" are btrfs subvolumes (@, @home, @nix,
#     @log) on ONE filesystem and "/boot" is the ESP — all of that is
#     protected and never rewritten, byte for byte;
#   * extra disks go into a marker-delimited managed block at the end of the
#     file; anything we don't understand (bind mounts, nfs, neededForBoot…)
#     is left alone;
#   * rebuilds go through `nh os switch|boot --elevation-strategy pkexec`,
#     like roudix-hw-sync and roudix-kernel-switcher;
#   * formatting runs a tiny root helper (this same file, `--helper-format`)
#     through pkexec — it re-validates everything itself.
#
# Layout of this file: core logic (no GTK) → root helper → GUI. The core part
# is importable/testable without GTK (see tests/test_core.py).

import bisect
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

VERSION = "1.0.0"
APP_ID = "io.roudix.disk"
# Absolute path of the installed launcher, substituted by the Nix package. pkexec
# must run the *wrapper* (it sets PATH for parted/mkfs/...), not the python file.
SELF_PATH = "@self@"

NH_FLAKE = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
ROUDIX_HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
HW_FILE = Path(NH_FLAKE) / "hosts" / ROUDIX_HOST / "hardware-configuration.nix"
BACKUP_DIR = Path(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))) / "roudix-disk" / "backups"
BACKUP_KEEP = 10


# ── translations (gettext) ───────────────────────────────────────────────────
# Same scheme as the other Roudix apps: messages are written in English,
# catalogs live in po/<lang>.po and are compiled to
# share/locale/<lang>/LC_MESSAGES/roudix-disk.mo by the Nix package.
import gettext as _gettext
import glob as _glob

_DOMAIN = "roudix-disk"


def _find_localedir(domain):
    cands = [os.environ.get("ROUDIX_LOCALEDIR", "")]
    d = os.path.dirname(os.path.realpath(__file__))
    while True:
        cands += [os.path.join(d, "share", "locale"), os.path.join(d, "locale")]
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    for c in cands:
        if c and _glob.glob(os.path.join(c, "*", "LC_MESSAGES", domain + ".mo")):
            return c
    return None


_translation = _gettext.translation(_DOMAIN, _find_localedir(_DOMAIN), fallback=True)
tr = _translation.gettext
ngettext = _translation.ngettext


# ═════════════════════════════════════════════════════════════════════════════
# CORE — no GTK below this line until the GUI section
# ═════════════════════════════════════════════════════════════════════════════

# Mount points Roudix owns. Their fileSystems blocks are never modified and
# partitions backing them are shown as "System" (read-only).
PROTECTED_MOUNTS = {
    "/", "/boot", "/boot/efi", "/nix", "/nix/store",
    "/home", "/var", "/var/lib", "/var/log", "/tmp", "/persist",
}
# Nothing may be mounted at or below these (extra disks only).
FORBIDDEN_PREFIXES = ("/boot", "/nix", "/proc", "/sys", "/dev", "/run",
                      "/etc", "/bin", "/usr", "/lib", "/sbin", "/tmp")
# Filesystems we know how to write a sane fileSystems entry for.
MANAGEABLE_FS = {"ext2", "ext3", "ext4", "btrfs", "xfs", "f2fs",
                 "ntfs", "ntfs3", "exfat", "vfat"}
FORMAT_FS = ("ext4", "btrfs")

MOUNTPOINT_RE = re.compile(r"^/[A-Za-z0-9._@+/-]*$")
MARK_BEGIN = "  # >>> roudix-disk (managed block — edited by roudix-disk, hand edits inside may be lost)"
MARK_END = "  # <<< roudix-disk"
MARK_BEGIN_KEY = "# >>> roudix-disk"
MARK_END_KEY = "# <<< roudix-disk"


class ConfigError(Exception):
    """The hardware-configuration.nix is in a shape we refuse to edit."""


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


# ── disks (lsblk) ────────────────────────────────────────────────────────────

@dataclass
class Partition:
    name: str
    path: str
    size: int
    fstype: Optional[str] = None
    label: Optional[str] = None
    uuid: Optional[str] = None
    partlabel: Optional[str] = None
    partuuid: Optional[str] = None
    mountpoints: list = field(default_factory=list)   # live mounts (incl. "[SWAP]")
    system: bool = False                               # backs a protected mount

    @property
    def uuid_path(self) -> Optional[str]:
        return f"/dev/disk/by-uuid/{self.uuid}" if self.uuid else None

    @property
    def manageable(self) -> bool:
        return bool(self.uuid) and (self.fstype or "") in MANAGEABLE_FS


@dataclass
class Disk:
    name: str
    path: str
    size: int
    model: str = ""
    rotational: bool = False
    removable: bool = False
    partitions: list = field(default_factory=list)
    system: bool = False

    @property
    def in_use(self) -> bool:
        """Anything live-mounted (or swapped on) anywhere on this disk."""
        return any(p.mountpoints for p in self.partitions)


def _lsblk_json(*extra) -> dict:
    cols = "NAME,PATH,SIZE,MODEL,TYPE,FSTYPE,LABEL,UUID,PARTLABEL,PARTUUID,MOUNTPOINTS,RM,ROTA"
    for columns in (cols, cols.replace("MOUNTPOINTS", "MOUNTPOINT")):  # old util-linux
        p = subprocess.run(["lsblk", "-J", "-b", "-o", columns, *extra],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
    raise RuntimeError(p.stderr.strip() or "lsblk failed")


def _as_bool(v) -> bool:
    return v in (True, 1, "1", "true")


def _mounts_of(node: dict) -> list:
    mps = node.get("mountpoints")
    if mps is None:
        mps = [node.get("mountpoint")]
    return [m for m in mps if m]


def _part_from(node: dict) -> Partition:
    return Partition(
        name=node["name"], path=node.get("path") or f"/dev/{node['name']}",
        size=int(node.get("size") or 0), fstype=node.get("fstype") or None,
        label=node.get("label") or None, uuid=node.get("uuid") or None,
        partlabel=node.get("partlabel") or None, partuuid=node.get("partuuid") or None,
        mountpoints=_mounts_of(node),
    )


def _descendant_mounts(node: dict) -> list:
    out = _mounts_of(node)
    for c in node.get("children") or []:
        out += _descendant_mounts(c)
    return out


def parse_lsblk(data: dict) -> list:
    """lsblk JSON -> list[Disk]. A disk with a filesystem straight on it (no
    partition table) is exposed as a single pseudo-partition."""
    disks = []
    for d in data.get("blockdevices", []):
        if d.get("type") != "disk":
            continue
        name = d["name"]
        if name.startswith(("zram", "loop", "ram", "sr", "fd")):
            continue
        disk = Disk(name=name, path=d.get("path") or f"/dev/{name}",
                    size=int(d.get("size") or 0), model=(d.get("model") or "").strip(),
                    rotational=_as_bool(d.get("rota")), removable=_as_bool(d.get("rm")))
        children = d.get("children") or []
        for c in children:
            if c.get("type") == "part":
                part = _part_from(c)
                # LUKS / LVM on top: mounts are on grandchildren
                sub = [m for gc in c.get("children") or [] for m in _descendant_mounts(gc)]
                part.mountpoints = part.mountpoints + sub
                disk.partitions.append(part)
        if not children and d.get("fstype"):
            disk.partitions.append(_part_from(d))
        disks.append(disk)
    return disks


def _decode_udev(s: str) -> str:
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), s)


def device_matches(part: Partition, device: str) -> bool:
    """Does a fileSystems `device = "…"` string designate this partition?"""
    base = device.rsplit("/", 1)[-1]
    if device.startswith("/dev/disk/by-uuid/"):
        return bool(part.uuid) and base.lower() == part.uuid.lower()
    if device.startswith("/dev/disk/by-label/"):
        return bool(part.label) and _decode_udev(base) == part.label
    if device.startswith("/dev/disk/by-partlabel/"):
        return bool(part.partlabel) and _decode_udev(base) == part.partlabel
    if device.startswith("/dev/disk/by-partuuid/"):
        return bool(part.partuuid) and base.lower() == part.partuuid.lower()
    if device == part.path:
        return True
    try:
        return os.path.realpath(device) == part.path
    except OSError:
        return False


def is_protected_mount(mp: str) -> bool:
    return mp in PROTECTED_MOUNTS or mp.startswith(("/boot/", "/nix/"))


def list_disks(protected_devices=()) -> list:
    """Disks from lsblk, with `system` flags set from live mounts and from the
    devices of the protected fileSystems entries in the config."""
    disks = parse_lsblk(_lsblk_json())
    for disk in disks:
        for part in disk.partitions:
            live = any(is_protected_mount(m) for m in part.mountpoints)
            cfg = any(device_matches(part, dev) for dev in protected_devices)
            part.system = live or cfg
        disk.system = any(p.system for p in disk.partitions)
    return disks


# ── Nix scanning (strings/comments aware) ────────────────────────────────────

def _tokens(text: str, start: int = 0):
    """Yield (begin, end, kind) with kind in code|string|comment. Code is
    yielded char by char; strings and comments as one span each."""
    i, n = start, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            yield i, j, "comment"
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            yield i, j, "comment"
            i = j
        elif text.startswith("''", i):
            j = i + 2
            while j < n:
                if text[j:j + 3] in ("'''", "''$", "''\\"):
                    j += 3
                elif text.startswith("''", j):
                    j += 2
                    break
                else:
                    j += 1
            yield i, j, "string"
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            yield i, j, "string"
            i = j
        else:
            yield i, i + 1, "code"
            i += 1


def _strip_comments(text: str) -> str:
    return "".join(text[s:e] for s, e, k in _tokens(text) if k != "comment")


def _match_close(text: str, open_idx: int) -> int:
    depth = 0
    for s, _e, k in _tokens(text, open_idx):
        if k != "code":
            continue
        ch = text[s]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s
    raise ConfigError(tr("Unbalanced braces in the configuration file."))


def _split_statements(body: str) -> list:
    out, depth, last = [], 0, 0
    for s, _e, k in _tokens(body):
        if k != "code":
            continue
        ch = body[s]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == ";" and depth == 0:
            out.append(body[last:s])
            last = s + 1
    tail = body[last:]
    if tail.strip():
        out.append(tail)
    return [x.strip() for x in out if x.strip()]


_FS_RE = re.compile(r'fileSystems\."((?:[^"\\])+)"\s*=\s*')
_WRAP_RE = re.compile(r"(?:lib\.)?mk(?:Default|Force)\s+|(?:lib\.)?mkOverride\s+\d+\s+")
_STR_RE = re.compile(r'^"([^"\\$]*)"$')
_LIST_RE = re.compile(r'^\[\s*((?:"[^"\\$]*"\s*)*)\]$')


@dataclass
class FsBlock:
    mountpoint: str
    start: int = -1
    end: int = -1
    full_line: bool = False       # span starts at a line start (can swallow the newline)
    device: Optional[str] = None
    fstype: Optional[str] = None
    options: Optional[list] = None
    adoptable: bool = False


@dataclass
class MountEntry:
    mountpoint: str
    device: str
    fstype: str
    options: list = field(default_factory=list)


def parse_blocks(text: str) -> list:
    """All `fileSystems."<mp>" = …;` blocks of the file, with spans."""
    noncode = [(s, e) for s, e, k in _tokens(text) if k != "code"]
    starts = [s for s, _ in noncode]

    def in_noncode(pos):
        i = bisect.bisect_right(starts, pos) - 1
        return i >= 0 and noncode[i][0] <= pos < noncode[i][1]

    for am in re.finditer(r"fileSystems\s*=\s*\{", text):
        if not in_noncode(am.start()):
            raise ConfigError(tr("This file uses the `fileSystems = { … }` form, which roudix-disk does not edit."))

    blocks, skip_until = [], 0
    for m in _FS_RE.finditer(text):
        if m.start() < skip_until or in_noncode(m.start()):
            continue
        mp = m.group(1)
        i = m.end()
        wm = _WRAP_RE.match(text, i)
        wrapped = bool(wm)
        if wm:
            i = wm.end()
        if i >= len(text) or text[i] != "{":
            blocks.append(FsBlock(mountpoint=mp))     # exotic RHS: never touched
            continue
        close = _match_close(text, i)
        end = close + 1
        while end < len(text) and text[end] in " \t":
            end += 1
        if end < len(text) and text[end] == ";":
            end += 1
        line_start = text.rfind("\n", 0, m.start()) + 1
        full_line = text[line_start:m.start()].strip() == ""
        start = line_start if full_line else m.start()
        skip_until = end

        attrs = {}
        ok = True
        for st in _split_statements(_strip_comments(text[i + 1:close])):
            key, eq, val = st.partition("=")
            if not eq:
                ok = False
                break
            attrs[key.strip()] = val.strip()
        blk = FsBlock(mountpoint=mp, start=start, end=end, full_line=full_line)
        if ok:
            dm = _STR_RE.match(attrs.get("device", ""))
            fm = _STR_RE.match(attrs.get("fsType", ""))
            lm = _LIST_RE.match(attrs["options"]) if "options" in attrs else None
            blk.device = dm.group(1) if dm else None
            blk.fstype = fm.group(1) if fm else None
            if lm:
                blk.options = re.findall(r'"([^"]*)"', lm.group(1))
            blk.adoptable = (
                not wrapped
                and set(attrs) <= {"device", "fsType", "options"}
                and blk.device is not None and blk.device.startswith("/dev/")
                and blk.fstype is not None
                and ("options" not in attrs or lm is not None)
                and not is_protected_mount(mp)
            )
        blocks.append(blk)
    return blocks


def protected_devices(text: str) -> list:
    return [b.device for b in parse_blocks(text) if is_protected_mount(b.mountpoint) and b.device]


def load_entries(text: str) -> list:
    return [MountEntry(b.mountpoint, b.device, b.fstype, list(b.options or []))
            for b in parse_blocks(text) if b.adoptable]


def render_entry(e: MountEntry) -> str:
    opts = " ".join(f'"{o}"' for o in e.options)
    return (f'  fileSystems."{e.mountpoint}" = {{\n'
            f'    device = "{e.device}";\n'
            f'    fsType = "{e.fstype}";\n'
            f'    options = [ {opts} ];\n'
            f'  }};\n')


def build_config(text: str, entries: list) -> str:
    """Return `text` with every adoptable non-protected block replaced by a
    single managed block holding `entries`. Everything else is byte-identical."""
    for e in entries:
        err = validate_mountpoint(e.mountpoint, [], allow_existing=True)
        if err:
            raise ConfigError(f"{e.mountpoint}: {err}")
        if not re.match(r"^/dev/[A-Za-z0-9._/@+-]+$", e.device) or not re.match(r"^[a-z0-9]+$", e.fstype):
            raise ConfigError(f"{e.mountpoint}: invalid device or filesystem")
        if any(not re.match(r"^[A-Za-z0-9._=:@+/,-]+$", o) for o in e.options):
            raise ConfigError(f"{e.mountpoint}: invalid mount option")
    if len({e.mountpoint for e in entries}) != len(entries):
        raise ConfigError(tr("Two entries share the same mount point."))

    spans = []
    for b in parse_blocks(text):
        if b.adoptable:
            end = b.end + 1 if (b.full_line and text[b.end:b.end + 1] == "\n") else b.end
            spans.append((b.start, end))
    for key in (MARK_BEGIN_KEY, MARK_END_KEY):         # marker lines (comments)
        pos = text.find(key)
        if pos >= 0:
            ls = text.rfind("\n", 0, pos) + 1
            le = text.find("\n", pos)
            if key == MARK_BEGIN_KEY and text[max(ls - 2, 0):ls] == "\n\n":
                ls -= 1                       # also drop the blank separator we inserted
            spans.append((ls, len(text) if le < 0 else le + 1))
    out = text
    for s, e in sorted(set(spans), reverse=True):
        out = out[:s] + out[e:]

    if not entries:
        return out
    stripped = out.rstrip()
    if not stripped.endswith("}"):
        raise ConfigError(tr("The configuration file does not end with a closing brace."))
    last = stripped.rfind("}")
    region = MARK_BEGIN + "\n" + "".join(render_entry(e) for e in entries) + MARK_END + "\n"
    return out[:last].rstrip() + "\n\n" + region + out[last:]


# ── mount points & options ───────────────────────────────────────────────────

def validate_mountpoint(mp: str, taken, allow_existing=False) -> Optional[str]:
    """None if OK, else a translated reason. `taken` = mount points already used."""
    mp = mp.strip()
    if not MOUNTPOINT_RE.match(mp):
        return tr("Use an absolute path with letters, digits and . _ - @ + only.")
    if len(mp) > 1 and mp.endswith("/"):
        return tr("No trailing slash.")
    if "//" in mp or "/../" in mp + "/" or "/./" in mp + "/":
        return tr("Use a clean path (no //, . or ..).")
    if mp == "/" or is_protected_mount(mp):
        return tr("This mount point belongs to the system.")
    if any(mp == p or mp.startswith(p + "/") for p in FORBIDDEN_PREFIXES):
        return tr("Mounting here could break the system.")
    if not allow_existing and mp in set(taken):
        return tr("This mount point is already used.")
    return None


def default_options(fstype: str, rotational: bool, uid: int, gid: int) -> list:
    opts = ["defaults", "nofail", "x-gvfs-show"]
    if fstype == "btrfs":                       # same defaults as Roudix's own btrfs mounts
        opts += ["compress=zstd:1", "noatime"]
        if not rotational:
            opts += ["ssd", "discard=async"]
    elif fstype in ("ntfs3", "exfat", "vfat"):
        opts += [f"uid={uid}", f"gid={gid}", "umask=022"]
    return opts


def nix_fstype(blkid_type: str) -> str:
    return "ntfs3" if blkid_type == "ntfs" else blkid_type    # kernel driver, no ntfs-3g needed


def suggest_mountpoint(part: Partition, taken) -> str:
    base = re.sub(r"[^A-Za-z0-9._@+-]", "_", part.label or part.name) or part.name
    cand, n = f"/media/{base}", 2
    while cand in set(taken):
        cand, n = f"/media/{base}{n}", n + 1
    return cand


# ── reading / writing the config file ────────────────────────────────────────

def backup_config(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"{ROUDIX_HOST}-{time.strftime('%Y%m%d-%H%M%S')}.nix"
    shutil.copy2(path, dest)
    for old in sorted(BACKUP_DIR.glob(f"{ROUDIX_HOST}-*.nix"))[:-BACKUP_KEEP]:
        old.unlink(missing_ok=True)
    return dest


def latest_backup() -> Optional[Path]:
    files = sorted(BACKUP_DIR.glob(f"{ROUDIX_HOST}-*.nix")) if BACKUP_DIR.exists() else []
    return files[-1] if files else None


def write_config(path: Path, new_text: str) -> Path:
    """Backup, syntax-check with `nix-instantiate --parse` when available, then
    atomically replace. Returns the backup path."""
    backup = backup_config(path)
    tmp = path.with_name(path.name + ".roudix-disk.tmp")
    tmp.write_text(new_text)
    try:
        if shutil.which("nix-instantiate"):
            p = subprocess.run(["nix-instantiate", "--parse", str(tmp)],
                               capture_output=True, text=True, timeout=30)
            if p.returncode != 0:
                raise ConfigError(tr("Generated file is not valid Nix:") + "\n" + p.stderr.strip())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return backup


def restore_backup(path: Path, backup: Path):
    shutil.copy2(backup, path)


def rebuild_cmd(mode: str) -> list:
    assert mode in ("switch", "boot")
    return ["nh", "os", mode, "--elevation-strategy", "pkexec",
            "--accept-flake-config", f"path:{NH_FLAKE}"]


# ═════════════════════════════════════════════════════════════════════════════
# ROOT HELPER — `pkexec roudix-disk --helper-format DEVICE FS LABEL`
# Runs as root, so it trusts nothing from the caller: it re-checks the device
# against lsblk and refuses anything mounted, swapped on, or system-related.
# ═════════════════════════════════════════════════════════════════════════════

_DISK_NODE_RE = re.compile(r"^/dev/(?:sd[a-z]{1,2}|vd[a-z]{1,2}|xvd[a-z]|nvme\d+n\d+|mmcblk\d+)$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,15}$")


def _say(msg: str):
    print(msg, flush=True)


def _sh(cmd: list):
    _say("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=subprocess.STDOUT)


def helper_format(argv: list) -> int:
    import pwd
    import tempfile
    if os.geteuid() != 0:
        _say("This helper must run as root (via pkexec).")
        return 2
    if len(argv) != 3:
        _say("usage: --helper-format DEVICE FS LABEL")
        return 2
    dev, fs, label = argv
    if not _DISK_NODE_RE.match(dev):
        _say(f"Refusing: {dev!r} is not a whole-disk device node.")
        return 2
    if fs not in FORMAT_FS or not _LABEL_RE.match(label):
        _say("Refusing: unsupported filesystem or invalid label.")
        return 2
    try:
        uid = int(os.environ["PKEXEC_UID"])
        gid = pwd.getpwuid(uid).pw_gid
    except (KeyError, ValueError):
        _say("Refusing: cannot determine the calling user (PKEXEC_UID).")
        return 2
    try:
        tree = _lsblk_json(dev)["blockdevices"]
    except Exception as e:
        _say(f"Refusing: lsblk failed ({e}).")
        return 2
    if len(tree) != 1 or tree[0].get("type") != "disk":
        _say("Refusing: not a disk.")
        return 2
    busy = _descendant_mounts(tree[0])
    if busy:
        _say("Refusing: the disk is in use (" + ", ".join(busy) + "). Unmount it first.")
        return 2

    part = dev + ("p" if dev[-1].isdigit() else "") + "1"
    mnt = None
    try:
        _sh(["wipefs", "-a", dev])
        _sh(["parted", "-s", dev, "mklabel", "gpt", "mkpart", label, "1MiB", "100%"])
        subprocess.run(["udevadm", "settle"], check=False)
        subprocess.run(["partprobe", dev], check=False)
        for _ in range(50):
            if os.path.exists(part):
                break
            time.sleep(0.2)
        else:
            _say(f"Partition {part} did not appear.")
            return 1
        if fs == "ext4":
            _sh(["mkfs.ext4", "-F", "-L", label, part])
        else:
            _sh(["mkfs.btrfs", "-f", "-L", label, part])
        subprocess.run(["udevadm", "settle"], check=False)
        # Give the new filesystem to the calling user so it is writable at once.
        mnt = tempfile.mkdtemp(prefix="roudix-disk-")
        _sh(["mount", part, mnt])
        os.chown(mnt, uid, gid)
        os.chmod(mnt, 0o755)
        _sh(["umount", mnt])
        uuid = subprocess.run(["blkid", "-s", "UUID", "-o", "value", part],
                              capture_output=True, text=True).stdout.strip()
        _say(f"RESULT uuid={uuid}")
        return 0
    except subprocess.CalledProcessError as e:
        _say(f"Command failed with exit code {e.returncode}.")
        return 1
    finally:
        if mnt:
            subprocess.run(["umount", mnt], check=False, capture_output=True)
            try:
                os.rmdir(mnt)
            except OSError:
                pass


if __name__ == "__main__" and len(sys.argv) > 1:
    if sys.argv[1] == "--helper-format":
        sys.exit(helper_format(sys.argv[2:]))
    if sys.argv[1] in ("--version", "-V"):
        print(f"roudix-disk {VERSION}")
        sys.exit(0)

# ═══ GUI ═══════════════════════════════════════════════════════════════════
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

import threading  # noqa: E402

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
esc = GLib.markup_escape_text


def self_launcher() -> str:
    if SELF_PATH[:1] != "@":
        return SELF_PATH
    return shutil.which("roudix-disk") or os.path.abspath(sys.argv[0])


class RunWindow(Adw.Window):
    """Modal log window running one command (pkexec / nh) in a thread."""

    def __init__(self, parent, title, cmd, on_done):
        super().__init__(transient_for=parent, modal=True, title=title,
                         default_width=680, default_height=440, deletable=False)
        self._on_done = on_done
        self.lines = []

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        self.spinner = Gtk.Spinner(spinning=True)
        header.pack_start(self.spinner)

        self.view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                 wrap_mode=Gtk.WrapMode.WORD_CHAR, top_margin=8,
                                 bottom_margin=8, left_margin=12, right_margin=12)
        self.buf = self.view.get_buffer()
        self.end_mark = self.buf.create_mark(None, self.buf.get_end_iter(), False)
        scroller = Gtk.ScrolledWindow(vexpand=True, child=self.view)

        self.close_btn = Gtk.Button(label=tr("Close"), sensitive=False, halign=Gtk.Align.END,
                                    margin_top=8, margin_bottom=8, margin_end=12,
                                    css_classes=["pill"])
        self.close_btn.connect("clicked", lambda *_: self.close())

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(scroller)
        view.add_bottom_bar(self.close_btn)
        self.set_content(view)
        self.present()
        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _append(self, text):
        self.buf.insert(self.buf.get_end_iter(), text)
        self.buf.move_mark(self.end_mark, self.buf.get_end_iter())
        self.view.scroll_to_mark(self.end_mark, 0.0, False, 0.0, 0.0)
        return False

    def _worker(self, cmd):
        rc = 1
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            for raw in proc.stdout:
                line = ANSI_ESCAPE.sub("", raw.split("\r")[-1] if raw.endswith("\n") else raw)
                self.lines.append(line.rstrip("\n"))
                GLib.idle_add(self._append, line)
            rc = proc.wait()
        except OSError as e:          # missing binary…
            msg = f"{cmd[0]}: {e}\n"
            self.lines.append(msg.strip())
            GLib.idle_add(self._append, msg)
            rc = -1
        GLib.idle_add(self._finish, rc)

    def _finish(self, rc):
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.set_deletable(True)
        self.close_btn.set_sensitive(True)
        self.close_btn.grab_focus()
        self._append("\n" + (tr("Done.") if rc == 0 else tr("Failed (exit code {rc}).").format(rc=rc)) + "\n")
        self._on_done(rc, self.lines)
        return False


class DiskWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=tr("Roudix Disks"),
                         default_width=760, default_height=720)
        self.hw_text = ""
        self.saved_entries = []     # as currently in the file
        self.entries = []           # working copy (what Apply will write)
        self.prot_devs = []
        self.disks = []
        self._groups = []

        self.toasts = Adw.ToastOverlay()
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text=tr("Rescan disks"))
        refresh.connect("clicked", lambda *_: self.scan())
        self.apply_btn = Gtk.Button(label=tr("Apply…"), sensitive=False,
                                    css_classes=["suggested-action"])
        self.apply_btn.connect("clicked", self._on_apply)
        header.pack_start(refresh)
        header.pack_end(self.apply_btn)
        toolbar.add_top_bar(header)

        banners = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pending_banner = Adw.Banner.new(tr("Changes not applied yet"))
        self.pending_banner.set_button_label(tr("Apply…"))
        self.pending_banner.connect("button-clicked", self._on_apply)
        self.missing_banner = Adw.Banner.new("")
        self.missing_banner.set_button_label(tr("Remove"))
        self.missing_banner.connect("button-clicked", self._on_remove_missing)
        self.error_banner = Adw.Banner.new("")
        self.error_banner.set_button_label(tr("Dismiss"))
        self.error_banner.add_css_class("error")
        self.error_banner.connect("button-clicked", lambda b: b.set_revealed(False))
        for b in (self.pending_banner, self.missing_banner, self.error_banner):
            b.set_revealed(False)
            banners.append(b)
        toolbar.add_top_bar(banners)

        self.stack = Gtk.Stack()
        self.page = Adw.PreferencesPage()
        self.status = Adw.StatusPage(icon_name="dialog-warning-symbolic")
        self.stack.add_named(self.page, "disks")
        self.stack.add_named(self.status, "error")
        toolbar.set_content(self.stack)
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)
        self.reload_config()

    # ── state ────────────────────────────────────────────────────────────────
    @property
    def dirty(self) -> bool:
        return self.entries != self.saved_entries

    def toast(self, msg):
        self.toasts.add_toast(Adw.Toast.new(msg))

    def show_error(self, msg):
        self.error_banner.set_title(msg.replace("\n", " "))
        self.error_banner.set_revealed(True)

    def reload_config(self):
        """(Re)read hardware-configuration.nix, dropping unsaved edits."""
        if not HW_FILE.exists():
            self.status.set_title(tr("Configuration not found"))
            self.status.set_description(esc(tr("Could not find {file}. Set ROUDIX_HOST or NH_FLAKE if your configuration lives elsewhere.").format(file=str(HW_FILE))))
            self.stack.set_visible_child_name("error")
            self.apply_btn.set_sensitive(False)
            return
        try:
            self.hw_text = HW_FILE.read_text()
            self.saved_entries = load_entries(self.hw_text)
            self.prot_devs = protected_devices(self.hw_text)
        except (ConfigError, OSError) as e:
            self.status.set_title(tr("This configuration can't be edited here"))
            self.status.set_description(esc(str(e)))
            self.stack.set_visible_child_name("error")
            self.apply_btn.set_sensitive(False)
            return
        self.entries = [MountEntry(e.mountpoint, e.device, e.fstype, list(e.options))
                        for e in self.saved_entries]
        self.stack.set_visible_child_name("disks")
        self.scan()

    def scan(self):
        try:
            self.disks = list_disks(self.prot_devs)
        except Exception as e:      # lsblk missing / bad output
            self.disks = []
            self.show_error(tr("Could not list disks: {err}").format(err=e))
        self.render()

    # ── rendering ────────────────────────────────────────────────────────────
    def _entry_for(self, part):
        for e in self.entries:
            if device_matches(part, e.device):
                return e
        return None

    def _missing(self):
        return [e for e in self.entries if not os.path.exists(e.device)]

    def render(self):
        for g in self._groups:
            self.page.remove(g)
        self._groups = []

        self.pending_banner.set_revealed(self.dirty)
        self.apply_btn.set_sensitive(self.dirty)
        missing = self._missing()
        if missing:
            self.missing_banner.set_title(ngettext(
                "{n} configured disk is not connected", "{n} configured disks are not connected",
                len(missing)).format(n=len(missing)))
        self.missing_banner.set_revealed(bool(missing))

        if not self.disks:
            g = Adw.PreferencesGroup()
            g.add(Adw.ActionRow(title=tr("No disks found")))
            self._add_group(g)
        for disk in self.disks:
            self._add_group(self._disk_group(disk))

    def _add_group(self, g):
        self.page.add(g)
        self._groups.append(g)

    def _disk_group(self, disk):
        kind = "HDD" if disk.rotational else "SSD"
        extra = " · " + tr("removable") if disk.removable else ""
        g = Adw.PreferencesGroup(
            title=esc(f"{disk.path} — {disk.model or tr('Unknown disk')}"),
            description=esc(f"{human_size(disk.size)} · {kind}{extra}"))
        if not disk.system:
            fmt = Gtk.Button(label=tr("Format…"), valign=Gtk.Align.CENTER)
            if disk.in_use:
                fmt.set_sensitive(False)
                fmt.set_tooltip_text(tr("Mounted — unmount it first"))
            else:
                fmt.connect("clicked", lambda *_: self._on_format(disk))
            g.set_header_suffix(fmt)
        if not disk.partitions:
            row = Adw.ActionRow(title=tr("Empty disk"),
                                subtitle=tr("No partition table or filesystem. Use Format… to prepare it."))
            g.add(row)
        for part in disk.partitions:
            g.add(self._partition_row(disk, part))
        return g

    def _partition_row(self, disk, part):
        bits = [part.path, part.fstype or tr("unknown filesystem"), human_size(part.size)]
        entry = self._entry_for(part)
        live = [m for m in part.mountpoints if m != "[SWAP]"]
        if live and not part.system and not (entry and entry.mountpoint in live):
            bits.append(tr("mounted at {mp}").format(mp=live[0]))
        row = Adw.ActionRow(title=esc(part.label or part.name), subtitle=esc(" · ".join(bits)))

        def suffix_label(text):
            row.add_suffix(Gtk.Label(label=text, css_classes=["dim-label"], valign=Gtk.Align.CENTER))

        if part.system:
            row.add_prefix(Gtk.Image.new_from_icon_name("changes-prevent-symbolic"))
            suffix_label(tr("System"))
        elif part.fstype == "swap" or "[SWAP]" in part.mountpoints:
            suffix_label("swap")
        elif entry:
            suffix_label(entry.mountpoint)
            edit = Gtk.Button(icon_name="document-edit-symbolic", valign=Gtk.Align.CENTER,
                              css_classes=["flat"], tooltip_text=tr("Change mount point"))
            edit.connect("clicked", lambda *_: self._ask_mountpoint(disk, part, entry))
            rm = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER,
                            css_classes=["flat"], tooltip_text=tr("Remove mount point"))
            rm.connect("clicked", lambda *_: self._on_remove(entry))
            row.add_suffix(edit)
            row.add_suffix(rm)
        elif part.manageable:
            add = Gtk.Button(label=tr("Mount…"), valign=Gtk.Align.CENTER)
            add.connect("clicked", lambda *_: self._ask_mountpoint(disk, part, None))
            row.add_suffix(add)
        else:
            suffix_label(tr("Not supported"))
        return row

    # ── mount points ─────────────────────────────────────────────────────────
    def _ask_mountpoint(self, disk, part, entry, then=None):
        taken = [e.mountpoint for e in self.entries if e is not entry]
        dlg = Adw.AlertDialog.new(tr("Mount point"),
                                  tr("Where should {device} be mounted?").format(device=part.path))
        row = Adw.EntryRow(title=tr("Mount point"))
        row.set_text(entry.mountpoint if entry else suggest_mountpoint(part, taken))
        lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])
        lb.append(row)
        err = Gtk.Label(xalign=0, wrap=True, css_classes=["error", "caption"])
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(lb)
        box.append(err)
        dlg.set_extra_child(box)
        dlg.add_response("cancel", tr("Cancel"))
        dlg.add_response("save", tr("Save"))
        dlg.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dlg.set_default_response("save")
        dlg.set_close_response("cancel")

        def validate(*_):
            problem = validate_mountpoint(row.get_text(), taken)
            err.set_text(problem or "")
            dlg.set_response_enabled("save", problem is None)

        row.connect("changed", validate)
        validate()

        def on_response(_d, resp):
            if resp != "save":
                return
            mp = row.get_text().strip()
            if entry:
                entry.mountpoint = mp
            else:
                fs = nix_fstype(part.fstype)
                self.entries.append(MountEntry(
                    mp, part.uuid_path, fs,
                    default_options(fs, disk.rotational, os.getuid(), os.getgid())))
            self.render()

        dlg.connect("response", on_response)
        dlg.present(self)

    def _on_remove(self, entry):
        self.entries.remove(entry)
        self.render()

    def _on_remove_missing(self, *_):
        gone = {id(e) for e in self._missing()}
        self.entries = [e for e in self.entries if id(e) not in gone]
        self.render()

    # ── formatting ───────────────────────────────────────────────────────────
    def _on_format(self, disk):
        self.scan()                                    # state may have changed
        disk = next((d for d in self.disks if d.path == disk.path), None)
        if disk is None or disk.system or disk.in_use:
            self.toast(tr("This disk is in use and can't be formatted."))
            return
        affected = [e for e in self.entries
                    if any(device_matches(p, e.device) for p in disk.partitions)]

        dlg = Adw.AlertDialog.new(
            tr("Format {device}?").format(device=disk.path),
            tr("All data on {device} ({model}, {size}) will be permanently erased and replaced by a single GPT partition.").format(
                device=disk.path, model=disk.model or tr("Unknown disk"), size=human_size(disk.size)))
        fs_row = Adw.ComboRow(title=tr("Filesystem"), model=Gtk.StringList.new(list(FORMAT_FS)))
        label_row = Adw.EntryRow(title=tr("Label"))
        label_row.set_text("Data")
        confirm_row = Adw.EntryRow(title=tr("Type {device} to confirm").format(device=disk.path))
        lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])
        for r in (fs_row, label_row, confirm_row):
            lb.append(r)
        err = Gtk.Label(xalign=0, wrap=True, css_classes=["error", "caption"])
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(lb)
        box.append(err)
        dlg.set_extra_child(box)
        dlg.add_response("cancel", tr("Cancel"))
        dlg.add_response("format", tr("Erase and format"))
        dlg.set_response_appearance("format", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.set_close_response("cancel")

        def validate(*_):
            label_ok = bool(_LABEL_RE.match(label_row.get_text()))
            err.set_text("" if label_ok else tr("Label: 1–16 characters, letters, digits . _ - only."))
            dlg.set_response_enabled(
                "format", label_ok and confirm_row.get_text().strip() == disk.path)

        for r in (label_row, confirm_row):
            r.connect("changed", validate)
        validate()

        def on_response(_d, resp):
            if resp == "format":
                self._run_format(disk, FORMAT_FS[fs_row.get_selected()],
                                 label_row.get_text().strip(), affected)

        dlg.connect("response", on_response)
        dlg.present(self)

    def _run_format(self, disk, fs, label, affected):
        cmd = ["pkexec", self_launcher(), "--helper-format", disk.path, fs, label]

        def done(rc, lines):
            if rc != 0:
                self.toast(tr("Authentication cancelled.") if rc in (126, 127)
                           else tr("Formatting failed — see the log."))
                self.scan()
                return
            uuid = next((l.split("uuid=", 1)[1].strip() for l in lines
                         if l.startswith("RESULT uuid=")), "")
            # the old UUIDs are gone: drop their now-dangling entries
            self.entries = [e for e in self.entries if e not in affected]
            self.scan()
            self.toast(tr("{device} formatted.").format(device=disk.path))
            for d in self.disks:
                for p in d.partitions:
                    if uuid and p.uuid == uuid and p.manageable:
                        self._ask_mountpoint(d, p, None)
                        return

        RunWindow(self, tr("Formatting {device}…").format(device=disk.path), cmd, done)

    # ── apply ────────────────────────────────────────────────────────────────
    def _on_apply(self, *_):
        if not self.dirty:
            return
        dlg = Adw.AlertDialog.new(
            tr("Apply changes?"),
            tr("{file} will be updated and Roudix rebuilt. The current file is backed up first, and restored if the rebuild fails.").format(file=str(HW_FILE)))
        dlg.add_response("cancel", tr("Cancel"))
        dlg.add_response("boot", tr("At next boot"))
        dlg.add_response("switch", tr("Apply now"))
        dlg.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)
        dlg.set_default_response("switch")
        dlg.set_close_response("cancel")
        dlg.connect("response", lambda _d, r: self._do_apply(r) if r in ("boot", "switch") else None)
        dlg.present(self)

    def _do_apply(self, mode):
        old_text = self.hw_text
        try:
            new_text = build_config(old_text, self.entries)
            backup = write_config(HW_FILE, new_text)
        except (ConfigError, OSError) as e:
            self.show_error(str(e))
            return
        self.error_banner.set_revealed(False)

        def done(rc, _lines):
            if rc == 0:
                self.toast(tr("Changes applied."))
                self.reload_config()
                return
            try:
                restore_backup(HW_FILE, backup)
            except OSError as e:
                self.show_error(tr("Rebuild failed and the backup could not be restored: {err}").format(err=e))
                return
            self.hw_text = old_text
            self.show_error(tr("Authentication cancelled — nothing was changed.") if rc in (126, 127)
                            else tr("Rebuild failed — the previous configuration was restored. Your edits are still here."))
            self.render()

        RunWindow(self, tr("Rebuilding Roudix…"), rebuild_cmd(mode), done)


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        win = self.props.active_window or DiskWindow(self)
        win.present()


def main():
    GLib.set_application_name(tr("Roudix Disks"))
    return App().run(sys.argv[:1])


if __name__ == "__main__":
    sys.exit(main())

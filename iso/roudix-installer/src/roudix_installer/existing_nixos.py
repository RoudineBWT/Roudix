"""
"Convert an existing NixOS" mode — everything that does not need GTK.

The wizard has two modes:

    fresh      booted from the Roudix ISO: partition (disko), nixos-install
    existing   run on an already installed NixOS: no partitioning, the config
               lives in ~/.config/roudix, applied with `nixos-rebuild boot`

The safety net of the second mode is NixOS itself: `nixos-rebuild boot` adds a
new generation and leaves the previous one in the boot menu. What generations
do NOT cover (a bootloader that fails to start, an old stateVersion, a rewritten
hardware-configuration.nix) is covered by a copy of /etc/nixos plus a
RESTORE.txt describing how to go back — see backup_files()/restore_text().

Kept free of GTK imports on purpose: it can be unit-tested and, later, reused
by a TTY front-end to replace roudix-installer.sh.
"""
import os
import pwd
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO_URL = "https://github.com/RoudineBWT/Roudix"
BACKUP_ROOT = Path("/var/backups/roudix")
# system.stateVersion forced by modules/system/nix/common.nix — keep in sync.
ROUDIX_STATE_VERSION = "26.11"
# Below this much free space in /boot, `nixos-rebuild boot` may fail half way:
# CachyOS kernels + several Limine generations fill a 512M ESP quickly.
MIN_BOOT_FREE_MIB = 1024
MIN_STORE_FREE_GIB = 10

MODE_FRESH = "fresh"
MODE_EXISTING = "existing"


# ── Mode detection ──────────────────────────────────────────────────────────

def detect_mode() -> str:
    """ROUDIX_INSTALLER_MODE=fresh|existing wins (testing). Otherwise: a NixOS
    that is not the Roudix live ISO -> existing; anything else -> fresh."""
    forced = os.environ.get("ROUDIX_INSTALLER_MODE", "").strip().lower()
    if forced in (MODE_FRESH, MODE_EXISTING):
        return forced
    on_live_iso = Path("/iso/iso-cfg").is_dir() or Path("/iso-cfg").is_dir()
    if Path("/etc/NIXOS").exists() and not on_live_iso:
        return MODE_EXISTING
    return MODE_FRESH


def current_user() -> str:
    """The human behind the session: SUDO_USER / PKEXEC_UID when started as root."""
    name = os.environ.get("SUDO_USER")
    if name and name != "root":
        return name
    pk = os.environ.get("PKEXEC_UID")
    if pk and pk.isdigit():
        try:
            return pwd.getpwuid(int(pk)).pw_name
        except KeyError:
            pass
    return pwd.getpwuid(os.geteuid()).pw_name


def user_exists(name: str) -> bool:
    try:
        pwd.getpwnam(name)
        return True
    except KeyError:
        return False


def config_dir_for(username: str) -> Path:
    """~/.config/roudix of that user — where autoupdate/nh/roudix-update expect it."""
    try:
        home = Path(pwd.getpwnam(username).pw_dir)
    except KeyError:
        home = Path("/home") / username
    return home / ".config" / "roudix"


# ── Config catalog (needed BEFORE the wizard to know the hosts/questions) ───

def catalog_dir() -> Path:
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return cache / "roudix-installer" / "repo"


def prepare_catalog(log=print) -> Path | None:
    """Make hosts/<n>/local.nix.example discoverable by host_profile (it only
    knows the ISO paths by default). Prefers the user's own checkout, else a
    shallow clone of main in the cache. Sets ROUDIX_CFG_ROOT. Best effort:
    returns None (host_profile then falls back to its built-in defaults)."""
    if os.environ.get("ROUDIX_CFG_ROOT"):
        return Path(os.environ["ROUDIX_CFG_ROOT"])
    own = config_dir_for(current_user())
    if (own / "hosts").is_dir():
        os.environ["ROUDIX_CFG_ROOT"] = str(own)
        return own
    dest = catalog_dir()
    if not (dest / "hosts").is_dir():
        log(f"roudix-installer: fetching the Roudix profiles into {dest} …")
        shutil.rmtree(dest, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet", REPO_URL, str(dest)],
                check=True, stdin=subprocess.DEVNULL, timeout=180,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            log(f"roudix-installer: could not fetch the profiles ({exc}) — using defaults")
            return None
    os.environ["ROUDIX_CFG_ROOT"] = str(dest)
    return dest


# ── Facts about the machine, for the backup and the pre-flight ──────────────

@dataclass
class Facts:
    date: str = ""
    hostname: str = ""
    generation: str = ""          # e.g. system-42-link
    state_version: str = ""       # from the user's own configuration.nix, if found
    bootloader: str = ""          # grub | systemd-boot | limine | "" (unknown)
    uses_flake: bool = False
    boot_free_mib: int | None = None   # None = /boot is not a separate mount / unreadable
    store_free_gib: int | None = None
    notes: list = field(default_factory=list)


_BOOTLOADERS = (
    ("systemd-boot", re.compile(r"boot\.loader\.systemd-boot\.enable\s*=\s*(lib\.mkForce\s+)?true")),
    ("grub", re.compile(r"boot\.loader\.grub\.(enable|device|devices|efiSupport)\b")),
    ("limine", re.compile(r"boot\.loader\.limine\.enable\s*=\s*true")),
)


def _read_nix_files(etc_nixos: Path) -> str:
    chunks = []
    try:
        for p in sorted(etc_nixos.glob("*.nix"))[:20]:
            if p.name != "hardware-configuration.nix":
                chunks.append(p.read_text(errors="replace"))
    except OSError:
        pass
    return "\n".join(chunks)


def read_facts(etc_nixos: Path = Path("/etc/nixos"),
               profile: Path = Path("/nix/var/nix/profiles/system"),
               boot: Path = Path("/boot"), store: Path = Path("/nix/store")) -> Facts:
    f = Facts(date=datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    try:
        f.hostname = os.uname().nodename
    except OSError:
        pass
    try:
        f.generation = os.readlink(profile)
    except OSError:
        f.generation = ""
    text = _read_nix_files(etc_nixos)
    m = re.search(r'system\.stateVersion\s*=\s*"([^"]+)"', text)
    f.state_version = m.group(1) if m else ""
    for name, rx in _BOOTLOADERS:
        if rx.search(text):
            f.bootloader = name
            break
    f.uses_flake = (etc_nixos / "flake.nix").is_file()
    if os.path.ismount(boot):
        try:
            st = os.statvfs(boot)
            f.boot_free_mib = st.f_bavail * st.f_frsize // (1024 * 1024)
        except OSError:
            pass
    try:
        st = os.statvfs(store)
        f.store_free_gib = st.f_bavail * st.f_frsize // (1024 ** 3)
    except OSError:
        pass
    return f


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return None


def preflight(f: Facts, chosen_bootloader: str = "") -> list[tuple[str, dict]]:
    """Warnings as (message id, format args). The caller translates them —
    this module stays free of i18n so it can be tested on its own."""
    out = []
    if f.boot_free_mib is not None and f.boot_free_mib < MIN_BOOT_FREE_MIB:
        out.append(("boot_space", {"free": f.boot_free_mib, "need": MIN_BOOT_FREE_MIB}))
    if f.store_free_gib is not None and f.store_free_gib < MIN_STORE_FREE_GIB:
        out.append(("store_space", {"free": f.store_free_gib, "need": MIN_STORE_FREE_GIB}))
    old, new = _version_tuple(f.state_version), _version_tuple(ROUDIX_STATE_VERSION)
    if old and new and old < new:
        out.append(("state_version", {"old": f.state_version, "new": ROUDIX_STATE_VERSION}))
    if chosen_bootloader and f.bootloader != chosen_bootloader:
        out.append(("bootloader_change", {"old": f.bootloader or "?", "new": chosen_bootloader}))
    return out


# ── Backup ──────────────────────────────────────────────────────────────────

def backup_dir(f: Facts) -> Path:
    return BACKUP_ROOT / f"nixos-{f.date}"


def restore_text(f: Facts, dest: Path) -> str:
    """RESTORE.txt, bilingual on purpose: it is read from a rescue shell, where
    the installer's language setting no longer exists."""
    flake_cmd = (
        f"sudo nixos-rebuild boot --flake {dest}/etc-nixos#<your-host>"
        if f.uses_flake else
        f"sudo nixos-rebuild boot -I nixos-config={dest}/etc-nixos/configuration.nix"
    )
    return f"""Roudix — NixOS backup / sauvegarde NixOS
==========================================
Made on / Fait le : {f.date}
Hostname          : {f.hostname or '?'}
Previous system   : {f.generation or '?'}   (/nix/var/nix/profiles/{f.generation or '<system-N-link>'})
Bootloader before : {f.bootloader or 'unknown / inconnu'}
stateVersion      : {f.state_version or 'unknown / inconnue'}   (Roudix sets {ROUDIX_STATE_VERSION})
Flake-based       : {'yes' if f.uses_flake else 'no'}

Your previous /etc/nixos is in / Ton ancien /etc/nixos est dans :
    {dest}/etc-nixos

1) Roudix boots but you want your old system / Roudix démarre mais tu veux revenir :
   pick the previous generation in the boot menu, then run
   choisis la génération précédente dans le menu de démarrage, puis :
       sudo nixos-rebuild switch --rollback

2) The machine does not boot at all / La machine ne démarre plus :
   boot any NixOS live USB, mount your root partition on /mnt (and the ESP on /mnt/boot), then
   démarre une clé live NixOS, monte ta racine sur /mnt (et l'ESP sur /mnt/boot), puis :
       sudo nixos-enter --root /mnt
       {flake_cmd}
   This puts your previous configuration (and bootloader) back.
   Cela remet ton ancienne configuration (et ton bootloader).

3) To forget Roudix for good, restore the files / Pour oublier Roudix, remets les fichiers :
       sudo cp -a {dest}/etc-nixos/. /etc/nixos/
"""


def backup_command(f: Facts, restore_file: Path) -> list[str]:
    """One privileged shell command doing the whole backup (a single polkit
    prompt). /etc/nixos is copied as-is, including hardware-configuration.nix."""
    dest = backup_dir(f)
    script = (
        f'set -e; mkdir -p "{dest}/etc-nixos"; '
        f'cp -a /etc/nixos/. "{dest}/etc-nixos/"; '
        f'cp "{restore_file}" "{dest}/RESTORE.txt"; chmod -R go-w "{dest}"; '
        f'echo "{dest}"'
    )
    return ["bash", "-c", script]

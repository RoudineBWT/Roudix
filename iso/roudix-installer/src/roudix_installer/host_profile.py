"""
Per-host question filtering — same contract as roudix-installer.sh.

A host opts in by putting this exact line in hosts/<name>/local.nix.example:

    # roudix-installer: only-listed

Then the wizard only shows the options that appear in that file (commented
or not); everything else is hidden and keeps the host's configuration.nix
defaults. Hosts without the marker (hosts/roudix) show every question, as
before. config_gen's substitutions are already no-ops for keys absent from
the example, so hiding a row never writes anything for it.
"""
import os
import re
from pathlib import Path

MARKER = "# roudix-installer: only-listed"
FIXED = "roudix-installer: fixed"   # trailing comment on a line = never asked, kept verbatim
_KEY = re.compile(r"^\s*#?\s*([A-Za-z_][\w.\-]*)\s*=")


def _roots():
    # isoImage.contents (iso/iso-configuration.nix, target "/iso-cfg") writes
    # into the ISO image itself, which the live system mounts on /iso — so the
    # embedded config is normally at /iso/iso-cfg. /iso-cfg is kept as a
    # fallback for setups where it is bind-mounted or copied to the root.
    roots = [Path("/iso/iso-cfg"), Path("/iso-cfg"), Path("/mnt/etc/nixos")]
    # Testing outside an ISO (nix run from a repo checkout): point this at the
    # checkout so hosts/<name>/ can be found — see ROUDIX_INSTALLER_DRY_RUN.
    override = os.environ.get("ROUDIX_CFG_ROOT")
    if override:
        roots.insert(0, Path(override))
    try:  # running from a repo checkout: iso/roudix-installer/src/roudix_installer/
        roots.append(Path(__file__).resolve().parents[4])
    except IndexError:
        pass
    return roots


def available_hosts():
    """Names of the installable hosts (hosts/<name>/ with a configuration.nix),
    'roudix' first. Looks in the same places as listed_options(); falls back to
    the two known profiles if nothing can be found, so the menu is never empty."""
    found = set()
    for root in _roots():
        hosts_dir = root / "hosts"
        if not hosts_dir.is_dir():
            continue
        for d in hosts_dir.iterdir():
            if d.is_dir() and not d.name.startswith(".") and (d / "configuration.nix").is_file():
                found.add(d.name)
    if not found:
        found = {"roudix", "nixie"}
    return sorted(found, key=lambda n: (n != "roudix", n))


def find_config_root(hostname: str):
    """Root of the config tree (the one holding hosts/<hostname>/local.nix.example),
    or None if it can't be found anywhere."""
    if not hostname or "/" in hostname or hostname.startswith("."):
        return None
    for root in _roots():
        if (root / "hosts" / hostname / "local.nix.example").is_file():
            return root
    return None


def find_example(hostname: str):
    """Path of hosts/<hostname>/local.nix.example in the first place it exists,
    or None if it can't be found anywhere."""
    root = find_config_root(hostname)
    return None if root is None else root / "hosts" / hostname / "local.nix.example"


def listed_options(hostname: str):
    """Set of option names listed for this host, or None = show everything
    (no marker, or its local.nix.example can't be found — fail open)."""
    example = find_example(hostname)
    if example is None:
        return None
    lines = example.read_text(encoding="utf-8", errors="replace").splitlines()
    if not any(l.startswith(MARKER) for l in lines):
        return None
    return {m.group(1) for l in lines if FIXED not in l and (m := _KEY.match(l))}


def restore_fixed_lines(example_text: str, patched_text: str) -> str:
    """Put every `# roudix-installer: fixed` line of the example back verbatim
    (the wizard's own defaults must never overwrite them)."""
    if not any(l.startswith(MARKER) for l in example_text.splitlines()):
        return patched_text
    for line in example_text.splitlines():
        m = _KEY.match(line)
        if m and FIXED in line:
            pattern = re.compile(rf"(?m)^[ \t]*#?[ \t]*{re.escape(m.group(1))}[ \t]*=.*$")
            patched_text = pattern.sub(lambda _m, _l=line: _l, patched_text, count=1)
    return patched_text

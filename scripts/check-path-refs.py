#!/usr/bin/env python3
"""
check-path-refs.py — flag repo-relative path references in .py/.sh files
that point at files/dirs which don't actually exist.

Why: scripts under pkgs/ and iso/roudix-installer/ hardcode paths into
the Roudix flake tree (modules/..., hosts/...) either as plain string
literals (bash, or a Python f-string/plain string) or as a chain of
Path("...") / "part" / "part" segments. When the tree gets reorganized
(a file moves into a subdirectory, gets renamed, ...) these references
silently go stale — the code doesn't crash, it just quietly does the
wrong thing (see: boot.local.nix moving into modules/system/boot/,
which broke iso/roudix-installer's config_gen.py without any error).

This script re-derives every such reference it can find and checks it
against the actual tree, so that kind of drift shows up as a CI failure
instead of a support request three weeks later.

Usage:
    python3 scripts/check-path-refs.py            # scan the whole repo
    python3 scripts/check-path-refs.py --paths pkgs iso/roudix-installer

Exit status: 0 if every reference resolves, 1 otherwise (for CI gating).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Only files under these top-level directories are considered "the repo
# tree" for existence-checking purposes — this is also used as the anchor
# that tells a candidate string apart from an unrelated path (a runtime
# path like /mnt/etc/nixos, a URL, a package name, ...).
ANCHORS = ("modules", "hosts", "pkgs", "iso", "docs", "dotfiles")

# Extensions worth checking. Deliberately narrow: catching every quoted
# string in a script would drown real hits in noise (flags, package
# names, unrelated strings that happen to contain a slash).
CHECKED_SUFFIXES = (".nix", ".example", ".svg", ".policy", ".png", ".md")

# Individual reference strings that are known-good but can't be resolved
# by looking at the tree on disk (generated at build/install time, or a
# template path pattern rather than a literal one). Add an entry here
# with a one-line reason if check-path-refs flags a legitimate case.
ALLOWLIST: set[str] = set()

DEFAULT_SCAN_DIRS = ("pkgs", "iso/roudix-installer", "roudix-installer.sh")

# Matches a plain quoted literal path, e.g. "modules/system/boot.local.nix"
LITERAL_RE = re.compile(
    r'"((?:%s)/[A-Za-z0-9_.\-/]*\.(?:%s))"'
    % ("|".join(ANCHORS), "|".join(s.lstrip(".") for s in CHECKED_SUFFIXES))
)

# Matches a chained Path("...") / "part" / "part" construction (2+ parts),
# e.g.  config_root / "modules" / "system" / "boot.local.nix"
CHAIN_RE = re.compile(r'((?:/\s*"[^"/]+"\s*){2,})')
CHAIN_PART_RE = re.compile(r'"([^"/]+)"')

# Matches a bare shell path used as a plain word, e.g. in a for-loop list
# or a cp/test command — anchored the same way as LITERAL_RE but without
# requiring quotes (bash word-splitting doesn't need them).
BARE_SHELL_RE = re.compile(
    r'(?<![\w./])((?:%s)/[A-Za-z0-9_.\-/]*\.(?:%s))'
    % ("|".join(ANCHORS), "|".join(s.lstrip(".") for s in CHECKED_SUFFIXES))
)


def find_candidates(text: str) -> set[str]:
    found: set[str] = set()

    found.update(LITERAL_RE.findall(text))
    found.update(BARE_SHELL_RE.findall(text))

    for chain in CHAIN_RE.findall(text):
        parts = CHAIN_PART_RE.findall(chain)
        if not parts:
            continue
        candidate = "/".join(parts)
        if candidate.startswith(ANCHORS) or any(
            candidate.startswith(a + "/") for a in ANCHORS
        ):
            found.add(candidate)
        # Also try anchoring from each position, in case the chain's
        # first segment isn't an anchor itself (e.g. a variable holding
        # a sub-path joined with more literal parts afterwards).
        for i in range(len(parts)):
            sub = "/".join(parts[i:])
            if any(sub == a or sub.startswith(a + "/") for a in ANCHORS):
                found.add(sub)

    return {c for c in found if c.endswith(CHECKED_SUFFIXES)}


def scan_file(path: Path) -> list[str]:
    text = path.read_text(errors="ignore")
    missing = []
    for candidate in sorted(find_candidates(text)):
        if candidate in ALLOWLIST:
            continue
        if not (REPO_ROOT / candidate).exists():
            missing.append(candidate)
    return missing


def iter_targets(scan_dirs: list[str]) -> list[Path]:
    targets: list[Path] = []
    for entry in scan_dirs:
        p = REPO_ROOT / entry
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets.extend(sorted(p.rglob("*.py")))
            targets.extend(sorted(p.rglob("*.sh")))
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        nargs="+",
        default=list(DEFAULT_SCAN_DIRS),
        help="Files/directories to scan (default: %(default)s)",
    )
    args = parser.parse_args()

    targets = iter_targets(args.paths)
    if not targets:
        print("No .py/.sh files found under the given paths.", file=sys.stderr)
        return 1

    had_errors = False
    for path in targets:
        missing = scan_file(path)
        if missing:
            had_errors = True
            rel = path.relative_to(REPO_ROOT)
            print(f"\n{rel}:")
            for m in missing:
                print(f"  ✗ {m}  (not found)")

    if had_errors:
        print(
            "\nSome referenced paths don't exist on disk. If a hit above is "
            "a false positive (a build-time/runtime-only path), add it to "
            "ALLOWLIST in scripts/check-path-refs.py with a one-line reason.",
            file=sys.stderr,
        )
        return 1

    print(f"OK — checked {len(targets)} file(s), all path references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

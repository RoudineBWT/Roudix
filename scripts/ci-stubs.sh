#!/usr/bin/env bash
# ci-stubs.sh — create / remove throw-away stubs for the machine-local files
# the flake needs in order to evaluate (they are gitignored, so a fresh
# checkout — CI, or a clone you never installed — doesn't have them).
#
#   scripts/ci-stubs.sh create    # write the MISSING stubs (files only)
#   scripts/ci-stubs.sh remove    # delete exactly the stubs `create` wrote
#
# Use it with a `path:` flake reference (`nix eval path:.#...`), exactly like
# `nh os switch path:$NH_FLAKE`: unlike `.#`, `path:` also sees gitignored /
# untracked files, so real local files work as they are and stubs are seen
# without touching the git index. (Touching the index would be a trap here:
# gitwatch runs `git add --all`, and would commit an intent-to-add file.)
#
# Safe on a real machine: a file that already exists is NEVER touched, and
# `remove` only deletes what `create` recorded.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
LIST="$(git rev-parse --git-dir)/ci-stubs.list"   # inside .git: never tracked

HW_STUB='{ config, lib, pkgs, modulesPath, ... }:

{
  imports = [ (modulesPath + "/installer/scan/not-detected.nix") ];

  boot.initrd.availableKernelModules = [ "xhci_pci" "ahci" "nvme" "usbhid" "sd_mod" ];
  boot.initrd.kernelModules = [ ];
  boot.kernelModules = [ "kvm-intel" ];
  boot.extraModulePackages = [ ];

  fileSystems."/" = {
    device = "/dev/disk/by-label/nixos";
    fsType = "ext4";
  };

  swapDevices = [ ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.intel.updateMicrocode = lib.mkDefault true;
}'

create() {
  touch "$LIST"   # append, never truncate: a 2nd `create` must not forget the 1st one's stubs
  for dir in hosts/*/; do
    host="$(basename "$dir")"
    [ -f "hosts/$host/configuration.nix" ] || continue

    if [ ! -f "hosts/$host/hardware-configuration.nix" ]; then
      printf '%s\n' "$HW_STUB" > "hosts/$host/hardware-configuration.nix"
      echo "hosts/$host/hardware-configuration.nix" >> "$LIST"
      echo "stub: hosts/$host/hardware-configuration.nix"
    fi

    # flake.nix does `import ./hosts/<host>/username.nix` (a plain string).
    if [ ! -f "hosts/$host/username.nix" ]; then
      echo '"ci-runner"' > "hosts/$host/username.nix"
      echo "hosts/$host/username.nix" >> "$LIST"
      echo "stub: hosts/$host/username.nix"
    fi
  done
}

remove() {
  [ -f "$LIST" ] || { echo "no stubs recorded, nothing to remove"; return 0; }
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rm -f -- "$f"
    echo "removed: $f"
  done < "$LIST"
  rm -f -- "$LIST"
}

case "${1:-}" in
  create) create ;;
  remove) remove ;;
  *) echo "usage: $0 create|remove" >&2; exit 2 ;;
esac

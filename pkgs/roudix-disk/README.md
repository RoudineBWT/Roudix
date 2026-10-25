# roudix-disk

GTK4/libadwaita app (Python) to **mount, unmount-by-config and format extra disks on Roudix**.
Inspired by nix-disk (Rust), rewritten in Python for how Roudix actually lays out its disks.

## What it does

- Lists disks/partitions (`lsblk`), including whole-disk filesystems and empty disks.
- Assign / change / remove a **mount point** for a partition (default `/media/<label>`).
  Sensible options per filesystem: `ext4` → `defaults,nofail,x-gvfs-show`;
  `btrfs` → + `compress=zstd:1,noatime` (+ `ssd,discard=async` on SSD/NVMe, same defaults as
  `roudix-installer`'s `btrfs_patch.py`); `ntfs` → written as `ntfs3` (kernel driver) with your uid/gid;
  `exfat`/`vfat` → uid/gid/umask.
- **Format** a whole disk (GPT + one partition, `ext4` or `btrfs`), owned by your user, then offers
  to mount it right away.
- Detects configured disks that are no longer connected and offers to drop them.
- Apply = write `hosts/<hostname>/hardware-configuration.nix` → `nh os switch|boot --elevation-strategy pkexec`
  (same mechanism as `roudix-hw-sync` / `roudix-kernel-switcher`).

## How it fits Roudix

| Roudix fact | What roudix-disk does |
|---|---|
| Config lives in `~/.config/roudix` (`NH_FLAKE`), per-host dir `hosts/<hostname>/` | Edits `hosts/<hostname>/hardware-configuration.nix` there (`ROUDIX_HOST` / `NH_FLAKE` override) |
| `/`, `/home`, `/nix`, `/var/log` are btrfs subvolumes (`@`, `@home`, `@nix`, `@log`) on one filesystem, `/boot` is a 4 G ESP | Those blocks are **never rewritten** (byte-identical, tested); their partitions show as 🔒 *System* and can't be formatted/edited |
| Other apps escalate with `pkexec` and rebuild with `nh` | Same |
| Apps are plain `pkgs/<name>` + gettext `po/` | Same layout, `fr.po` provided |

Extra disks are written into one marker-delimited block at the end of the file:

```nix
  # >>> roudix-disk (managed block — …)
  fileSystems."/media/Games" = {
    device = "/dev/disk/by-uuid/…";
    fsType = "ext4";
    options = [ "defaults" "nofail" "x-gvfs-show" ];
  };
  # <<< roudix-disk
```

Entries it doesn't fully understand (nfs, bind mounts, `neededForBoot`, `mkDefault`-wrapped…) are left untouched.
Plain by-uuid entries added by hand or by nix-disk are adopted into the managed block on the first apply.

## Safety

- Backup of the config before every write (`~/.local/state/roudix-disk/backups`, last 10), syntax check with
  `nix-instantiate --parse` when available, atomic replace.
- If the rebuild fails, the previous file is **restored automatically** and your edits stay in the UI.
- Formatting needs typing the device name; the root helper (`pkexec roudix-disk --helper-format …`)
  re-validates everything itself: whole-disk node only, nothing mounted/swapped anywhere on it
  (LUKS/LVM children included), label/fs whitelisted, caller uid taken from `PKEXEC_UID`.
- Mount points: strict charset, nothing under `/boot /nix /etc /usr /run …`, no duplicates.

## Wire it into the flake (3 small edits)

`flake.nix`:
```nix
roudix-disk = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-disk {};
# …and add `roudix-disk` to the `inherit` list of baseSpecialArgs
```
`modules/home/common.nix`: add `roudix-disk` to the argument set (line 1) and to the package list next to
`roudix-hw-sync`.

Runtime tools (util-linux, parted, e2fsprogs, btrfs-progs, systemd, coreutils) are added to the wrapper's PATH by
`default.nix`; `nh`, `pkexec` and `nix-instantiate` come from the system.

## Tests

```
python3 tests/test_core.py [path/to/roudix/hosts]          # core: parser/writer/lsblk/helper (no GTK)
xvfb-run -a python3 tests/smoke_gui.py <hardware-configuration.nix> out.png   # GUI with fake lsblk + fake rebuilds
```

## Differences from nix-disk

- Its writer deletes every `fileSystems` block except `/ /boot /boot/efi /nix /nix/store` and regenerates the rest,
  which would drop Roudix's `/home` and `/var/log` subvolume mounts. roudix-disk only touches its own block.
- Targets `hosts/<host>/hardware-configuration.nix`, not `/etc/nixos/hardware-configuration.nix`.
- Whole-disk filesystems, `ntfs3`, btrfs defaults, automatic rollback, `nh`-based rebuild, btrfs formatting.

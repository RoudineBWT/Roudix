# Secure Boot, TPM 2.0 and EAC Linux v2

Everything on this page is **opt-in and off by default**. A machine without
Secure Boot or a TPM keeps working exactly as before.

## Why

Epic's Easy Anti-Cheat Linux v2 (announced 2026-10-14) has no kernel driver.
It checks, when a protected game starts, that the machine booted a kernel it
can trust: Secure Boot on, TPM 2.0 with measured boot, a kernel and modules
signed with a **well-known key**, kernel lockdown, no kexec, IOMMU on, BPF LSM.
Epic's list of well-known keys has Fedora, Universal Blue (Bazzite), Canonical,
Debian, openSUSE, … and Microsoft (which signs shim). It does not have a
Roudix key, nor CachyOS' or xddxdd's: a kernel built by Nix and signed with
your own key does not qualify, whatever its config.

## What Roudix does about it

Two independent options:

| Option | What it does |
|---|---|
| `roudix.boot.secureBoot.enable` | Signs **Limine** with sbctl, so the normal Roudix entry (your kernel, the Limine wallpaper, your other OS entries) boots with Secure Boot ON. Keys are yours, enrolled next to Microsoft's. |
| `roudix.boot.eac.enable` | Adds a separate **"NixOS EAC"** entry ([eacnix](https://github.com/samos667/eacnix)): NixOS userspace on Fedora's (or Bazzite's OGC) signed kernel, through Fedora's Microsoft-signed shim and grub. Your normal entry is not changed. |

`roudix.boot.eac.vendor` = `"fedora"` (default, nothing to enroll) or
`"bazzite"` (needs Universal Blue's key enrolled once as a MOK:
`sudo eacnix-enroll-mok`, then `sudo eac-reboot` and "Enroll MOK" in the blue
screen). `addToBootOrder` lists the entry in the firmware boot menu;
`generations` is how many EAC generations stay on the ESP.

Epic's FAQ explicitly allows a separate compliant boot entry for protected
games, and your own keys in the Secure Boot `db` for the other entries.

### Why Limine stays

lanzaboote (the NixOS Secure Boot tool) is built on systemd-boot, which has no
wallpaper or theming support, so switching to it would drop the Roudix boot
wallpaper. nixpkgs' Limine module can sign Limine itself, so Roudix keeps
Limine and signs it instead of changing bootloader.

## Limits — read before relying on it

- **Not confirmed by Epic.** No game uses EAC Linux v2 yet (Fortnite is the
  pilot). eacnix follows Epic's *published* requirements; whether EAC accepts
  NixOS userspace on another distribution's signed kernel is an open question.
- **eacnix is young** (a handful of commits, one maintainer, no license file at
  the pinned commit, hardware-tested on one machine). Roudix pins it to an
  audited commit in `flake.nix`; bump it only after reading the diff.
- **The EAC entry is a different kernel.** Your Roudix kernel choice
  (kernel switcher, AMD/NVIDIA split) does not apply there; no custom kernel
  patches; locally built kernel modules (v4l2loopback virtual camera, xone,
  ZFS…) are left out of that entry, with a warning at build time; hibernation
  is blocked by lockdown.
- **NVIDIA** is not wired by Roudix. With a Bazzite vendor kernel set
  `eacnix.nvidia.enable = true;` yourself in `local.nix` (open modules, Turing
  and newer, only tested in VMs so far).
- **Vendor pins age.** Kernel, grub and shim are pinned together and must be
  bumped together; Bazzite images are pruned from ghcr.io after a few months.
- **Other OS entries** chainloaded by Limine (`boot.local.nix`) must be signed
  to boot with Secure Boot on. Windows' boot manager and shim-based distros
  (Fedora, openSUSE, …) are; a custom or unsigned loader is not (sign it with
  `sbctl sign`, or leave Secure Boot off for that OS).

## Turning it on safely (existing Limine install)

Nothing here changes your bootloader. Do the steps in this order, and stop at
any step that does not behave as described.

1. **Prepare a way back.** Back up the ESP (`sudo tar -C /boot -cf ~/esp-backup.tar .`),
   have a live USB at hand, and know how to open the firmware setup.
2. **Create the keys** (Secure Boot still OFF in the firmware):
   `sudo sbctl create-keys` (stored in `/var/lib/sbctl`; back them up).
3. **Put the firmware in Setup Mode** (the menu entry to clear or reset the
   Secure Boot keys; it differs per board). Secure Boot stays disabled.
4. **Enroll your keys with Microsoft's:** `sudo sbctl enroll-keys -m -f`
   (`-m` keeps Microsoft's certificates, needed by Fedora's shim and most GPU
   firmware; `-f` keeps the firmware's built-in ones). `sudo sbctl status`
   should now show Setup Mode off.
5. **Sign Limine:** in `hosts/<host>/local.nix` set
   `roudix.boot.secureBoot.enable = true;`, then rebuild. Check
   `sudo sbctl verify`: the Limine EFI files must show as signed (kernels are
   verified by Limine through the hashes in its enrolled config, not by
   signature).
6. **Reboot with Secure Boot still OFF** and check it boots normally.
7. **Turn Secure Boot ON in the firmware** and reboot. If the machine does not
   boot, disable Secure Boot in the firmware: Roudix boots as before. The ESP
   backup and the live USB cover the rest.
8. **Optional — EAC entry:** set `roudix.boot.eac.enable = true;`
   (`vendor = "bazzite"` if you want the OGC kernel), rebuild, then
   `sudo eac-reboot` to boot it once. In it, `sudo eacnix-check` checks every
   requirement against the TPM event log. The next reboot returns to the
   normal entry.

Some boards report Secure Boot as enabled but still run unsigned images
(MSI's "Image Execution Policy: Always Execute", for example): `eacnix-check`
warns about it.

## Undoing it

Set both options back to `false` and rebuild. To go back to a firmware without
Secure Boot, disable it in the firmware setup; `sbctl` keys stay in
`/var/lib/sbctl` and can be removed from the firmware (clear the keys) if you
no longer want them.

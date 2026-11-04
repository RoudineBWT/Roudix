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
| `roudix.boot.secureBoot.enable` | Signs the bootloader with your own sbctl keys, so the normal Roudix entry boots with Secure Boot ON: **Limine** (signed with sbctl; your kernel, the Limine wallpaper and your other OS entries stay) or **systemd-boot** (through lanzaboote: signed systemd-boot plus one signed unified kernel image per generation). Same keys and same steps for both, enrolled next to Microsoft's. |
| `roudix.boot.eac.enable` | Adds a separate **"NixOS EAC"** entry ([eacnix](https://github.com/samos667/eacnix)): NixOS userspace on Fedora's (or Bazzite's OGC) signed kernel, through Fedora's Microsoft-signed shim and grub. Your normal entry is not changed. |

`roudix.boot.eac.vendor` = `"fedora"` (default, nothing to enroll) or
`"bazzite"` (needs Universal Blue's key enrolled once as a MOK:
`sudo eacnix-enroll-mok`, then `sudo eac-reboot` and "Enroll MOK" in the blue
screen). `addToBootOrder` lists the entry in the firmware boot menu;
`generations` is how many EAC generations stay on the ESP.

Epic's FAQ explicitly allows a separate compliant boot entry for protected
games, and your own keys in the Secure Boot `db` for the other entries.

### Limine or systemd-boot

Both bootloaders get the same Secure Boot support; pick with
`roudix.boot.bootloader`.

- **Limine** (default): themed (Roudix wallpaper), multi-OS entries, and the
  only one that can carry the EAC entry with Secure Boot on. nixpkgs' Limine
  module signs Limine itself; the kernels are checked by Limine through the
  hashes in its enrolled config.
- **systemd-boot** (minimal, no wallpaper or theming): signed by lanzaboote, the
  NixOS Secure Boot tool built on systemd-boot. lanzaboote replaces
  systemd-boot's own installer and writes one signed unified kernel image per
  generation to `EFI/Linux`; the kernels and initrds it keeps under `EFI/nixos`
  are checked by that signed stub through hashes. The number of generations
  kept follows `boot.loader.systemd-boot.configurationLimit`. Because lanzaboote
  takes over the installer eacnix hooks into, the EAC entry is not available
  with systemd-boot and Secure Boot (a build assertion says so).

## Limits — read before relying on it

- **Not confirmed by Epic.** No game uses EAC Linux v2 yet (Fortnite is the
  pilot). eacnix follows Epic's *published* requirements; whether EAC accepts
  NixOS userspace on another distribution's signed kernel is an open question.
- **eacnix is young** (a handful of commits, one maintainer, no license file at
  the pinned commit, hardware-tested on one machine). Roudix pins it to an
  audited commit in `flake.nix`; bump it only after reading the diff.
- **UEFI only.** On a legacy BIOS machine (`roudix.boot.biosDevice`, or an ISO
  booted without `/sys/firmware/efi`) there is no Secure Boot: the options are
  hidden in the installers and `roudix-switcher`, and the module refuses them.
- **systemd-boot + Secure Boot is not hardware-tested by Roudix yet.** Keep the
  ESP backup and the live USB of the steps below at hand, and run
  `roudix-secureboot verify` before turning Secure Boot on in the firmware.
- **The EAC entry is a different kernel.** Your Roudix kernel choice
  (kernel switcher, AMD/NVIDIA split) does not apply there; no custom kernel
  patches; locally built kernel modules (v4l2loopback virtual camera, xone,
  ZFS…) are left out of that entry, with a warning at build time; hibernation
  is blocked by lockdown.
- **NVIDIA** needs the Bazzite vendor: Fedora ships no signed NVIDIA modules,
  Universal Blue does. With `hardware.myGpu = "nvidia"` Roudix turns on
  `eacnix.nvidia` for you (open modules when `hardware.nvidiaOpen` is on,
  i.e. Turing and newer; the proprietary ones, pre-Turing only, run on Bazzite's
  LTS kernel), and refuses `vendor = "fedora"` with an NVIDIA GPU. The
  installers and `roudix-switcher` pick Bazzite by themselves on NVIDIA.
  Tested upstream only in VMs without a GPU; hybrid laptops (PRIME) are not
  covered and raise a warning.
- **Vendor pins age.** Kernel, grub and shim are pinned together and must be
  bumped together; Bazzite images are pruned from ghcr.io after a few months.
- **Other OS entries** chainloaded by Limine (`boot.local.nix`) must be signed
  to boot with Secure Boot on. Windows' boot manager and shim-based distros
  (Fedora, openSUSE, …) are; a custom or unsigned loader is not (sign it with
  `sbctl sign`, or leave Secure Boot off for that OS).

## Installer and roudix-switcher

The same options are exposed outside `local.nix`, all off by default:

- **GTK installer and `roudix-installer.sh`** ask for them on the options page:
  "Secure Boot (sign the bootloader)" with Limine or systemd-boot, and, only with
  Limine, "EAC Linux v2 boot entry (experimental)" and, once that one is on, the
  EAC kernel (Fedora or Bazzite OGC). With Secure Boot on, the sbctl keys are created on the new
  system during the install (`autoGenerateKeys`). **Enrolling them in the
  firmware stays manual**, as described below. For a Bazzite kernel the MOK
  enrollment (`sudo eacnix-enroll-mok`) is also done after the install.
- **`roudix-switcher`** has a "Secure Boot and EAC (experimental)" group on the
  System page with the same two switches and the EAC kernel choice (the EAC
  ones only with Limine; the Secure Boot switch works with both bootloaders). Turning Secure Boot on there rebuilds with signing enabled, so create
  the sbctl keys first (`roudix-secureboot create-keys`).

## Turning it on safely (existing install, Limine or systemd-boot)

`roudix-secureboot` is installed on every system and walks you through
this: run it without arguments to see where you are (keys, firmware mode,
Secure Boot, the bootloader's signature, and the EAC entry with Limine) and what to do next. Nothing here
changes your bootloader. Do the steps in this order, and stop at any step that
does not behave as described.

1. **Prepare a way back.** Back up the ESP (`sudo tar -C /boot -cf ~/esp-backup.tar .`),
   have a live USB at hand, and know how to open the firmware setup.
2. **Create the keys** (Secure Boot still OFF in the firmware):
   `roudix-secureboot create-keys` (stored in `/var/lib/sbctl`; back them up).
3. **Put the firmware in Setup Mode.** In the firmware setup, clear the Secure
   Boot keys (the entry differs per board; don't choose "restore factory keys").
   Secure Boot stays disabled. `roudix-secureboot firmware` reboots into the setup.
4. **Enroll your keys with Microsoft's:** `roudix-secureboot enroll`
   (it runs `sbctl enroll-keys -m -f`: `-m` keeps Microsoft's certificates, needed
   by Fedora's shim and most GPU firmware; `-f` keeps the firmware's built-in
   ones, and it refuses to run outside Setup Mode). `roudix-secureboot` should
   now report your keys as enrolled.
5. **Sign the bootloader:** in `hosts/<host>/local.nix` set
   `roudix.boot.secureBoot.enable = true;`, then rebuild. Check with
   `roudix-secureboot verify`. With Limine, Limine's EFI file must be signed
   (kernels are verified by Limine through the hashes in its enrolled config,
   not by signature). With systemd-boot, systemd-boot and the kernel images in
   `EFI/Linux` must be signed (the kernels and initrds under `EFI/nixos` are
   checked by the signed stub through hashes). The other files `sbctl verify`
   lists as "not signed" are expected.
6. **Reboot with Secure Boot still OFF** and check it boots normally.
7. **Turn Secure Boot ON in the firmware** (`roudix-secureboot firmware`) and
   reboot. If the machine does not boot, disable Secure Boot in the firmware:
   Roudix boots as before. The ESP backup and the live USB cover the rest.
8. **Optional — EAC entry (Limine only):** set `roudix.boot.eac.enable = true;`
   (`vendor = "bazzite"` if you want the OGC kernel), rebuild, then
   `sudo eac-reboot` to boot it once. In it, `sudo eacnix-check` checks every
   requirement against the TPM event log. The next reboot returns to the
   normal entry.

Some boards report Secure Boot as enabled but still run unsigned images
(MSI's "Image Execution Policy: Always Execute", for example): `eacnix-check`
warns about it.

If Windows is installed with BitLocker, changing the Secure Boot keys can make
it ask for its recovery key: `roudix-secureboot` reminds you before it enrolls.
The tool also runs without arguments from a normal user (it asks for sudo) and
`-y` skips its confirmations.

## Undoing it

Set both options back to `false` and rebuild. To go back to a firmware without
Secure Boot, disable it in the firmware setup; `sbctl` keys stay in
`/var/lib/sbctl` and can be removed from the firmware (clear the keys) if you
no longer want them.

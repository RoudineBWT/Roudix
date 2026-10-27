{ lib, config, pkgs, ... }:
# Secure Boot + EAC Linux v2 boot path — everything here is OPT-IN (off by
# default), so machines without Secure Boot / TPM 2.0 are not affected.
# See docs/secure-boot-eac.md for the why, the limits and the safe way to
# turn it on.
#
#  * roudix.boot.secureBoot  signs Limine with sbctl, so the normal Roudix
#                            entry (your kernel, the Limine wallpaper, other
#                            OS entries) keeps booting with Secure Boot ON.
#  * roudix.boot.eac         adds eacnix's "NixOS EAC" entry: Fedora's or
#                            Bazzite's signed kernel behind Fedora's
#                            Microsoft-signed shim, measured by the TPM.
let
  cfg = config.roudix.boot;
  limine = cfg.bootloader == "limine";
in
{
  options.roudix.boot = {
    secureBoot = {
      enable = lib.mkOption {
        description = ''
          Sign the Limine binary with sbctl so the machine can boot with UEFI
          Secure Boot enabled. Limine only (with systemd-boot there is no
          signing here). Needs the keys created and enrolled BEFORE the first
          rebuild with this on — follow docs/secure-boot-eac.md, in this
          order: `sbctl create-keys`, firmware Setup Mode,
          `sbctl enroll-keys -m -f`, rebuild, check `sbctl verify`, and only
          then enable Secure Boot in the firmware.
        '';
        type = lib.types.bool;
        default = false;
      };

      autoGenerateKeys = lib.mkOption {
        description = ''
          Generate the sbctl keys in /var/lib/sbctl at install time when none
          exist yet (same as running `sbctl create-keys`). Enrolling them in
          the firmware stays manual (`sbctl enroll-keys -m -f`).
        '';
        type = lib.types.bool;
        default = false;
      };
    };

    eac = {
      enable = lib.mkOption {
        description = ''
          Add a separate "NixOS EAC" boot entry meant for Easy Anti-Cheat
          Linux v2 games (eacnix). It boots NixOS userspace on a kernel signed
          by Fedora or Universal Blue; your normal entry and kernel are not
          touched. Needs UEFI, Secure Boot ON in the firmware and a TPM 2.0.
          Whether EAC accepts this setup is not confirmed by Epic yet.
        '';
        type = lib.types.bool;
        default = false;
      };

      vendor = lib.mkOption {
        description = ''
          Whose signed kernel the EAC entry boots: "fedora" (nothing to
          enroll) or "bazzite" (the OGC kernel; needs Universal Blue's key
          enrolled once as a MOK with `sudo eacnix-enroll-mok`).
        '';
        type = lib.types.enum [ "fedora" "bazzite" ];
        default = "fedora";
      };

      addToBootOrder = lib.mkOption {
        description = ''
          List "NixOS EAC" in the firmware boot menu (appended behind another
          OS entry; your default stays first). Without it, reach the entry
          with `sudo eac-reboot` (one-shot).
        '';
        type = lib.types.bool;
        default = false;
      };

      generations = lib.mkOption {
        description = "EAC generations kept on the ESP, for rollback.";
        type = lib.types.ints.positive;
        default = 3;
      };
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [

    # ── Secure Boot (Limine signed with sbctl) ────────────────────────────
    (lib.mkIf cfg.secureBoot.enable {
      assertions = [
        {
          assertion = limine;
          message = "roudix.boot.secureBoot.enable only supports roudix.boot.bootloader = \"limine\" (Limine is signed with sbctl).";
        }
      ];

      boot.loader.limine.secureBoot = lib.mkIf limine {
        enable = true;
        autoGenerateKeys = cfg.secureBoot.autoGenerateKeys;
      };

      environment.systemPackages = [ pkgs.sbctl ];
    })

    # ── EAC Linux v2 boot entry (eacnix) ──────────────────────────────────
    (lib.mkIf cfg.eac.enable {
      eacnix = {
        enable = true;
        vendor = cfg.eac.vendor;
        boot = {
          generations = cfg.eac.generations;
          addToBootOrder = cfg.eac.addToBootOrder;
          # eacnix hooks systemd-boot's installer by itself; for Limine we do
          # it below, since nixpkgs' Limine module has its own hook.
          install = !limine;
        };
      };

      # Limine: install/refresh the EAC boot path right after Limine's own
      # install. A failure (full ESP, usually) only warns: the previous EAC
      # entries keep working and the switch is not failed over a secondary path.
      boot.loader.limine.extraInstallCommands = lib.mkIf limine (lib.mkAfter ''
        if ! ${config.system.build.eacnix.installCommand}; then
          echo "warning: eacnix: the eac boot path was not updated (see above)." >&2
        fi
      '');

      assertions = [
        {
          assertion = cfg.eac.addToBootOrder -> config.boot.loader.efi.canTouchEfiVariables;
          message = "roudix.boot.eac.addToBootOrder needs boot.loader.efi.canTouchEfiVariables (without it the firmware entry is never created).";
        }
      ];

      warnings =
        lib.optional (!cfg.secureBoot.enable) ''
          roudix.boot.eac.enable is on but roudix.boot.secureBoot.enable is off.
          EAC Linux v2 needs Secure Boot ON in the firmware, and an unsigned
          Limine cannot boot with Secure Boot on. Enable roudix.boot.secureBoot
          (docs/secure-boot-eac.md) or the normal entry stops booting the day
          you turn Secure Boot on.
        ''
        ++ lib.optional limine ''
          roudix.boot.eac: with Limine, the "eac" specialisation also shows in
          Limine's menu. Do NOT boot it from there (that runs the vendor kernel
          behind Limine, which EAC rejects): use `sudo eac-reboot` or the
          "NixOS EAC" firmware entry.
        '';
    })
  ]);
}

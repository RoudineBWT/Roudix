{ lib, config, ... }:
let
  cfg = config.roudix.boot.hibernation;
  swap = import ./hibernation-swap.nix;
  resumeDevice = swap.resumeDevice config.swapDevices;
  # An explicit boot.resumeDevice (set by hand or by the installer) means the
  # user already made a choice: never mask hibernation behind their back.
  resumeDeclared = config.boot.resumeDevice != "";
in
{
  options.roudix.boot.hibernation.enable = lib.mkOption {
    description = ''
      Enable system hibernation (S4 / suspend-to-disk).

      Off by default: nixos-generate-config fills swapDevices but never
      boot.resumeDevice, so without it the kernel has no resume= and a
      "hibernate" ends in a cold boot with the session lost. NVIDIA Blackwell
      (RTX 5000) with the proprietary 580+ driver also fails to survive S4.

      While this is off (and boot.resumeDevice is not set by hand), the
      hibernate / hybrid-sleep / suspend-then-hibernate targets are masked, so
      the action fails cleanly instead of losing the session. S3 suspend is
      unaffected.

      When on, boot.resumeDevice defaults to the first on-disk swap device
      (zram excluded). Override with:
        boot.resumeDevice = "/dev/disk/by-uuid/<swap UUID>";
    '';
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkMerge [
    (lib.mkIf (!cfg.enable && !resumeDeclared) {
      systemd.targets.hibernate.enable = false;
      systemd.targets.hybrid-sleep.enable = false;
      systemd.targets.suspend-then-hibernate.enable = false;
    })

    (lib.mkIf (cfg.enable && resumeDevice != null) {
      boot.resumeDevice = lib.mkDefault resumeDevice;
    })

    (lib.mkIf (cfg.enable && swap.noDiskSwap config.swapDevices && !resumeDeclared) {
      warnings = [
        ''
          roudix.boot.hibernation.enable is on but no usable on-disk swap was
          found (zram does not count). Declare a swap partition at least as
          large as your RAM in swapDevices, or turn the option off.
        ''
      ];
    })

    (lib.mkIf (cfg.enable && swap.onlySwapFile config.swapDevices && !resumeDeclared) {
      warnings = [
        ''
          roudix.boot.hibernation.enable is on but the only on-disk swap is a
          file. A file cannot carry boot.resumeDevice alone: set
          boot.resumeDevice to the device holding the file and add
          resume_offset=<offset> to boot.kernelParams, or use a swap partition.
        ''
      ];
    })
  ];
}

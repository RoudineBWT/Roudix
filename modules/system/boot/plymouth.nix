{ lib, config, pkgs, ... }:
let
  cfg = config.roudix.boot.plymouth;
  roudixPlymouth = pkgs.callPackage ../../../pkgs/roudix-plymouth { };
in
{
  options.roudix.boot.plymouth = {
    enable = lib.mkOption {
      description = ''
        Roudix boot splash (Plymouth): the Roudix logo on the boot-menu brown,
        with a progress bar and a disk-encryption (LUKS) password prompt.
      '';
      type = lib.types.bool;
      default = true;
    };

    theme = lib.mkOption {
      description = ''
        Which splash to show:
          roudix           logo with a gentle pulse (default)
          roudix-spin      logo turning slowly
          roudix-gradient  warm gradient background, glow pulsing behind the logo
          roudix-ember     embers rising, progress ring, logo in a growing
                           glow (the showy one)
          roudix-panda     Pandoudix, the mascot (waves on boot, sleeps on
                           shutdown, teary when a message shows up)
      '';
      type = lib.types.enum [ "roudix" "roudix-spin" "roudix-gradient" "roudix-ember" "roudix-panda" ];
      default = "roudix";
    };

    quiet = lib.mkOption {
      description = ''
        Hide kernel / initrd messages during boot so the splash is not drawn
        over by text (adds "quiet" and lowers the console log level). Turn it
        off to debug a boot problem; the splash itself can be skipped by
        removing "splash" from the kernel command line in the boot menu.
      '';
      type = lib.types.bool;
      default = true;
    };
  };

  config = lib.mkIf (config.roudix.boot.enable && cfg.enable) {
    boot.plymouth = {
      enable = true;
      theme = cfg.theme;
      themePackages = [ roudixPlymouth ];
    };

    boot.consoleLogLevel = lib.mkIf cfg.quiet (lib.mkDefault 0);
    boot.kernelParams = lib.mkIf cfg.quiet [ "quiet" "udev.log_level=3" ];
  };
}

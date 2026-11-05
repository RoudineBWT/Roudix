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
      theme = "roudix";
      themePackages = [ roudixPlymouth ];
    };

    boot.consoleLogLevel = lib.mkIf cfg.quiet (lib.mkDefault 0);
    boot.initrd.verbose = lib.mkIf cfg.quiet (lib.mkDefault false);
    boot.kernelParams = lib.mkIf cfg.quiet [ "quiet" "udev.log_level=3" ];
  };
}

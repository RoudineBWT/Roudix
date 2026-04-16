{ config, lib, pkgs, username, ... }:

let
  cfg = config.roudix.autoupdate;
in
{
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };

  nix.optimise = {
    automatic = true;
    dates = [ "weekly" ];
  };

  services.fwupd.enable = true;

  nix.settings.auto-optimise-store = true;

  system.autoUpgrade = lib.mkIf (!cfg.enable) {
    enable = true;
    flake = "path:${cfg.configPath}#roudix";
    operation = "boot";
    dates = cfg.interval;
    allowReboot = false;
  };
}

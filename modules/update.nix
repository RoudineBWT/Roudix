{ config, username, ... }:
{
  # Keep common values as the source of truth for all hosts.
  system.autoUpgrade = {
    enable = true;
    allowReboot = false;
    flake = "/home/${username}/.config/roudix#${config.networking.hostName}";
    dates = "daily";
  };

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
}

{ config, username, ... }:
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
}

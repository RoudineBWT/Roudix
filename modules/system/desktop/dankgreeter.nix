{ config, pkgs, inputs, lib, roudixBranding, username, ... }:
let
  desktopType = config.roudix.desktop.type;
  shellType   = config.roudix.desktop.shell or "noctalia";
  isDms       = shellType == "dms";
  compositor  = if desktopType == "niri" then "niri" else "hyprland";
in
lib.mkIf isDms {
  services.displayManager.dms-greeter = {
    enable          = true;
    compositor.name = compositor;
    package = inputs.dms.packages.${pkgs.stdenv.hostPlatform.system}.default;
  };

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.dms-greeter.enableGnomeKeyring = true;

}

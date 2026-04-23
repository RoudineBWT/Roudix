{ config, pkgs, inputs, lib, ... }:
let
  desktopType = config.roudix.desktop.type;
  waylandCompositors = [ "niri" "hyprland" "mangowc" ];
  compositor  = if desktopType == "niri"    then "niri"
                else if desktopType == "mangowc" then "mango"
                else "hyprland";
in
lib.mkIf (builtins.elem desktopType waylandCompositors) {
  services.displayManager.dms-greeter = {
    enable          = true;
    compositor.name = compositor;
    package = inputs.dms.packages.${pkgs.stdenv.hostPlatform.system}.default;
  };

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.dms-greeter.enableGnomeKeyring = true;
}

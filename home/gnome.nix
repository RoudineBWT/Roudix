{ osConfig, lib, pkgs, inputs, username, ... }:
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "gnome") {
    home.packages = with pkgs; [
      papirus-icon-theme
      capitaine-cursors
    ];

    home.pointerCursor = {
      name    = "capitaine-cursors-white";
      package = pkgs.capitaine-cursors;
      size    = 24;
      gtk.enable = true;
    };

    dconf.settings = {
      "org/gnome/desktop/background" = {
        picture-uri      = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-light.svg";
        picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
        picture-options  = "zoom";
      };
      "org/gnome/desktop/screensaver" = {
        picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
      };
      "org/gnome/desktop/interface" = {
        color-scheme = "prefer-dark";
        icon-theme   = "Papirus-Dark";
        gtk-theme    = "adw-gtk3-dark";
        cursor-theme = "capitaine-cursors-white";
        cursor-size  = 24;
      };
    };
  };
}

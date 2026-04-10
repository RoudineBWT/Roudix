{ pkgs, lib, config, ... }:
let
  roudix-branding = pkgs.callPackage ./pkgs/roudix-branding {};
in

{
  environment.systemPackages = with pkgs; [
    roudix-branding
  ];

  environment.pathsToLink = [ "/share/icons" "/share/backgrounds" "/share/gnome-background-properties" ];

  # Logo GDM
  programs.dconf.profiles.gdm.databases = [{
    settings = {
      "org/gnome/login-screen" = {
        logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
      };
    };
  }];

  # Wallpaper par défaut GNOME
  programs.dconf.profiles.user.databases = [{
    settings = {
      "org/gnome/desktop/background" = {
        picture-uri       = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-light.svg";
        picture-uri-dark  = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
        picture-options   = "zoom";
      };
      "org/gnome/desktop/screensaver" = {
        picture-uri = "file:///run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";
      };
    };
  }];

  # Wallpaper par défaut KDE
  environment.etc."xdg/plasma-workspace/env/roudix-wallpaper.sh" = {
    mode = "0755";
    text = ''
      #!/bin/sh
      WALLPAPER_DARK="/run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg"
      WALLPAPER_LIGHT="/run/current-system/sw/share/backgrounds/roudix/roudix-light.svg"
      CONFIG="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
      if [ ! -f "$CONFIG" ]; then
        mkdir -p "$HOME/.config"
        cat > "$CONFIG" << KDEEOF
[Containments][1][Wallpaper][org.kde.image][General]
Image=$WALLPAPER_DARK
KDEEOF
      fi
    '';
  };
}

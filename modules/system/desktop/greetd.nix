{ config, lib, pkgs, roudixBranding, ... }:
{
  programs.regreet = {
    enable = true;
    cageArgs = [ "-s" "-m" "last" ];
    settings = {
      background = {
        path = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
        fit = "Cover";
      };
      GTK = {
        cursor_theme_name = lib.mkForce "capitaine-cursors";
        icon_theme_name = lib.mkForce "Papirus-Dark";
        application_prefer_dark_theme = true;
      };
    };
    extraCss = ''
      /* Catppuccin Mocha */

      /* Cacher la barre de titre de cage */
      headerbar,
      .titlebar {
        opacity: 0;
        min-height: 0;
        padding: 0;
        margin: 0;
      }

      window {
        background-color: transparent;
      }

      window > box {
        margin-left: 120px;
        margin-right: auto;
      }

      .container {
        background-color: alpha(#1e1e2e, 0.85);
        border-radius: 16px;
        padding: 32px 40px;
        border: 1px solid alpha(#585b70, 0.5);
        box-shadow: 0 8px 32px alpha(#000000, 0.5);
        min-width: 320px;
      }

      /* Logo Roudix au dessus du formulaire */
      .container image {
        -gtk-icon-source: url("/run/current-system/sw/share/backgrounds/roudix/roudix-logo.png");
        margin-bottom: 16px;
      }

      entry {
        background-color: alpha(#313244, 0.9);
        border: 1px solid alpha(#585b70, 0.8);
        border-radius: 8px;
        color: #cdd6f4;
        padding: 10px 14px;
        caret-color: #cba6f7;
      }

      entry:focus {
        border-color: #cba6f7;
        box-shadow: 0 0 0 2px alpha(#cba6f7, 0.3);
      }

      button {
        background-color: alpha(#cba6f7, 0.25);
        color: #cba6f7;
        border: 1px solid #cba6f7;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        box-shadow: none;
      }

      button:hover {
        background-color: alpha(#cba6f7, 0.45);
      }

      combobox button {
        background-color: alpha(#313244, 0.9);
        color: #cdd6f4;
        border: 1px solid alpha(#585b70, 0.8);
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: none;
      }

      combobox button:hover {
        background-color: alpha(#585b70, 0.9);
        border-color: #cba6f7;
      }

      label {
        color: #cdd6f4;
      }

      /* Boutons Reboot/Power Off */
      .reboot-button,
      .poweroff-button {
        background-color: alpha(#f38ba8, 0.2);
        color: #f38ba8;
        border: 1px solid #f38ba8;
      }

      .reboot-button:hover,
      .poweroff-button:hover {
        background-color: alpha(#f38ba8, 0.4);
      }
    '';
  };

  environment.etc = {
    "greetd/sessions/hyprland-uwsm.desktop".text = ''
      [Desktop Entry]
      Name=Hyprland (UWSM)
      Exec=uwsm start hyprland-uwsm.desktop
      Type=Application
    '';
  };

  environment.systemPackages = with pkgs; [
    papirus-icon-theme
    capitaine-cursors
  ];

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;

  users.users.greeter.extraGroups = [ "video" "input" ];
}

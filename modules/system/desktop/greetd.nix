{ config, lib, pkgs, ... }:
{
  services.greetd = {
    enable = true;
    settings.default_session = {
      command = "${lib.getExe pkgs.greetd.regreet} -l debug";
      user    = "greeter";
    };
  };

  programs.regreet = {
    enable = true;
    settings = {
      background = {
        path = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
        fit  = "Cover";
      };
      GTK = {
        application_prefer_dark_theme = true;
        icon_theme_name   = "Papirus-Dark";
        cursor_theme_name = "capitaine-cursors";
      };
    };
    extraCss = ''
      window {
        background-color: transparent;
      }

      .container {
        background-color: alpha(#1e1e2e, 0.75);
        border-radius: 16px;
        padding: 48px 56px;
        border: 1px solid alpha(#cdd6f4, 0.1);
        box-shadow: 0 8px 32px alpha(#000000, 0.5);
        min-width: 360px;
      }

      entry {
        background-color: alpha(#313244, 0.9);
        border: 1px solid alpha(#cdd6f4, 0.2);
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
        background-color: #cba6f7;
        color: #1e1e2e;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
      }

      button:hover {
        background-color: #b4a0e8;
      }

      combobox button {
        background-color: alpha(#313244, 0.9);
        color: #cdd6f4;
        border: 1px solid alpha(#cdd6f4, 0.2);
      }

      label {
        color: #cdd6f4;
      }
    '';
  };

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
}

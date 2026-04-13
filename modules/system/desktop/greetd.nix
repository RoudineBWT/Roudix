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
        cursor_theme_name = "capitaine-cursors";
        icon_theme_name = "Papirus-Dark";
      };
    };
    extraCss = ''
      /* Catppuccin Mocha */

      window {
        background-color: transparent;
      }

      box#main-box {
        background-color: rgba(30, 30, 46, 0.85);
        border-radius: 16px;
        padding: 32px 40px;
        border: 1px solid rgba(88, 91, 112, 0.5);
      }

      label#clock {
        font-family: monospace;
        font-size: 48px;
        font-weight: bold;
        color: #cba6f7;
        margin-bottom: 4px;
      }

      label {
        color: #cdd6f4;
      }

      entry {
        background-color: rgba(49, 50, 68, 0.9);
        color: #cdd6f4;
        border: 1px solid #585b70;
        border-radius: 12px;
        padding: 10px 14px;
      }

      entry:focus {
        border-color: #cba6f7;
        box-shadow: none;
      }

      combobox button,
      combobox button.combo {
        background: rgba(49, 50, 68, 0.9);
        color: #cdd6f4;
        border: 1px solid #585b70;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: none;
      }

      combobox button:hover {
        background-color: rgba(88, 91, 112, 0.9);
        border-color: #cba6f7;
      }

      button.suggested-action {
        background-color: rgba(203, 166, 247, 0.25);
        color: #cba6f7;
        border: 1px solid #cba6f7;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: bold;
        box-shadow: none;
      }

      button.suggested-action:hover {
        background-color: rgba(203, 166, 247, 0.45);
      }

      button.destructive-action {
        background-color: rgba(243, 139, 168, 0.2);
        color: #f38ba8;
        border: 1px solid #f38ba8;
        border-radius: 12px;
        padding: 8px 20px;
        box-shadow: none;
      }

      button.destructive-action:hover {
        background-color: rgba(243, 139, 168, 0.4);
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

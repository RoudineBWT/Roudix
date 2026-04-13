{ config, lib, pkgs, ... }:
{
  services.greetd = {
    enable = true;
    settings.default_session = {
      command = "${lib.getExe pkgs.nwg-hello}";
      user = "greeter";
    };
  };

  environment.etc = {
    "greetd/sessions/hyprland-uwsm.desktop".text = ''
      [Desktop Entry]
      Name=Hyprland (UWSM)
      Exec=uwsm start hyprland-uwsm.desktop
      Type=Application
    '';

    "nwg-hello/nwg-hello.json".text = builtins.toJSON {
      session_dirs     = [ "/etc/greetd/sessions" ];
      custom_sessions  = [];
      monitor_nums     = [];
      form_on_monitors = [ 0 ];
      delay_secs       = 1;
      "cmd-sleep"      = "systemctl suspend";
      "cmd-reboot"     = "systemctl reboot";
      "cmd-poweroff"   = "systemctl poweroff";
      "gtk-theme"          = "adw-gtk3-dark";
      "gtk-icon-theme"     = "Papirus-Dark";
      "gtk-cursor-theme"   = "capitaine-cursors";
      "prefer-dark-theme"  = true;
      "template-name"      = "";
      "time-format"        = "%H:%M";
      "date-format"        = "%A, %d %B";
      "layer"              = "overlay";
      "keyboard-mode"      = "exclusive";
      "lang"               = "en";
      "avatar-show"        = false;
      "avatar-size"        = 100;
      "avatar-border-width" = 1;
      "avatar-border-color" = "#cdd6f4";   # Catppuccin text
      "avatar-corner-radius" = 15;
      "avatar-circle"      = false;
      "env-vars"           = [];
    };

    "nwg-hello/nwg-hello.css".text = ''
      /* Catppuccin Mocha */

      window {
        background-image: url("/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png");
        background-size: auto 100%;
      }

      #form-wrapper {
        background-color: rgba(30, 30, 46, 0.75);
      }

      entry {
        background-color: rgba(49, 50, 68, 0.9);
        color: #cdd6f4;
        border: 1px solid #585b70;
        border-radius: 18px;
        padding: 12px;
      }

      entry:focus {
        border-color: #cba6f7;
      }

      button {
        background: rgba(49, 50, 68, 0.85) none;
        color: #cdd6f4;
        border: 1px solid #585b70;
        border-radius: 18px;
        padding: 12px;
      }

      button:hover {
        background-color: rgba(88, 91, 112, 0.9);
        border-color: #cba6f7;
      }

      #power-button {
        border-radius: 18px;
        background: none;
        border: none;
      }

      #power-button:hover {
        background-color: rgba(203, 166, 247, 0.15);
      }

      #power-button:active {
        background-color: rgba(203, 166, 247, 0.3);
      }

      #welcome-label {
        font-size: 48px;
        color: #cba6f7;
      }

      #clock-label {
        font-family: monospace;
        font-size: 30px;
        color: #cdd6f4;
      }

      #date-label {
        font-size: 18px;
        color: #a6adc8;
      }

      #form-label {
        color: #a6adc8;
      }

      #form-combo {
      }

      #password-entry {
      }

      #login-button {
        background-color: rgba(203, 166, 247, 0.2);
        border-color: #cba6f7;
      }

      #login-button:hover {
        background-color: rgba(203, 166, 247, 0.4);
      }
    '';
  };

  environment.systemPackages = with pkgs; [
    papirus-icon-theme
    capitaine-cursors
    adw-gtk3
  ];

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
}

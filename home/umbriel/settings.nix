{ pkgs, config, lib, osConfig, ... }:

let
  terminalCmd = osConfig.roudix.terminal or "ghostty";
  terminal = "${pkgs.${terminalCmd}}/bin/${terminalCmd}";

  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  fileManager = "${pkgs.${fileManagerCmd}}/bin/${fileManagerCmd}";

  browserCmd = osConfig.roudix.browser.command or null;
  browser = if browserCmd != null then "${pkgs.${browserCmd}}/bin/${browserCmd}" else null;

  noctalia = lib.getExe config.programs.noctalia.package;
in
{
  programs.umbriel.settings = {
    general = {
      show_cheatsheet = false;
      screenshot_path = "~/Pictures/umbriel-screenshots/from %Y-%m-%d %H-%M-%S.png";
    };

    appearance = {
      prefer_no_csd = true;
      border_width = 2;
      outer_border_width = 13;
      corner_radius = 20;  # Niri avait 20
      animation_ms = 200;

      shadow = {
        enabled = false;  # Niri avait shadow, mais Umbriel gère différemment
        softness = 0;
        offset_x = 5;
        offset_y = 5;
        color = "#00000070";
      };

      blur = {
        enabled = true;
        passes = 2;
        radius = 3;
        noise = 0.03;
        brightness = 1.0;
        contrast = 1.0;
        saturation = 1.0;
        optimized = true;
      };
    };

    layout = {
      mode = "scrolling";
      gap = 9;  # Niri avait 9
      center_focused_column = false;  # Niri avait "never"
      width_presets = [
        0.33333
        0.5
        0.66667
      ];
      scrolling = {
        always_center_single_column = false;
      };
    };

    # ─── Outputs (adapté de Niri) ──────────────────────────────────────────
    output = {
      "HKC OVERSEAS LIMITED 24E4 0000000000001" = {
        mode = "1920x1080@165.001";
        position = [ 0 0 ];
        scale = 1.0;
        transform = "normal";
      };
      "Lenovo Group Limited Legion 27Q-10 UNA07260" = {
        mode = "2560x1440@240.000";
        position = [ 1920 0 ];
        scale = 1.0;
        transform = "normal";
        variable_refresh_rate = { on_demand = true; };
      };
    };

    # ─── Input (adapté de Niri) ────────────────────────────────────────────
    input = {
      keyboard = {
        layout = "us";
        variant = "intl";
        repeat_rate = 25;
        repeat_delay = 600;
        numlock = true;
      };
      touchpad = {
        tap = true;
        natural_scroll = true;
      };
      mouse = {
        scroll_wheel_step = 60;
        accel_profile = "flat";
      };
      cursor = {
        theme = "Bibata-Modern-Ice";
        size = 24;
        hide_when_typing = true;
        hide_after_inactive_ms = 1000;
      };
      focus = {
        follows_mouse = true;
      };
    };

    workspaces = {
      back_and_forth = true;
    };

    cursor = {
      xcursor_theme = "Bibata-Modern-Ice";
      xcursor_size = 24;
    };
  };
}

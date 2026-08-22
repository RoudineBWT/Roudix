{ pkgs, config, lib, osConfig, ... }:

let
  terminalCmd = osConfig.roudix.terminal or "ghostty";
  terminal = "${pkgs.${terminalCmd}}/bin/${terminalCmd}";

  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  fileManager = "${pkgs.${fileManagerCmd}}/bin/${fileManagerCmd}";

  noctalia = lib.getExe config.programs.noctalia.package;
in
{
  programs.umbriel.settings = {
    general = {
      screenshot_path = "~/Pictures/umbriel-screenshots/from %Y-%m-%d %H-%M-%S.png";
    };

    appearance = {
      prefer_no_csd = true;
      border_width = 2;
      outer_border_width = 13;
      corner_radius = 20;
      animation_ms = 200;
    };

    layout = {
      mode = "scrolling";
      gap = 9;
      width_presets = [ 0.33333 0.5 0.66667 ];
      scrolling = {
        always_center_single_column = false;
      };
    };

    # ─── Outputs ──────────────────────────────────────────────────────────
    output = {
      "DP-1" = {  # ← Utilise les noms réels de tes écrans
        mode = "2560x1440@240.000";
        position = [ 0 0 ];
        scale = 1.0;
        transform = "normal";
      };
      "DP-3" = {
        mode = "1920x1080@165.001";
        position = [ 2560 0 ];
        scale = 1.0;
        transform = "normal";
      };
    };

    # ─── Input ────────────────────────────────────────────────────────────
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
  };
}

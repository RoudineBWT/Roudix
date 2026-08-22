{ pkgs, config, lib, osConfig, ... }:

{
  # Variables d'environnement pour Noctalia
  home.sessionVariables = {
    XDG_CURRENT_DESKTOP = "Umbriel";
    XDG_SESSION_TYPE = "wayland";
    XDG_SESSION_DESKTOP = "Umbriel";
    NOCTALIA_SHELL = "noctalia";
  };

  programs.umbriel.settings = {
    general = {
      # Noctalia sera lancé via autostart
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
    };

    # ─── Outputs ──────────────────────────────────────────────────────────
    output = {
      "DP-1" = {
        mode = "2560x1440@240.000";
        position = [ 1920 0 ];
        scale = 1.0;
        transform = "normal";
      };
      "DP-3" = {
        mode = "1920x1080@165.001";
        position = [ 0 0 ];
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

## _input.nix — Umbriel: [input], [input.keyboard], [input.touchpad],
## [input.mouse], [input.cursor], [input.focus].
##
## Doc : https://docs.noctalia.dev/umbriel/input/
{ ... }:
{
  programs.umbriel.settings = {
  input = {
    # middle_click_paste laissé au défaut (true), pas configuré côté niri.

    keyboard = {
      layout = "us";
      variant = "intl";
      numlock_toggle = true; # niri: keyboard { numlock } au démarrage
    };

    touchpad = {
      tap = true;
      natural_scroll = true;
    };

    mouse.accel_profile = "flat";

    focus.follows_mouse = true; # niri: focus-follows-mouse

    cursor = {
      theme = "Bibata-Modern-Ice"; # misc.kdl: cursor { xcursor-theme ... }
      size = 24;
      hide_when_typing = true;
      hide_timeout_ms = 1000; # niri: hide-after-inactive-ms 1000
    };
  };
  };
}

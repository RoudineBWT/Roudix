## _input.nix — Umbriel: [input], [input.keyboard], [input.touchpad],
## [input.mouse], [input.cursor], [input.focus].
##
## Docs: https://docs.noctalia.dev/umbriel/input/
{ osConfig, ... }:
{
  programs.umbriel.settings = {
  input = {
    # middle_click_paste left at its default (true).

    keyboard = {
      layout = osConfig.roudix.keyboardLayout;
      variant = osConfig.roudix.keyboardVariant;
      numlock_toggle = true; # niri: keyboard { numlock } on startup
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
      # hardware_cursor = false fixes the cursor freezing at its last
      # position in-game (only redrawing when the mouse moves) and then
      # flickering instead of smoothly appearing/disappearing — a classic
      # hardware cursor plane desync with fullscreen direct scanout (DP-1
      # has tearing=true + direct_scanout by default, see _output.nix).
      # This is the documented workaround for "cursor flicker or
      # disappearance caused by hardware cursor planes": the cursor gets
      # composited into the render instead of using the GPU's hardware
      # plane. Slight extra GPU cost (negligible outside demanding games),
      # no more stuck/ghost cursor.
      hardware_cursor = false;
    };
  };
  };
}

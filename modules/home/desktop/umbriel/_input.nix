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
      # Buttons for 1/2/3-finger taps (umbriel #301): "left_right_middle"
      # (libinput default) or "left_middle_right". Set explicitly so the
      # behavior doesn't change if the compositor default ever does.
      tap_button_map = "left_right_middle";
    };

    mouse.accel_profile = "flat";

    focus = {
      follows_mouse = true; # niri: focus-follows-mouse
      # hover_raises (umbriel e57420b): by default hovering a window with
      # follows_mouse also RAISES it, so sweeping the pointer over a larger
      # window underneath buries the one above (the floating ghostty / chat
      # windows over a tiled browser). false = hover only focuses; clicks,
      # keybinds and activation still raise.
      hover_raises = false;
    };

    # Edge/corner drop zones for floating windows (umbriel d88d0bc turned it
    # ON by default). Pinned to false to keep the previous behaviour: a
    # dragged floating window stays exactly where it is released. Set to true
    # to get half/quarter-screen snapping (see also window-snap in _binds.nix).
    window_snapping = false;

    # Edge scroll while dragging (umbriel #401): holding a window (Mod+drag
    # or tab bar) or a drag-and-drop near either end of a scrolling workspace
    # scrolls the strip so off-screen columns can be reached. Web / games /
    # DP-3 web workspaces are scrolling. Values below are the documented ones.
    drag_edge_scroll = {
      enabled = true;
      trigger_zone = 30;  # px at each end of the layout
      delay_ms = 100;     # time in the zone before scrolling starts
      max_speed = 1500.0; # px/s at the outer edge
    };

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
      hardware_cursor = true;
    };
  };
  };
}

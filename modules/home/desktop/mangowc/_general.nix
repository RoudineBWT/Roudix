{ osConfig, ... }:
{
  wayland.windowManager.mango.settings = {
    xkb_rules_layout = osConfig.roudix.keyboardLayout;
    xkb_rules_variant = osConfig.roudix.keyboardVariant;
    numlockon = 1;
    repeat_rate = 25;
    repeat_delay = 600;

    accel_profile = 1;
    accel_speed = 0.0;
    tap_to_click = 1;
    tap_and_drag = 1;
    drag_lock = 1;
    trackpad_natural_scrolling = 1;
    trackpad_disable_while_typing = 1;

    xwayland_persistence = 1;
    syncobj_enable = 1;
    focus_on_activate = 1;
    sloppyfocus = 1;
    warpcursor = 1;
    focus_cross_monitor = 0;
    focus_cross_tag = 0;
    enable_floating_snap = 1;
    snap_distance = 50;
    drag_tile_to_tile = 1;
    single_scratchpad = 1;
    axis_bind_apply_timeout = 100;

    cursor_size = 24;
    cursor_theme = "capitaine-cursors-white";
    cursor_hide_timeout = 0;
  };
}

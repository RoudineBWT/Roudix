{ osConfig, ... }:
let
  # Mango's layer blur/shadows ignore surface opacity, so transparent Noctalia
  # surfaces get blurred (docs.noctalia.dev compositor-settings/mango).
  isNoctalia = (osConfig.roudix.desktop.shell or "noctalia") == "noctalia";
  layerFx = if isNoctalia then 0 else 1;
in
{
  wayland.windowManager.mango.settings = {
    gap_inner_horizontal = 4;
    gap_inner_vertical = 4;
    gap_outer_horizontal = 9;
    gap_outer_vertical = 9;

    border_px = 2;
    border_color = "0x44444488";
    focus_color = "0x88888888";
    root_color = "0x201b14ff";
    maximized_screen_color = "0xBABD2Cff";
    urgent_color = "0xad401fff";
    scratchpad_color = "0xc4939dff";
    global_color = "0x8d64cfff";
    overlay_color = "0x95C381ff";
    border_radius = 0;
    no_border_when_single = 0;
    no_radius_when_single = 0;

    scratchpad_width_ratio = 0.8;
    scratchpad_height_ratio = 0.9;

    focused_opacity = 1.0;
    unfocused_opacity = 0.85;

    blur = 1;
    blur_layer = layerFx;
    blur_optimized = 1;
    blur_params_radius = 5;
    blur_params_num_passes = 2;
    blur_params_noise = 0.02;
    blur_params_brightness = 0.9;
    blur_params_contrast = 0.9;
    blur_params_saturation = 1.2;

    shadows = 1;
    layer_shadows = layerFx;
    shadow_only_floating = 1;
    shadows_size = 6;
    shadows_blur = 24;
    shadows_position_x = 0;
    shadows_position_y = 0;
    shadows_color = "0x00000066";
  };
}

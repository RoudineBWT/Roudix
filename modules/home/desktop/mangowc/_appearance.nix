{ ... }:
{
  wayland.windowManager.mango.settings = {
    gappih = 4;
    gappiv = 4;
    gappoh = 9;
    gappov = 9;

    borderpx = 2;
    bordercolor = "0x44444488";
    focuscolor = "0x88888888";
    rootcolor = "0x201b14ff";
    maximizescreencolor = "0xBABD2Cff";
    urgentcolor = "0xad401fff";
    scratchpadcolor = "0xc4939dff";
    globalcolor = "0x8d64cfff";
    overlaycolor = "0x95C381ff";
    border_radius = 0;
    no_border_when_single = 0;
    no_radius_when_single = 0;

    scratchpad_width_ratio = 0.8;
    scratchpad_height_ratio = 0.9;

    focused_opacity = 1.0;
    unfocused_opacity = 0.85;

    blur = 1;
    blur_layer = 1;
    blur_optimized = 1;
    blur_params_radius = 5;
    blur_params_num_passes = 2;
    blur_params_noise = 0.02;
    blur_params_brightness = 0.9;
    blur_params_contrast = 0.9;
    blur_params_saturation = 1.2;

    shadows = 1;
    layer_shadows = 1;
    shadow_only_floating = 1;
    shadows_size = 12;
    shadows_blur = 15;
    shadows_position_x = 0;
    shadows_position_y = 0;
    shadowscolor = "0x000000ff";
  };
}

{ ... }:
{
  wayland.windowManager.mango.settings = {
    # Layouts cycled by switch_layout. Mango documents circle_layout as the
    # list used by the switch_layout dispatcher.
    circle_layout = "scroller,tile,monocle,grid,deck";

    # Scroller / PaperWM-like behavior. Mango's current defaults give
    # scroller_prefer_overspread priority over focus_center/prefer_center,
    # so disable overspread to make the centering options below effective.
    scroller_structs = 20;
    scroller_default_proportion = 0.8;
    scroller_ignore_proportion_single = 0;
    scroller_default_proportion_single = 1.0;
    scroller_focus_center = 1;
    scroller_prefer_center = 1;
    scroller_prefer_overspread = 0;
    scroller_proportion_preset = "0.33333,0.5,0.66667,1.0";
    edge_scroller_pointer_focus = 1;

    default_mfact = 0.55;
    default_nmaster = 1;
    new_is_master = 1;
    smartgaps = 1;

    enable_hotarea = 1;
    hotarea_size = 10;
    hotarea_disable_on_fullscreen = 1;
    hotarea_corner = 2;
    ov_tab_mode = 0;
    overviewgappi = 5;
    overviewgappo = 30;

    # Fullscreen-only tearing: games explicitly marked with force_tearing:1
    # may tear, while windowed applications remain synchronized.
    allow_tearing = 2;
  };
}

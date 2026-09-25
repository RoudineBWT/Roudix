{ ... }:
{
  wayland.windowManager.mango.settings = {
    tagrule = [
      "id:1,monitor_name:DP-1,layout_name:scroller,no_hide:1"
      "id:2,monitor_name:DP-1,layout_name:tile,no_hide:1"
      "id:3,monitor_name:DP-1,layout_name:tile"
      "id:5,monitor_name:DP-1,layout_name:monocle"
      "id:6,monitor_name:DP-1,layout_name:deck"
      "id:4,monitor_name:DP-3,layout_name:grid"
      "id:7,monitor_name:DP-3,layout_name:monocle"
      "id:8,monitor_name:DP-3,layout_name:tile"
      "id:9,monitor_name:DP-3,layout_name:tile"
    ];

    # Keep generic selection surfaces from inheriting blur or animation.
    # Shell-specific layer rules belong in _rules-noctalia.nix / _rules-dms.nix
    # if they become necessary later.
    layerrule = [
      "noblur:1,noanim:1,layer_name:^selection$"
    ];
  };
}

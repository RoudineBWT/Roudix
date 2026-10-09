{ ... }:
{
  wayland.windowManager.mango.settings.window_rule = [
    "tags:5,monitor:DP-1,app_id:^steam$"
    "is_floating:1,app_id:^steam$,title:^notificationtoasts_.*$"
    "tags:5,monitor:DP-1,is_floating:1,title:^Friends List$"

    # Fullscreen games: allow tearing and prevent idle inhibition from being
    # lost while the game has focus.
    "tags:5,monitor:DP-1,is_fullscreen:1,force_tearing:1,vrr_only_fullscreen:1,idle_inhibit_when_focus:1,app_id:^steam_app_.*$"
    "tags:5,monitor:DP-1,is_fullscreen:1,force_tearing:1,vrr_only_fullscreen:1,idle_inhibit_when_focus:1,app_id:^heroic$"
    "tags:5,monitor:DP-1,app_id:^org\\.prismlauncher\\.PrismLauncher$"
    "tags:5,monitor:DP-1,is_fullscreen:1,force_tearing:1,vrr_only_fullscreen:1,idle_inhibit_when_focus:1,app_id:^Minecraft.*$"
    "tags:5,monitor:DP-1,app_id:^net\\.lutris\\.Lutris$"
    "tags:5,monitor:DP-1,app_id:^com\\.usebottles\\.bottles$"
    "tags:5,monitor:DP-1,app_id:^openrgb$"
  ];
}

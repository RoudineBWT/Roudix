{ ... }:
{
  wayland.windowManager.mango.settings.windowrule = [
    "tags:5,appid:^steam$"
    "isfloating:1,appid:^steam$,title:^notificationtoasts_.*$"
    "tags:5,isfloating:1,title:^Friends List$"

    # Fullscreen games: allow tearing and prevent idle inhibition from being
    # lost while the game has focus.
    "tags:5,isfullscreen:1,force_tearing:1,idleinhibit_when_focus:1,appid:^steam_app_.*$"
    "tags:5,isfullscreen:1,force_tearing:1,idleinhibit_when_focus:1,appid:^heroic$"
    "tags:5,appid:^org\\.prismlauncher\\.PrismLauncher$"
    "tags:5,isfullscreen:1,force_tearing:1,idleinhibit_when_focus:1,appid:^Minecraft.*$"
    "tags:5,appid:^net\\.lutris\\.Lutris$"
    "tags:5,appid:^com\\.usebottles\\.bottles$"
    "tags:5,appid:^openrgb$"
  ];
}

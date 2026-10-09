{ osConfig, lib, ... }:
let
  # roudix.mangowc.scratchpadApps (declared in
  # modules/system/desktop/mangowc.nix): toggles Discord/Element/Telegram
  # and Spotify between fixed tiling (false, default) and named scratchpads
  # (true). See _binds-scratchpad.nix for the keybind side. Sizes below
  # mirror the ones used on Umbriel; when no width/height is given, MangoWC
  # falls back to scratchpad_width_ratio/scratchpad_height_ratio from
  # _appearance.nix.
  scratchpadApps = osConfig.roudix.mangowc.scratchpadApps or false;
in
{
  wayland.windowManager.mango.settings.window_rule = [
    # Communication / utility apps
  ]
  ++ (if scratchpadApps then [
    "is_named_scratchpad:1,width:1316,height:1011,app_id:^discord$"
    "is_named_scratchpad:1,width:1316,height:1011,app_id:^Element$"
    "is_named_scratchpad:1,width:555,height:1011,app_id:^(org\\.telegram\\.desktop|TelegramDesktop)$"
  ] else [
    "tags:4,monitor:DP-3,app_id:^discord$"
    "tags:4,monitor:DP-3,app_id:^Element$"
    "tags:4,monitor:DP-3,app_id:^(org\\.telegram\\.desktop|TelegramDesktop)$"
  ])
  ++ [
    # Terminals / editors
    "tags:3,monitor:DP-1,is_floating:1,width:1505,height:755,app_id:^com\\.mitchellh\\.ghostty$"
    "tags:3,monitor:DP-1,is_floating:1,app_id:^kitty$"
    "tags:3,monitor:DP-1,app_id:^org\\.gnome\\.Ptyxis$"
    "tags:2,monitor:DP-1,app_id:^dev\\.zed\\.Zed$"

    # Browsers
    "tags:1,monitor:DP-1,app_id:^zen$"
    "is_floating:1,is_global:1,app_id:^zen$,title:^Picture-in-Picture$"
    "is_floating:1,app_id:^zen$,title:^About Zen$"

    "tags:1,monitor:DP-1,app_id:^firefox$"
    "is_floating:1,is_global:1,app_id:^firefox$,title:^Picture-in-Picture$"
    "is_floating:1,app_id:^firefox$,title:^About Mozilla Firefox$"

    "tags:1,monitor:DP-1,app_id:^brave-origin-beta$"
    "tags:9,monitor:DP-3,app_id:^brave-browser$"

    # Desktop / file / media apps
    "tags:6,monitor:DP-1,app_id:^org\\.(gnome\\.Nautilus|kde\\.dolphin)$"
    "is_floating:1,app_id:^org\\.(gnome\\.Nautilus|kde\\.dolphin)$,title:^(Save As|Open)$"
    "tags:6,monitor:DP-1,app_id:^org\\.(gnome\\.TextEditor|kde\\.kate)$"
  ]
  ++ (if scratchpadApps then [
    "is_named_scratchpad:1,app_id:^spotify$"
  ] else [
    "tags:7,monitor:DP-3,app_id:^spotify$"
  ])
  ++ [
    "tags:7,monitor:DP-3,app_id:^com\\.github\\.wwmm\\.easyeffects$"
  ];
}

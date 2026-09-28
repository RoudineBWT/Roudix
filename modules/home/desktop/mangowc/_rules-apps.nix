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
  wayland.windowManager.mango.settings.windowrule = [
    # Communication / utility apps
  ]
  ++ (if scratchpadApps then [
    "isnamedscratchpad:1,width:1316,height:1011,appid:^discord$"
    "isnamedscratchpad:1,width:1316,height:1011,appid:^Element$"
    "isnamedscratchpad:1,width:555,height:1011,appid:^(org\\.telegram\\.desktop|TelegramDesktop)$"
  ] else [
    "tags:4,appid:^discord$"
    "tags:4,appid:^Element$"
    "tags:4,appid:^(org\\.telegram\\.desktop|TelegramDesktop)$"
  ])
  ++ [
    # Terminals / editors
    "tags:3,isfloating:1,width:1505,height:755,appid:^com\\.mitchellh\\.ghostty$"
    "tags:3,isfloating:1,appid:^kitty$"
    "tags:3,appid:^org\\.gnome\\.Ptyxis$"
    "tags:2,appid:^dev\\.zed\\.Zed$"

    # Browsers
    "tags:1,appid:^zen$"
    "isfloating:1,isglobal:1,appid:^zen$,title:^Picture-in-Picture$"
    "isfloating:1,appid:^zen$,title:^About Zen$"

    "tags:1,appid:^firefox$"
    "isfloating:1,isglobal:1,appid:^firefox$,title:^Picture-in-Picture$"
    "isfloating:1,appid:^firefox$,title:^About Mozilla Firefox$"

    "tags:1,appid:^brave-origin-beta$"
    "tags:9,appid:^brave-browser$"

    # Desktop / file / media apps
    "tags:6,appid:^org\\.gnome\\.Nautilus$"
    "isfloating:1,appid:^org\\.gnome\\.Nautilus$,title:^(Save As|Open)$"
    "tags:6,appid:^org\\.gnome\\.TextEditor$"
  ]
  ++ (if scratchpadApps then [
    "isnamedscratchpad:1,appid:^spotify$"
  ] else [
    "tags:7,appid:^spotify$"
  ])
  ++ [
    "tags:7,appid:^com\\.github\\.wwmm\\.easyeffects$"
  ];
}

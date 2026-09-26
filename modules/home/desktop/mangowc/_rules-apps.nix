{ ... }:
{
  wayland.windowManager.mango.settings.windowrule = [
    # Communication / utility apps
    "tags:4,appid:^discord$"
    "tags:4,appid:^Element$"
    "tags:4,appid:^(org\\.telegram\\.desktop|TelegramDesktop)$"

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
    "tags:7,appid:^spotify$"
    "tags:7,appid:^com\\.github\\.wwmm\\.easyeffects$"
  ];
}

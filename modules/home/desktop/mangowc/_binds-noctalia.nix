{ ... }:
{
  wayland.windowManager.mango.settings = {
    bind = [
      "SUPER+SHIFT,Q,spawn,noctalia msg panel-toggle session"
      "SUPER,D,spawn,noctalia msg panel-toggle launcher"
      "SUPER+ALT,L,spawn,noctalia msg session lock"
      "ALT,Tab,spawn,noctalia msg window-switcher hold"

      "CTRL+SHIFT,1,spawn,noctalia msg screenshot-region"
      "CTRL+SHIFT,2,spawn,noctalia msg screenshot-fullscreen"
      "CTRL+SHIFT,3,spawn,noctalia msg screenshot-fullscreen pick"

    ];

    # bindl = also active while the screen is locked (niri allow-when-locked).
    bindl = [
      "NONE,XF86AudioRaiseVolume,spawn,noctalia msg volume-up"
      "NONE,XF86AudioLowerVolume,spawn,noctalia msg volume-down"
      "NONE,XF86AudioMute,spawn,noctalia msg volume-mute"
      "NONE,XF86AudioMicMute,spawn,noctalia msg mic-mute"
      "NONE,XF86AudioPlay,spawn,playerctl play-pause"
      "NONE,XF86AudioPrev,spawn,playerctl previous"
      "NONE,XF86AudioNext,spawn,playerctl next"
    ];
  };
}

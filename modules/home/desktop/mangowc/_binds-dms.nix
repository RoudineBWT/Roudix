{ ... }:
{
  wayland.windowManager.mango.settings = {
    bind = [
      "SUPER+SHIFT,Escape,spawn,dms ipc call keybinds toggle mangowc"
      "SUPER+SHIFT,Q,spawn,dms ipc call powermenu toggle"
      "SUPER,D,spawn,dms ipc call spotlight toggle"
      "SUPER+ALT,L,spawn,dms ipc call lock lock"

      "CTRL+SHIFT,1,spawn,dms screenshot"
      "CTRL+SHIFT,2,spawn,dms screenshot full"
      "CTRL+SHIFT,3,spawn,dms screenshot window"

      "NONE,XF86AudioRaiseVolume,spawn,dms ipc call audio increment 3"
      "NONE,XF86AudioLowerVolume,spawn,dms ipc call audio decrement 3"
      "NONE,XF86AudioMute,spawn,dms ipc call audio mute"
      "NONE,XF86AudioMicMute,spawn,dms ipc call audio micmute"
      "NONE,XF86AudioPlay,spawn,dms ipc call mpris playPause"
      "NONE,XF86AudioPrev,spawn,dms ipc call mpris previous"
      "NONE,XF86AudioNext,spawn,dms ipc call mpris next"
    ];
  };
}

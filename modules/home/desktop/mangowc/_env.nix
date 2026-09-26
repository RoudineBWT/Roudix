{ osConfig, ... }:
let
  terminalCmd = osConfig.roudix.terminal or "ghostty";
in
{
  wayland.windowManager.mango.settings.env = [
    "MOZ_ENABLE_WAYLAND,1"
    "XDG_SESSION_TYPE,wayland"
    "XDG_CURRENT_DESKTOP,wlroots"
    "XDG_SESSION_DESKTOP,mango"
    "MOZ_DBUS_REMOTE,1"
    "GDK_BACKEND,wayland"
    "QT_AUTO_SCREEN_SCALE_FACTOR,1"
    "EGL_PLATFORM,wayland"
    "CLUTTER_BACKEND,wayland"
    "TERMINAL,${terminalCmd}"
    "_JAVA_AWT_WM_NONREPARENTING,1"
    "ELECTRON_OZONE_PLATFORM_HINT,auto"
    "QT_QPA_PLATFORMTHEME,qt6ct"
    "XCURSOR_THEME,capitaine-cursors-white"
    "XCURSOR_SIZE,24"
  ];
}

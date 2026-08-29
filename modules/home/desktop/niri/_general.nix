## _general.nix — niri: prefer-no-csd, screenshot-path, environment,
## debug, hotkey-overlay, spawn-at-startup, cursor (varient selon le shell).
{ osConfig, lib, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
in
{
  programs.niri.settings = {
    prefer-no-csd = true;
    screenshot-path = "~/Pictures/niri-screenshots/ from %Y-%m-%d %H-%M-%S.png";
    hotkey-overlay.skip-at-startup = true;

    environment = {
      LD_PRELOAD = "";
      MOZ_ENABLE_WAYLAND = "1";
      XDG_SESSION_TYPE = "wayland";
      XDG_CURRENT_DESKTOP = "niri";
      XDG_SESSION_DESKTOP = "niri";
      MOZ_DBUS_REMOTE = "1";
      GDK_BACKEND = "wayland";
      QT_AUTO_SCREEN_SCALE_FACTOR = "1";
      QT_WAYLAND_FORCE_DPI = "physical";
      EGL_PLATFORM = "wayland";
      CLUTTER_BACKEND = "wayland";
      TERM = "ghostty";
      TERMINAL = "ghostty";
      _JAVA_AWT_WM_NONREPARENTING = "1";
      ELECTRON_OZONE_PLATFORM_HINT = "auto";
      QT_QPA_PLATFORMTHEME = "qt6ct";
      QT_QPA_PLATFORMTHEME_QT6 = "qt6ct";
    }
    # GTK_IM_MODULE=simple (fix touches mortes) n'était fixé que côté
    # noctalia dans ta config d'origine.
    // (lib.optionalAttrs isNoctalia { GTK_IM_MODULE = "simple"; });

    cursor = if isNoctalia then {
      theme = "Bibata-Modern-Ice";
      size = 24;
    } else {
      theme = "capitaine-cursors-white";
      size = 32;
    };

    spawn-at-startup =
      [
        { command = [ "xwayland-satellite" ]; }
        { command = [ "swww-daemon" ]; }
        { command = [ "discord" ]; }
        { command = [ "openrgb" ]; }
      ]
      ++ (if isNoctalia then [
        { command = [ "noctalia" ]; }
      ] else [
        { command = [ "/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1" ]; }
      ]);
  };
}

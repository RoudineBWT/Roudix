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

    # Recommandé par la doc Noctalia v5 (compositor-settings/niri) pour que
    # les actions de notification et l'activation de fenêtre depuis
    # Noctalia fonctionnent correctement ; inoffensif côté DMS.
    debug.honor-xdg-activation-with-invalid-serial = true;

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

    # Coin en haut à gauche pour ouvrir/fermer l'overview à la souris
    # (niri >= 25.02, gestures.hot-corners.top-left).
    gestures.hot-corners.top-left = true;

    # Côté DMS il n'y a pas de calque de wallpaper "backdrop" comme avec
    # Noctalia (place-within-backdrop) : on donne au moins une couleur de
    # fond à l'overview plutôt que le gris par défaut de niri.
    overview = lib.mkIf (!isNoctalia) {
      backdrop-color = "#1a1a1a";
    };

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
        { command = [ "discord" ]; }
      ]
      ++ (if isNoctalia then [
        { command = [ "noctalia" ]; }
      ] else [
        { command = [ "/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1" ]; }
      ]);
  };
}

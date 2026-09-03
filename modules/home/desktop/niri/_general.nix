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

    # Hot corner (coin en haut à gauche bascule l'overview) — équivalent
    # niri du hot corner Umbriel. ⚠ niri lui-même sait choisir un coin
    # précis depuis la 25.11 (gestures.hot-corners { top-right; }), mais
    # le schéma typé de niri-flake n'a pas encore rattrapé cette
    # fonctionnalité : seul un interrupteur global `enable` existe pour
    # l'instant (toujours le coin haut-gauche). Si tu veux vraiment un
    # autre coin, il faudra passer par programs.niri.settings-config brut
    # (KDL) le jour où niri-flake expose top-left/top-right/etc.
    gestures.hot-corners.enable = true;

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
      # Recommandé par epireyn/niri-flake pour les apps Electron (VS Code,
      # Discord...) — beaucoup de wrappers nixpkgs cherchent spécifiquement
      # cette variable pour ajouter --ozone-platform=wayland automatiquement.
      # Ne fonctionne que si niri est lancé via `niri-session` (pas juste
      # `niri`) — vérifie que c'est bien le cas côté display manager/greetd.
      NIXOS_OZONE_WL = "1";
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

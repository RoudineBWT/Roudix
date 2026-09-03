## _general.nix — Umbriel: [general], [environment], [workspaces],
## [overview] et [hot_corners].
##
## Doc : https://docs.noctalia.dev/umbriel/configuration/
##       https://docs.noctalia.dev/umbriel/workspace-overview/
{ ... }:
{
  programs.umbriel.settings = {
  general = {
    autostart = [ "noctalia" "discord" ];
    # ⚠ "xwayland-satellite" n'est pas dans autostart : Umbriel le spawn
    # lui-même via `xwayland = true` (intégré au compositeur).
    mod_key = "Super";
    xwayland = true;
    show_cheatsheet = false; # niri: hotkey-overlay { skip-at-startup }
    focus_on_activate = false;
    # Nouveau (absent de la doc au moment de ta traduction niri) : les apps
    # comme Steam/PrismLauncher qui rouvrent déjà maximisées le restent au
    # lieu d'être re-tuilées à l'ouverture.
    honor_restored_maximize = true;
  };

  environment = {
    LD_PRELOAD = "";
    MOZ_ENABLE_WAYLAND = "1";
    MOZ_DBUS_REMOTE = "1";
    GDK_BACKEND = "wayland";
    QT_AUTO_SCREEN_SCALE_FACTOR = "1";
    QT_WAYLAND_FORCE_DPI = "physical";
    EGL_PLATFORM = "wayland";
    CLUTTER_BACKEND = "wayland";
    TERM = "ghostty";
    TERMINAL = "ghostty";
    QT_QPA_PLATFORM= "xcb";
    _JAVA_AWT_WM_NONREPARENTING = "1";
    ELECTRON_OZONE_PLATFORM_HINT = "auto";
    QT_QPA_PLATFORMTHEME = "qt6ct";
    QT_QPA_PLATFORMTHEME_QT6 = "qt6ct";
    GTK_IM_MODULE = "simple";
  };

  workspaces.back_and_forth = true; # niri: workspace-auto-back-and-forth

  # ── Survol des espaces (Mod+O) ──────────────────────────────────────────
  # Absent de ta config niri traduite ; ajouté pour un rendu cohérent avec
  # le blur/thème du reste (utilise appearance.blur pour le fond flouté).
  overview = {
    zoom = 0.5;
    background_blur = true;
    # background_tint / workspace_background ne sont plus des clés de
    # [overview] : ce sont des couleurs, déplacées vers [colors.overview],
    # géré par le noctalia.toml inclus (regénéré par matugen à chaque
    # wallpaper). Voir _include-noctalia.nix.
  };

  # ── Hot corners ──────────────────────────────────────────────────────────
  # Fonctionnalité native d'Umbriel sans équivalent niri direct. Un seul
  # coin activé par défaut (overview en haut-gauche) ; les 3 autres peuvent
  # être ajoutés de la même façon (top_right / bottom_left / bottom_right).
  hot_corners.top_left = {
    enabled = true;
    delay_ms = 300;
    action = "overview-toggle";
  };
  };
}

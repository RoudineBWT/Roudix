## _general.nix — niri: prefer-no-csd, screenshot-path, environment,
## debug, hotkey-overlay, spawn-at-startup, cursor (vary by shell).
{ osConfig, lib, pkgs, ... }:
let
  integrationApps = import ../_integration-apps.nix { inherit pkgs osConfig; };
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
in
{
  programs.niri.settings = {
    prefer-no-csd = true;
    screenshot-path = "~/Pictures/niri-screenshots/ from %Y-%m-%d %H-%M-%S.png";
    hotkey-overlay.skip-at-startup = true;

    # Lets Noctalia notification actions / window activation work
    # (docs.noctalia.dev compositor-settings/niri). Check the exact option
    # shape against the niri-flake schema.
    debug.honor-xdg-activation-with-invalid-serial = [ ];

    # Hot corner (top-left toggles the overview) — niri's equivalent of
    # Umbriel's hot corner. The niri-flake schema exposes the four corners
    # as required booleans (no `enable` switch, no defaults): all four
    # must be set explicitly.
    gestures.hot-corners = {
      top-left = true;
      top-right = false;
      bottom-left = false;
      bottom-right = false;
    };

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
      # Recommended by epireyn/niri-flake for Electron apps (VS Code,
      # Discord...) — many nixpkgs wrappers look for this variable
      # specifically to add --ozone-platform=wayland automatically. Only
      # works if niri is launched via `niri-session` (not bare `niri`) —
      # check the display manager/greetd session config.
      NIXOS_OZONE_WL = "1";
      QT_QPA_PLATFORMTHEME = "qt6ct";
      QT_QPA_PLATFORMTHEME_QT6 = "qt6ct";
    }
    # GTK_IM_MODULE=simple (dead-key fix) is only set for noctalia.
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
        { command = [ "discord" ]; }
      ]
      ++ (if isNoctalia then [
        { command = [ "noctalia" ]; }
      ] else [
        { command = [ integrationApps.polkitAgentExe ]; }
      ]);
  };
}

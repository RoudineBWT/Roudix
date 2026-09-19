## _rules-common.nix — niri: [[window-rule]] shared between noctalia and
## dms. Shell-specific rules live in _rules-noctalia.nix / _rules-dms.nix
## — imported alongside this file in default.nix, they CONCATENATE
## automatically (lists merge by concatenation in the Home Manager module
## system, no manual merge needed).
{ ... }:
let
  ws = import ./_ws.nix { };
in
{
  programs.niri.settings.window-rules = [
    {
      matches = [ { at-startup = true; app-id = "discord"; } ];
      open-on-workspace = ws.chat;
      default-column-width.fixed = 1316;
      default-window-height.fixed = 1011;
      default-floating-position = { x = 0; y = 0; relative-to = "top-left"; };
    }
    {
      matches = [ { at-startup = true; app-id = "Element"; } ];
      open-on-workspace = ws.chat;
      default-column-width.fixed = 1316;
      default-window-height.fixed = 1011;
      default-floating-position = { x = 0; y = 0; relative-to = "top-left"; };
    }
    {
      matches = [ { at-startup = true; app-id = "org.telegram.desktop"; } ];
      open-on-workspace = ws.chat;
      default-column-width.fixed = 555;
      default-window-height.fixed = 1011;
      default-floating-position = { x = 0; y = 0; relative-to = "top-right"; };
    }
    {
      matches = [ { app-id = "firefox"; } ];
      open-on-workspace = ws.web;
      open-maximized = true;
    }
    {
      matches = [ { title = "About Mozilla Firefox"; } ];
      open-on-workspace = ws.web;
      open-floating = true;
    }
    {
      matches = [ { app-id = "dev.zed.Zed"; } ];
      open-on-workspace = ws.code;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "^org.gnome.Nautilus$"; title = "^Save As$"; } ];
      open-focused = true;
    }
    {
      matches = [ { app-id = "com.mitchellh.ghostty"; } ];
      default-column-width.fixed = 1505;
      default-window-height.fixed = 755;
      open-floating = true;
    }
    {
      matches = [ { app-id = "steam"; } ];
      open-on-workspace = ws.games;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "openrgb"; } ];
      open-on-workspace = ws.games;
    }
    {
      matches = [ { app-id = "kitty"; } ];
      open-on-workspace = ws.term;
      open-floating = true;
    }
    {
      matches = [ { app-id = "org.gnome.Ptyxis"; } ];
      open-on-workspace = ws.term;
    }
    {
      matches = [ { app-id = "^(steam_app_.*)$"; } ];
      open-on-workspace = ws.games;
      open-fullscreen = true;
    }
    {
      matches = [ { app-id = "^heroic$"; } ];
      open-on-workspace = ws.games;
      open-fullscreen = true;
    }
    {
      matches = [ { app-id = "org.prismlauncher.PrismLauncher"; } ];
      open-on-workspace = ws.games;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "Minecraft"; } ];
      open-on-workspace = ws.games;
      open-fullscreen = true;
    }
    {
      matches = [ { app-id = "^firefox$"; title = "^Picture-in-Picture$"; } ];
      open-floating = true;
    }
    {
      matches = [ { app-id = "^zen$"; title = "^Picture-in-Picture$"; } ];
      open-floating = true;
    }
    {
      matches = [ { app-id = "^brave$"; title = "^Picture-in-Picture$"; } ];
      open-floating = true;
    }
    {
      matches = [ { app-id = "steam"; title = "^notificationtoasts_\\d+_desktop$"; } ];
      default-floating-position = { x = 10; y = 10; relative-to = "bottom-right"; };
    }
    {
      matches = [ { title = "Friends List"; } ];
      open-on-workspace = ws.games;
      open-floating = true;
    }
    {
      matches = [ { app-id = "^org\\.gnome\\.Nautilus$"; } ];
      excludes = [
        { app-id = "^xdg-desktop-portal(-gtk)?$"; }
        { title = "(?i)^(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$"; }
      ];
      open-on-workspace = ws.files;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "org.gnome.TextEditor"; } ];
      open-on-workspace = ws.files;
    }
    {
      matches = [ { app-id = "com.github.wwmm.easyeffects"; } ];
      open-on-workspace = ws.music;
    }
    {
      # Corner radius + clip applied to all windows (matches = [{}] — one
      # empty criteria group — applies to everything; matches = [] — an
      # empty list — matches NOTHING, counter-intuitively).
      matches = [ { } ];
      geometry-corner-radius = { top-left = 0.0; top-right = 0.0; bottom-left = 0.0; bottom-right = 0.0; };
      clip-to-geometry = true;
    }
  ];
}

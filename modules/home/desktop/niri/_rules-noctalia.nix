## _rules-noctalia.nix — niri: extra rules specific to Noctalia
## (blur/xray, Zen opacity, brave-origin-beta, KDE easyeffects, noctalia-*
## layers). Concatenated automatically with _rules-common.nix by the
## module system (see default.nix).
{ ... }:
let
  ws = import ./_ws.nix { };
in
{
  programs.niri.settings = {
  window-rules = [
    {
      matches = [ { at-startup = true; app-id = "com.mitchellh.ghostty"; } ];
      open-floating = true;
      background-effect = { blur = true; xray = false; };
    }
    {
      matches = [ { app-id = "zen-twilight"; } ];
      open-on-workspace = ws.web;
      open-maximized = true;
      draw-border-with-background = false;
      opacity = 0.95;
      background-effect = { blur = true; xray = false; };
    }
    {
      matches = [ { title = "About Zen Twilight"; } ];
      open-on-workspace = ws.web;
      open-floating = true;
      draw-border-with-background = false;
      opacity = 0.95;
      background-effect = { blur = true; xray = false; };
    }
    {
      matches = [ { app-id = "brave-origin-beta"; } ];
      open-on-workspace = ws.web;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "brave-browser"; } ];
      open-on-workspace = ws.browser2;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "Spotify"; } ];
      open-on-workspace = ws.music;
      open-maximized = true;
    }
    {
      matches = [ { app-id = "com.kde.easyeffects"; } ];
      open-on-workspace = ws.music;
    }
    # Global blur (all windows) without xray, for a realistic look.
    {
      matches = [ { } ];
      background-effect = { blur = true; xray = false; };
    }
  ];

  layer-rules = [
    {
      matches = [ { namespace = "^noctalia-wallpaper*"; } ];
      place-within-backdrop = true;
    }
    {
      matches = [ { namespace = "^noctalia-(bar-[^\"]+|notification|dock|panel|attached-panel|osd)$"; } ];
      background-effect.xray = false;
      # Extends the background effect to popups spawned by these
      # surfaces (e.g. quick-settings dropdown menus) — otherwise only
      # the bar itself gets blurred, not its popups.
      popups.background-effect.xray = false;
    }
    {
      matches = [ { namespace = "noctalia-window-switcher"; } ];
      background-effect = { blur = true; xray = false; };
    }
    # Hides only notification TOASTS from screen capture/streaming (OBS,
    # Discord Go Live...) — the bar and dock stay visible. Prevents a
    # private DM from flashing on stream without hiding notifications
    # app-by-app. To also block a specific app (e.g. a password manager),
    # add a window-rule with `block-out-from = "screencast";` in
    # niri-custom.nix.
    {
      matches = [ { namespace = "^noctalia-notification$"; } ];
      block-out-from = "screencast";
    }
  ];

  blur = { passes = 2; offset = 3.0; noise = 0.03; saturation = 1.0; };
  };
}

## _rules-noctalia.nix — niri: règles additionnelles spécifiques à Noctalia
## (blur/xray, opacité Zen, brave-origin-beta, easyeffects KDE, layers
## noctalia-*). Concaténé automatiquement avec _rules-common.nix par le
## système de modules (voir default.nix).
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
    # Blur global (toutes les fenêtres) sans xray, pour un rendu réaliste.
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
      # Nouveau (niri 26.04) : étend l'effet de fond aux popups générés
      # par ces surfaces (ex. menus déroulants des quick-settings) —
      # sans ça, seule la barre elle-même était floutée, pas ses popups.
      popups.background-effect.xray = false;
    }
    {
      matches = [ { namespace = "noctalia-window-switcher"; } ];
      background-effect = { blur = true; xray = false; };
    }
    # Masque uniquement les TOASTS de notification des captures d'écran/
    # stream (OBS, Discord Go Live...) — pas la barre ni le dock, qui
    # restent visibles. Le classique "un DM privé s'affiche 3 secondes en
    # plein stream" sans jamais avoir à réfléchir à quoi cacher app par
    # app. Si une appli en particulier doit aussi être masquée (un
    # gestionnaire de mots de passe par ex.), ajoute une window-rule avec
    # `block-out-from = "screencast";` dans niri-custom.nix.
    {
      matches = [ { namespace = "^noctalia-notification$"; } ];
      block-out-from = "screencast";
    }
  ];

  blur = { passes = 2; offset = 3.0; noise = 0.03; saturation = 1.0; };
  };
}

## _input.nix — Umbriel: [input], [input.keyboard], [input.touchpad],
## [input.mouse], [input.cursor], [input.focus].
##
## Doc : https://docs.noctalia.dev/umbriel/input/
{ ... }:
{
  programs.umbriel.settings = {
  input = {
    # middle_click_paste laissé au défaut (true), pas configuré côté niri.

    keyboard = {
      layout = "us";
      variant = "intl";
      numlock_toggle = true; # niri: keyboard { numlock } au démarrage
    };

    touchpad = {
      tap = true;
      natural_scroll = true;
    };

    mouse.accel_profile = "flat";

    focus.follows_mouse = true; # niri: focus-follows-mouse

    cursor = {
      theme = "Bibata-Modern-Ice"; # misc.kdl: cursor { xcursor-theme ... }
      size = 24;
      hide_when_typing = true;
      hide_timeout_ms = 1000; # niri: hide-after-inactive-ms 1000
      # Fix pour le curseur qui reste figé à son ancienne position en jeu
      # (visible seulement quand la souris bouge) puis clignote au lieu de
      # simplement disparaître/réapparaître : c'est un artefact classique du
      # curseur matériel (hardware cursor plane), qui se resynchronise mal
      # avec le direct scanout plein écran des jeux (DP-1 a tearing=true +
      # direct_scanout par défaut, voir _output.nix). La doc Umbriel identifie
      # justement hardware_cursor=false comme le contournement pour "cursor
      # flicker or disappearance caused by hardware cursor planes" : le
      # curseur est alors composité dans le rendu au lieu de passer par le
      # plan matériel du GPU. Léger coût GPU en plus (négligeable hors jeux
      # très exigeants), mais plus de curseur fantôme/figé.
      hardware_cursor = false;
    };
  };
  };
}

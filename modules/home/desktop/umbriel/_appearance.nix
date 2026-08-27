## _appearance.nix — Umbriel: [colors], [appearance], [appearance.blur],
## [appearance.shadow].
##
## Doc : https://docs.noctalia.dev/umbriel/appearance/
{ ... }:
{
  # ── Couleurs partagées (cheatsheet, bannière de diagnostic config) ──────
  # Seul `warning` était fixé dans ta config d'origine (venait de la couleur
  # "urgent" de niri). Le reste manquait : complété ici en gardant une base
  # sombre cohérente avec ton thème Catppuccin Mocha / accent pêche
  # (ajuste librement si Noctalia/matugen pousse déjà sa propre palette).
  colors = {
    background = "#1e1e2eF0";
    text_primary = "#cdd6f4FF";
    text_muted = "#a6adc8FF";
    accent_primary = "#fab387FF";  # peach
    accent_secondary = "#f9e2afFF"; # yellow
    warning = "#a7cce1FF";
    error = "#f38ba8FF";
  };

  appearance = {
    prefer_no_csd = true;
    corner_radius = 20;               # niri: geometry-corner-radius 20
    border_focused = "#9dd2c0FF";     # niri: focus-ring/border active-color
    border_unfocused = "#0e1214FF";   # niri: focus-ring/border inactive-color
    insert_hint_color = "#9dd2c080";  # niri: insert-hint color
    # border_width / outer_border_width : pas de valeur explicite côté niri,
    # donc défauts Umbriel conservés (2 / 0).

    blur = {
      enabled = true;
      optimized = true; # nouveau : un seul blur de fond par output (perf)
      passes = 2;
      noise = 0.03;
      saturation = 1.0;
      # radius / brightness / contrast laissés aux défauts Umbriel (5 / 0.9
      # / 0.9) — pas d'équivalent direct niri (moteur SceneFX différent),
      # à ajuster visuellement si besoin.
    };

    shadow = {
      enabled = true;
      color = "#00000070";
      # softness / offset_x / offset_y laissés aux défauts (10 / 2 / 2).
    };
  };
}

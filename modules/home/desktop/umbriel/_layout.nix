## _layout.nix — Umbriel: [layout], [layout.scrolling].
##
## Doc : https://docs.noctalia.dev/umbriel/layout/
{ ... }:
{
  layout = {
    mode = "scrolling";
    gap = 9; # niri: layout { gaps 9 }
    width_presets = [ 0.33333 0.5 0.66667 ];

    scrolling = {
      direction = "horizontal"; # niri scrollait horizontalement (colonnes)
      # Nouveau (absent avant, donc extent initial livré au choix du
      # client) : fixe une largeur de départ cohérente pour les nouvelles
      # colonnes, comme le fait la config packagée d'Umbriel.
      default_width_fraction = 0.5;
      center_underfull_strip = true;
      # ⚠ niri: center-focused-column "never" n'a toujours pas
      # d'équivalent (pas d'option pour désactiver l'auto-centrage au
      # focus). center_underfull_strip est un concept différent (centrer
      # la bande entière si elle est plus étroite que l'écran).
    };
  };
}

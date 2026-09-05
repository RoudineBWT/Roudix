## _layout.nix — Umbriel: [layout], [layout.scrolling].
##
## Doc : https://docs.noctalia.dev/umbriel/layout/
{ ... }:
{
  programs.umbriel.settings = {
  layout = {
    # Correction : layout.mode dans une règle [[workspace]] accepte bien
    # "scrolling", "dwindle" ET "master" directement (doc à jour :
    # docs.noctalia.dev/umbriel/workspaces/#available-fields). Pas besoin de
    # changer le mode global : il reste "scrolling" comme avant, et chat/jeux
    # reçoivent chacun une règle explicite layout.mode = "master" dans
    # _output.nix.
    mode = "scrolling";
    gap = 9; # niri: layout { gaps 9 }
    width_presets = [ 0.33333 0.5 0.66667 ];

    master = {
      position = "left";        # colonne principale à gauche, pile à droite
      default_width_fraction = 0.55;
      new_on_top = true;        # une nouvelle fenêtre rejoint le haut de la pile
    };

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
  };
}

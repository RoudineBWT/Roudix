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
      # ⚠ Changement de doc (cause du warning "unknown key
      # layout.scrolling.direction") : `direction` a été retiré. La
      # direction du scroll dépend maintenant de `workspace_axis` sur
      # l'output (docs.noctalia.dev/umbriel/outputs/#settings) : par
      # défaut "vertical" (workspaces empilés verticalement) → la bande de
      # scrolling est perpendiculaire, donc horizontale. C'est déjà le cas
      # ici (aucun workspace_axis défini dans _output.nix), donc le
      # comportement voulu (scroll horizontal façon niri) est conservé
      # sans rien à faire d'autre que supprimer cette clé.
      default_width_fraction = 0.5;
      center_underfull_strip = true;
      # Nouveau (absent avant) : remplit tout le viewport quand une
      # workspace n'a qu'une seule colonne tuilée, comme le fait la config
      # packagée d'Umbriel. N'affecte que l'affichage, pas la fraction
      # stockée : dès qu'une 2e colonne apparaît, la largeur configurée
      # reprend.
      expand_single_column = true;
      # Nouveau : équivalent (partiel) du "center-focused-column" de
      # niri, absent jusqu'ici. `true` centre systématiquement la colonne
      # focus (≈ "always" côté niri). Contrairement à niri, il n'y a que
      # bool ici : pas d'équivalent "on-overflow". Laissé à `false`
      # (comportement précédent, pas de centrage forcé au focus) —
      # décommente si tu veux ce centrage permanent.
      # center_focused = true;
    };
  };
  };
}

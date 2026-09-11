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
      # ⚠ Retiré : `expand_single_column` — testé et rejeté par `umbriel
      # validate` ("unknown key layout.scrolling.expand_single_column").
      # Je ne le retrouve pas confirmé dans la doc actuelle à cet
      # emplacement ; possible que ce soit un nom différent, un autre
      # chemin, ou une clé qui n'existe pas dans la version que tu as.
      # Umbriel bouge vite (le README prévient que les clés changent
      # entre versions) — à re-tester plus tard si tu veux vraiment ce
      # comportement (remplir le viewport avec une seule colonne), plutôt
      # que de deviner un autre nom.
      #
      # ⚠ `center_focused` ci-dessous est dans le même cas : je l'avais
      # noté comme nouveau (équivalent partiel du center-focused-column de
      # niri) mais je n'ai pas pu reconfirmer son existence/emplacement
      # exact après le rejet de expand_single_column. Laissé en commentaire
      # par précaution — décommente pour tester, mais vérifie le résultat
      # de `umbriel validate` avant de recharger.
      # center_focused = true;
    };
  };
  };
}

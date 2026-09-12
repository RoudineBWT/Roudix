# modules/system/nixpkgs-compat.nix
#
# Correctifs temporaires pour des régressions de nixpkgs unstable.
#
# nixpkgs unstable supprime parfois des alias ou change des attributs du
# jour au lendemain, avant que tous les paquets qui en dépendent (souvent
# via meta/passthru, pas un vrai usage) aient été mis à jour. Résultat :
# l'évaluation de tout le système plante, même si le paquet fautif n'est
# jamais réellement construit.
#
# Ce fichier centralise les overlays de contournement le temps que les
# correctifs remontent en amont dans nixpkgs.
#
# Règle : chaque entrée documente la date, le message d'erreur exact, et
# la raison. On retire l'entrée dès que le vrai fautif est corrigé
# upstream (généralement en quelques heures à quelques jours sur unstable).

{ lib, ... }:

{
  nixpkgs.overlays = [
    (final: prev: {
      # [2026-09-12] nixpkgs a supprimé l'alias plat `gtksourceview` :
      #   "'gtksourceview' attribute has been removed from nixpkgs.
      #    Use a 'gtksourceview*' attribute with an explicit ABI version
      #    instead."
      # Un paquet quelque part dans la closure (non identifié précisément —
      # ni dans home.packages, ni dans les paquets custom Roudix, donc
      # probablement une dépendance transitive d'un flake externe ou des
      # métadonnées d'un paquet nixpkgs) y référence encore l'alias.
      # gtksourceview5 build sans problème en isolation, donc on restaure
      # juste l'alias vers la version actuelle.
      gtksourceview = prev.gtksourceview5;
    })

    # Ajouter les futurs correctifs ici, sous la même forme :
    # (final: prev: {
    #   # [YYYY-MM-DD] raison + message d'erreur exact
    #   nom-du-paquet = prev.nom-du-paquet-remplacant;
    # })
  ];
}

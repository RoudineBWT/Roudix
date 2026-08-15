{ pkgs, ... }:
let
  # Thème Tela-dark déjà construit par le vrai install.sh de vinceliuice
  # (index.theme valide, tailles/symlinks résolus, recolorage "dark" déjà appliqué)
  telaDarkBase = "${pkgs.tela-icon-theme}/share/icons/Tela-dark";

  telaSync = pkgs.writeShellScriptBin "noctalia-tela-sync" ''
    set -euo pipefail
    # Fichier généré par le template Noctalia (voir templates/tela-primary.tmpl
    # ci-dessous) : contient juste le hex de la couleur "primary" active.
    primaryFile="$HOME/.config/noctalia/generated/tela-primary.txt"
    [ -f "$primaryFile" ] || exit 0

    primary=$(tr -d '[:space:]' < "$primaryFile")
    case "$primary" in
      \#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
      *) exit 0 ;;  # valeur vide/invalide (template pas encore rendu) -> on ne touche à rien
    esac

    dest="$HOME/.icons/Tela-noctalia"
    rm -rf "$dest"
    mkdir -p "$dest"
    # -L : déréférence les symlinks (scalable/32/... pointent vers le thème Tela
    # standard dans le store) pour obtenir un thème autonome et copiable tel quel
    cp -rL "${telaDarkBase}/." "$dest/"
    chmod -R u+w "$dest"

    ${pkgs.gnused}/bin/sed -i "s/^Name=.*/Name=Tela Noctalia/" "$dest/index.theme"

    # On ne touche QUE le dossier "places" (icônes de dossiers/emplacements),
    # sur TOUS les fichiers svg (pas juste default-folder*) : Tela a des dizaines
    # d'alias (folder.svg, folder-open.svg, gnome-folder.svg, stock_folder.svg...)
    # qui étaient des symlinks vers default-folder*.svg avant le cp -rL ci-dessus,
    # et qui sont maintenant des copies indépendantes à recolorer aussi.
    ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g" \
      "$dest/scalable/places/"*.svg \
      "$dest/16/places/"*.svg \
      "$dest/22/places/"*.svg \
      "$dest/24/places/"*.svg

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
      gtk-update-icon-cache -f -t "$dest" || true
    fi
    # Thème régénéré dans ~/.icons/Tela-noctalia, mais pas appliqué
    # automatiquement : choisis-le toi-même (nwg-look, etc.) si tu veux.
  '';
in
{
  home.packages = [ pkgs.tela-icon-theme telaSync pkgs.gnused ];

  # Le template ne contient QUE le hex de la couleur "primary" de la palette
  # active. Noctalia le régénère à chaque changement de thème/couleur.
  xdg.configFile."noctalia/templates/tela-primary.tmpl".text =
    "{{colors.primary.default.hex}}";

  # Syntaxe v5 : les templates utilisateur se déclarent dans un fichier .toml
  # fusionné (~/.config/noctalia/*.toml est lu et fusionné alphabétiquement),
  # sous [theme.templates.user.<id>], PAS dans un user-templates.toml séparé
  # (ça c'était l'ancien format v4).
  xdg.configFile."noctalia/50-tela-icons.toml".text = ''
    [theme.templates.user.tela_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${telaSync}/bin/noctalia-tela-sync"
  '';
}

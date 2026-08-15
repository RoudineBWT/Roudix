{ pkgs, ... }:
let
  telaIconsOut = "${pkgs.tela-icon-theme}/share/icons";

  telaSync = pkgs.writeShellScriptBin "noctalia-tela-sync" ''
    set -euo pipefail
    primaryFile="$HOME/.config/noctalia/generated/tela-primary.txt"
    [ -f "$primaryFile" ] || exit 0

    primary=$(tr -d '[:space:]' < "$primaryFile")
    case "$primary" in
      \#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
      *) exit 0 ;;
    esac

    dest="$HOME/.icons"
    mkdir -p "$dest"

    build=$(mktemp -d)
    trap 'rm -rf "$build"' EXIT

    # Étape 1 : Tela, Tela-light et Tela-dark dépendent les uns des autres via
    # des symlinks internes (ex: Tela-dark/scalable -> ../Tela/scalable). On
    # les copie tous les 3 comme frères SANS déréférencer (pas de -L) dans un
    # dossier temporaire, pour que ces symlinks restent valides -> contenu
    # complet, pas d'icônes d'app manquantes.
    for variant in Tela Tela-light Tela-dark; do
      mkdir -p "$build/$variant"
      # -L : le paquet tela-icon-theme build ~350 variantes de couleur en une
      # fois et déduplique les fichiers identiques entre elles via des
      # symlinks (jdupes). En ne prenant que ces 3 variantes, certains de ces
      # symlinks pointeraient vers une variante qu'on n'a pas copiée -> -L
      # résout tout vers du contenu réel, peu importe où il vit dans le store.
      cp -rL "${telaIconsOut}/$variant/." "$build/$variant/"
      chmod -R u+w "$build/$variant"
    done

    # On ne touche QUE les dossiers "places", à toutes les tailles.
    find "$build/Tela" "$build/Tela-light" "$build/Tela-dark" \
      -path '*/places/*.svg' -print0 \
      | xargs -0 ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g"

    # Étape 2 : maintenant que tout est correct et recoloré, on déréférence
    # (-L) vers les noms suffixés "-noctalia", qui deviennent des thèmes
    # autonomes et distincts des Tela/Tela-dark/Tela-light d'origine -> tu
    # gardes le choix entre les deux dans nwg-look.
    for variant in Tela Tela-light Tela-dark; do
      rm -rf "$dest/''${variant}-noctalia"
      mkdir -p "$dest/''${variant}-noctalia"
      cp -rL "$build/$variant/." "$dest/''${variant}-noctalia/"
      ${pkgs.gnused}/bin/sed -i "s/^Name=.*/Name=''${variant} Noctalia/" \
        "$dest/''${variant}-noctalia/index.theme"
      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest/''${variant}-noctalia" || true
      fi
    done
    # Thèmes générés dans ~/.icons/{Tela,Tela-light,Tela-dark}-noctalia, mais
    # pas appliqués automatiquement : choisis-les toi-même (nwg-look, etc.).
  '';
in
{
  home.packages = [ pkgs.tela-icon-theme telaSync pkgs.gnused ];

  xdg.configFile."noctalia/templates/tela-primary.tmpl".text =
    "{{colors.primary.default.hex}}";

  xdg.configFile."noctalia/50-tela-icons.toml".text = ''
    [theme.templates.user.tela_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${telaSync}/bin/noctalia-tela-sync"
  '';
}

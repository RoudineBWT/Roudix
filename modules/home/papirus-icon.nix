{ pkgs, ... }:
let
  papirusIconsOut = "${pkgs.papirus-icon-theme}/share/icons";

  papirusSync = pkgs.writeShellScriptBin "noctalia-papirus-sync" ''
    set -euo pipefail
    primaryFile="$HOME/.config/noctalia/generated/tela-primary.txt"
    [ -f "$primaryFile" ] || exit 0

    primary=$(tr -d '[:space:]' < "$primaryFile")
    case "$primary" in
      \#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
      *) exit 0 ;;
    esac

    # Papirus utilise 2 teintes par couleur : #5294e2 (corps) et #4877b1
    # (onglet, ~80% plus sombre). On calcule l'équivalent sombre de primary.
    hex="''${primary#\#}"
    r=$((16#''${hex:0:2})); g=$((16#''${hex:2:2})); b=$((16#''${hex:4:2}))
    r=$(( r * 80 / 100 )); g=$(( g * 80 / 100 )); b=$(( b * 80 / 100 ))
    darker=$(printf '#%02x%02x%02x' "$r" "$g" "$b")

    dest="$HOME/.icons"
    mkdir -p "$dest"

    build=$(mktemp -d)
    trap 'rm -rf "$build"' EXIT

    # Étape 1 : Papirus, Papirus-Light et Papirus-Dark dépendent les uns des
    # autres via des symlinks internes (ex: Papirus-Dark/48x48 ->
    # ../Papirus/48x48). On les copie tous les 3 comme frères SANS
    # déréférencer, dans un dossier temporaire, pour que ces symlinks
    # restent valides -> contenu complet, pas d'icônes d'app manquantes.
    for variant in Papirus Papirus-Light Papirus-Dark; do
      cp -r "$papirusIconsOut/$variant/." "$build/$variant/"
      chmod -R u+w "$build/$variant"
    done

    # On ne touche QUE les dossiers "places", à toutes les tailles.
    find "$build/Papirus" "$build/Papirus-Light" "$build/Papirus-Dark" \
      -path '*/places/*.svg' -print0 \
      | xargs -0 ${pkgs.gnused}/bin/sed -i \
          -e "s/#5294e2/$primary/g" \
          -e "s/#4877b1/$darker/g"

    # Étape 2 : déréférencement (-L) vers les noms suffixés "-noctalia",
    # thèmes autonomes distincts des Papirus/Papirus-Dark/Papirus-Light
    # d'origine -> tu gardes le choix entre les deux dans nwg-look.
    for variant in Papirus Papirus-Light Papirus-Dark; do
      rm -rf "$dest/${variant}-noctalia"
      cp -rL "$build/$variant/." "$dest/${variant}-noctalia/"
      ${pkgs.gnused}/bin/sed -i "s/^Name=.*/Name=${variant} Noctalia/" \
        "$dest/${variant}-noctalia/index.theme"
      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest/${variant}-noctalia" || true
      fi
    done
    # Thèmes générés dans ~/.icons/{Papirus,Papirus-Light,Papirus-Dark}-noctalia,
    # pas appliqués automatiquement : choisis-les toi-même (nwg-look).
  '';
in
{
  home.packages = [ pkgs.papirus-icon-theme papirusSync pkgs.gnused ];

  # Réutilise le template partagé défini dans tela-icon.nix
  # (~/.config/noctalia/templates/tela-primary.tmpl), avec son propre post_hook.
  xdg.configFile."noctalia/51-papirus-icons.toml".text = ''
    [theme.templates.user.papirus_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${papirusSync}/bin/noctalia-papirus-sync"
  '';
}

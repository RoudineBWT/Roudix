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

    for variant in Papirus Papirus-Light Papirus-Dark; do
      dest="$HOME/.icons/''${variant}-noctalia"
      rm -rf "$dest"
      mkdir -p "$dest"

      # On n'hérite du thème d'origine QUE pour ce qu'on ne fournit pas
      # nous-mêmes -> aucune copie des icônes d'apps, zéro risque de casse.
      cp "${papirusIconsOut}/$variant/index.theme" "$dest/index.theme"
      ${pkgs.gnused}/bin/sed -i \
        -e "s/^Inherits=.*/Inherits=$variant/" \
        -e "s/^Name=.*/Name=''${variant} Noctalia/" \
        "$dest/index.theme"

      # On ne copie QUE le dossier "places" de chaque taille disponible,
      # en déréférençant (-L) les symlinks internes/entre variantes
      # (ex: Papirus-Dark/48x48 -> ../Papirus/48x48).
      for size in 16x16 22x22 24x24 32x32 48x48 64x64 96x96 128x128 scalable symbolic; do
        src="${papirusIconsOut}/$variant/$size/places"
        [ -d "$src" ] || continue
        mkdir -p "$dest/$size/places"
        cp -rL "$src/." "$dest/$size/places/"
      done

      find "$dest" -path '*/places/*.svg' -print0 \
        | xargs -0 ${pkgs.gnused}/bin/sed -i \
            -e "s/#5294e2/$primary/g" \
            -e "s/#4877b1/$darker/g"

      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest" || true
      fi
    done
    # Thèmes générés dans ~/.icons/{Papirus,Papirus-Light,Papirus-Dark}-noctalia,
    # mais pas appliqués automatiquement : choisis-les toi-même (nwg-look).
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

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

    for variant in Tela Tela-light Tela-dark; do
      dest="$HOME/.icons/''${variant}-noctalia"
      rm -rf "$dest"
      mkdir -p "$dest"

      # On n'hérite du thème d'origine QUE pour ce qu'on ne fournit pas
      # nous-mêmes -> aucune copie des icônes d'apps, zéro risque de casse.
      cp "${telaIconsOut}/$variant/index.theme" "$dest/index.theme"
      ${pkgs.gnused}/bin/sed -i \
        -e "s/^Inherits=.*/Inherits=$variant/" \
        -e "s/^Name=.*/Name=''${variant} Noctalia/" \
        "$dest/index.theme"

      # On ne copie QUE le dossier "places" de chaque taille disponible,
      # en déréférençant (-L) les symlinks internes/entre variantes.
      for size in 16 22 24 32 scalable symbolic; do
        src="${telaIconsOut}/$variant/$size/places"
        [ -d "$src" ] || continue
        mkdir -p "$dest/$size/places"
        cp -rL "$src/." "$dest/$size/places/"
      done

      find "$dest" -path '*/places/*.svg' -print0 \
        | xargs -0 ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g"

      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest" || true
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

{ pkgs, ... }:
let
  # Papirus-Dark tel que buildé par nixpkgs (mv direct du repo upstream, donc
  # même piège que Tela : "places" et d'autres catégories sont des symlinks
  # vers le thème "Papirus" clair sibling). Contrairement à Tela, les fichiers
  # eux-mêmes ne sont PAS des alias entre eux (pas de folder.svg -> autre.svg).
  papirusDarkBase = "${pkgs.papirus-icon-theme}/share/icons/Papirus-Dark";

  papirusSync = pkgs.writeShellScriptBin "noctalia-papirus-sync" ''
    set -euo pipefail
    # Même fichier généré que pour Tela : juste le hex de "primary".
    primaryFile="$HOME/.config/noctalia/generated/tela-primary.txt"
    [ -f "$primaryFile" ] || exit 0

    primary=$(tr -d '[:space:]' < "$primaryFile")
    case "$primary" in
      \#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
      *) exit 0 ;;
    esac

    # Papirus utilise DEUX teintes par couleur : #5294e2 (corps, teinte
    # "normale") et #4877b1 (onglet du dessus, ~80% plus sombre). On calcule
    # l'équivalent sombre de la couleur primary pour garder le même effet 3D.
    hex="''${primary#\#}"
    r=$((16#''${hex:0:2})); g=$((16#''${hex:2:2})); b=$((16#''${hex:4:2}))
    r=$(( r * 80 / 100 )); g=$(( g * 80 / 100 )); b=$(( b * 80 / 100 ))
    darker=$(printf '#%02x%02x%02x' "$r" "$g" "$b")

    dest="$HOME/.icons/Papirus-Noctalia"
    rm -rf "$dest"
    mkdir -p "$dest"
    # -L : déréférence les symlinks de catégories (places, apps, devices...)
    # qui pointent vers le thème Papirus clair dans le store
    cp -rL "${papirusDarkBase}/." "$dest/"
    chmod -R u+w "$dest"

    ${pkgs.gnused}/bin/sed -i "s/^Name=.*/Name=Papirus Noctalia/" "$dest/index.theme"

    # On ne touche QUE les dossiers "places" (dossiers/emplacements), à toutes
    # les tailles, quel que soit le nom exact du fichier
    find "$dest" -path '*/places/*.svg' -print0 \
      | xargs -0 ${pkgs.gnused}/bin/sed -i \
          -e "s/#5294e2/$primary/g" \
          -e "s/#4877b1/$darker/g"

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
      gtk-update-icon-cache -f -t "$dest" || true
    fi

    ${pkgs.glib}/bin/gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Noctalia'
  '';
in
{
  home.packages = [ pkgs.papirus-icon-theme papirusSync pkgs.gnused pkgs.glib ];

  # Réutilise le même template que Tela (~/.config/noctalia/templates/tela-primary.tmpl,
  # défini dans tela-icon.nix) mais avec son propre post_hook.
  xdg.configFile."noctalia/51-papirus-icons.toml".text = ''
    [theme.templates.user.papirus_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${papirusSync}/bin/noctalia-papirus-sync"
  '';
}

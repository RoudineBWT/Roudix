{ pkgs, ... }:
let
  # Thème Tela-dark déjà construit par le vrai install.sh de vinceliuice
  # (index.theme valide, tailles/symlinks résolus, recolorage "dark" déjà appliqué)
  telaDarkBase = "${pkgs.tela-icon-theme}/share/icons/Tela-dark";

  telaSync = pkgs.writeShellScriptBin "noctalia-tela-sync" ''
    set -euo pipefail
    colors="$HOME/.config/noctalia/colors.json"
    [ -f "$colors" ] || exit 0

    primary=$(${pkgs.jq}/bin/jq -r '.mPrimary' "$colors")
    dest="$HOME/.icons/Tela-noctalia"

    rm -rf "$dest"
    mkdir -p "$dest"
    # -L : déréférence les symlinks (scalable/32/... pointent vers le thème Tela
    # standard dans le store) pour obtenir un thème autonome et copiable tel quel
    cp -rL "$telaDarkBase/." "$dest/"
    chmod -R u+w "$dest"

    # Nom lisible dans index.theme (par défaut "Tela dark")
    ${pkgs.gnused}/bin/sed -i "s/^Name=.*/Name=Tela Noctalia/" "$dest/index.theme"

    # On ne touche QUE les icônes de dossiers, tout le reste reste du Tela-dark pur
    ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g" \
      "$dest/scalable/places/"default-folder*.svg \
      "$dest/16/places/"folder*.svg \
      "$dest/22/places/"folder*.svg \
      "$dest/24/places/"folder*.svg

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
      gtk-update-icon-cache -f -t "$dest" || true
    fi

    ${pkgs.glib}/bin/gsettings set org.gnome.desktop.interface icon-theme 'Tela-noctalia'
  '';
in
{
  home.packages = [ pkgs.tela-icon-theme telaSync pkgs.jq pkgs.gnused pkgs.glib ];

  xdg.configFile."noctalia/hooks.toml".text = ''
    [hooks]
    colors_changed = ["${telaSync}/bin/noctalia-tela-sync"]
  '';
}

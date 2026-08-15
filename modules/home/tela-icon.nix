{ pkgs, ... }:
let
  telaSrc = pkgs.fetchFromGitHub {
    owner = "vinceliuice";
    repo = "Tela-icon-theme";
    rev = "sha256-e4Ysu9YE2jAib9+q9eYL0E3w1BBXbu/QYNTmSjk0CRY=";
    sha256 = "sha256-e4Ysu9YE2jAib9+q9eYL0E3w1BBXbu/QYNTmSjk0CRY=";
  };

  telaSync = pkgs.writeShellScriptBin "noctalia-tela-sync" ''
    set -euo pipefail
    colors="$HOME/.config/noctalia/colors.json"
    [ -f "$colors" ] || exit 0

    primary=$(${pkgs.jq}/bin/jq -r '.mPrimary' "$colors")
    dest="$HOME/.icons/Tela-noctalia"

    rm -rf "$dest"
    mkdir -p "$dest"
    cp -r ${telaSrc}/src/* "$dest/"
    chmod -R u+w "$dest"

    ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g" \
      "$dest/scalable/apps/"*.svg \
      "$dest/scalable/places/"default-*.svg \
      "$dest/16/places/"folder*.svg

    ${pkgs.glib}/bin/gsettings set org.gnome.desktop.interface icon-theme 'Tela-noctalia'
  '';
in
{
  home.packages = [ telaSync pkgs.jq pkgs.gnused pkgs.glib ];

  xdg.configFile."noctalia/hooks.toml".text = ''
    [hooks]
    colors_changed = ["${telaSync}/bin/noctalia-tela-sync"]
  '';
}

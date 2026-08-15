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
    workdir="$HOME/.cache/tela-icon-theme-src"

    mkdir -p "$workdir"
    cp -rn ${telaSrc}/* "$workdir/" 2>/dev/null || true
    chmod +x "$workdir/change_color.sh"

    "$workdir/change_color.sh" -a "$primary" -d "$HOME/.icons"
    ${pkgs.glib}/bin/gsettings set org.gnome.desktop.interface icon-theme 'Tela-noctalia'
  '';
in
{
  home.packages = [ telaSync pkgs.jq pkgs.glib ];

  xdg.configFile."noctalia/hooks.toml".text = ''
    [hooks]
    colors_changed = "${telaSync}/bin/noctalia-tela-sync"
  '';
}

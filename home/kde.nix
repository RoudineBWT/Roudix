{ lib, ... }:
let
  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/roudix-dark.svg";
  logoPath      = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
in
lib.mkIf (osConfig.roudix.desktop.type == "kde") {
  # ── Roudix KDE branding — fresh install only ─────────────────────────────
  #
  # Ce script s'exécute lors de `nixos-rebuild switch` via Home Manager,
  # AVANT que KDE démarre. Il écrit les configs uniquement si elles
  # n'existent pas encore → respecte les changements utilisateur après.
  #
  # Pour override perso, copier dans home/local.nix :
  #   home.activation.roudixKdeDefaults = lib.mkForce "";

  home.activation.roudixKdeDefaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PLASMA_CFG="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    if [ ! -f "$PLASMA_CFG" ]; then
      $DRY_RUN_CMD mkdir -p "$(dirname "$PLASMA_CFG")"
      $DRY_RUN_CMD cat > "$PLASMA_CFG" <<EOF
[Containments][2][Applets][3][Configuration][General]
icon=${logoPath}

[Containments][2][Wallpaper][org.kde.image][General]
Image=${wallpaperDark}
SlidePaths=/run/current-system/sw/share/wallpapers
EOF
    fi
  '';
}

{
  lib,
  stdenvNoCC,
  coreutils,
  bash,
  imagemagick,
}:

stdenvNoCC.mkDerivation {
  pname = "roudix-branding";
  version = "1.0.0";

  src = ../../assets;

  buildInputs = [ bash coreutils imagemagick ];

  installPhase = ''
    # ── Icônes (toutes tailles) ───────────────────────────────────────────────
    for SIZE in 16 32 48 64 128 256; do
      mkdir -p $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps

      # Logo principal
      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/roudix-logo.png

      # Icône menu KDE
      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/start-here-kde.png

      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/start-here.png
    done

    # ── Wallpapers (share/backgrounds pour SDDM + autres) ────────────────────
    mkdir -p $out/share/backgrounds/roudix
    cp $src/wallpapers/roudix-dark.svg $out/share/backgrounds/roudix/roudix-dark.svg
    cp $src/wallpapers/roudix-light.svg $out/share/backgrounds/roudix/roudix-light.svg

    # ── Wallpaper KDE (share/wallpapers pour le sélecteur KDE) ───────────────
    mkdir -p $out/share/wallpapers/Roudix/contents/images
    cp $src/wallpapers/roudix-dark.svg \
      $out/share/wallpapers/Roudix/contents/images/roudix-dark.svg
    cp $src/wallpapers/roudix-light.svg \
      $out/share/wallpapers/Roudix/contents/images/roudix-light.svg

    cat <<JSONEOF > $out/share/wallpapers/Roudix/metadata.json
{
  "KPlugin": {
    "Authors": [
      {
        "Name": "Roudix"
      }
    ],
    "Id": "Roudix",
    "License": "AGPL-3.0+",
    "Name": "Roudix",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "Roudix"
}
JSONEOF

    # ── Entrées GNOME background properties (paire dark/light) ───────────────
    mkdir -p $out/share/gnome-background-properties
    cat <<XMLEOF > $out/share/gnome-background-properties/roudix.xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">
<wallpapers>
  <wallpaper deleted="false">
    <name>Roudix</name>
    <filename>/run/current-system/sw/share/backgrounds/roudix/roudix-light.svg</filename>
    <filename-dark>/run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg</filename-dark>
    <options>zoom</options>
    <shade_type>solid</shade_type>
    <pcolor>#eff1f5</pcolor>
    <scolor>#1e1e2e</scolor>
  </wallpaper>
</wallpapers>
XMLEOF
  '';

  meta = {
    description = "Roudix branding";
    license = lib.licenses.agpl3Plus;
  };
}

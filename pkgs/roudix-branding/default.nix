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
    # ── Icônes PNG (toutes tailles) ───────────────────────────────────────────
    for SIZE in 16 32 48 64 128 256; do
      mkdir -p $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps

      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/roudix-logo.png

      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/start-here-kde.png

      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/start-here.png
    done

    # ── Icônes SVG scalable ───────────────────────────────────────────────────
    mkdir -p $out/share/icons/hicolor/scalable/apps

    cp $src/logo/roudix-logo.svg \
      $out/share/icons/hicolor/scalable/apps/roudix-logo.svg

    cp $src/logo/roudix-logo.svg \
      $out/share/icons/hicolor/scalable/apps/start-here-kde.svg

    cp $src/logo/roudix-logo.svg \
      $out/share/icons/hicolor/scalable/apps/start-here.svg

    cp $src/logo/roudix-logo.svg \
      $out/share/icons/hicolor/scalable/apps/start-here-kde-symbolic.svg

    # ── Icône symbolique Kickoff (priorité maximale) ──────────────────────────
    mkdir -p $out/share/icons/hicolor/symbolic/apps

    cp $src/logo/roudix-logo.svg \
      $out/share/icons/hicolor/symbolic/apps/start-here-kde-symbolic.svg

    # ── Wallpapers SVG (fallback) ─────────────────────────────────────────────
    mkdir -p $out/share/backgrounds/roudix
    cp $src/wallpapers/roudix-dark.svg $out/share/backgrounds/roudix/roudix-dark.svg
    cp $src/wallpapers/roudix-light.svg $out/share/backgrounds/roudix/roudix-light.svg
    cp $src/wallpapers/roudix_wallpaper_cosmos.svg $out/share/backgrounds/roudix/roudix_wallpaper_cosmos.svg
    cp $src/wallpapers/roudix_wallpaper_dark_logo.svg $out/share/backgrounds/roudix/roudix_wallpaper_dark_logo.svg
    cp $src/wallpapers/roudix_wallpaper_light_logo.svg $out/share/backgrounds/roudix/roudix_wallpaper_light_logo.svg

    # ── Wallpapers PNG GNOME (libpng/librsvg crash workaround) ────────────────
    # -strip                   : supprime les métadonnées et profils ICC
    # -define png:color-type=2 : force RGB sans canal alpha
    # -depth 8                 : force 8 bits par canal
    convert $src/wallpapers/roudix-dark.svg \
      -resize 3840x2160 \
      -strip \
      -define png:color-type=2 \
      -depth 8 \
      $out/share/backgrounds/roudix/roudix-dark.png

    convert $src/wallpapers/roudix-light.svg \
      -resize 3840x2160 \
      -strip \
      -define png:color-type=2 \
      -depth 8 \
      $out/share/backgrounds/roudix/roudix-light.png

      convert $src/wallpapers/roudix_wallpaper_cosmos.svg \
        -resize 3840x2160 \
        -strip \
        -define png:color-type=2 \
        -depth 8 \
        $out/share/backgrounds/roudix/roudix_wallpaper_cosmos.svg.png

        convert $src/wallpapers/roudix_wallpaper_dark_logo.svg \
          -resize 3840x2160 \
          -strip \
          -define png:color-type=2 \
          -depth 8 \
          $out/share/backgrounds/roudix/roudix_wallpaper_dark_logo.png

          convert $src/wallpapers/roudix_wallpaper_light_logo.svg \
            -resize 3840x2160 \
            -strip \
            -define png:color-type=2 \
            -depth 8 \
            $out/share/backgrounds/roudix/roudix_wallpaper_light_logo.png

    # ── Wallpaper KDE Dark ────────────────────────────────────────────────────
    mkdir -p $out/share/wallpapers/RoudixDark/contents/images

    convert $src/wallpapers/roudix-dark.svg \
      -resize 3840x2160 \
      $out/share/wallpapers/RoudixDark/contents/images/3840x2160.png

    convert $src/wallpapers/roudix-dark.svg \
      -resize 400x250 \
      $out/share/wallpapers/RoudixDark/contents/screenshot.png

    cat <<JSONEOF > $out/share/wallpapers/RoudixDark/metadata.json
{
  "KPlugin": {
    "Authors": [ { "Name": "Roudix" } ],
    "Id": "RoudixDark",
    "License": "AGPL-3.0+",
    "Name": "Roudix Dark",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "RoudixDark"
}
JSONEOF

    # ── Wallpaper KDE Light ───────────────────────────────────────────────────
    mkdir -p $out/share/wallpapers/RoudixLight/contents/images

    convert $src/wallpapers/roudix-light.svg \
      -resize 3840x2160 \
      $out/share/wallpapers/RoudixLight/contents/images/3840x2160.png

    convert $src/wallpapers/roudix-light.svg \
      -resize 400x250 \
      $out/share/wallpapers/RoudixLight/contents/screenshot.png

    cat <<JSONEOF > $out/share/wallpapers/RoudixLight/metadata.json
{
  "KPlugin": {
    "Authors": [ { "Name": "Roudix" } ],
    "Id": "RoudixLight",
    "License": "AGPL-3.0+",
    "Name": "Roudix Light",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "RoudixLight"
}
JSONEOF

    # ── Wallpaper KDE Cosmos ──────────────────────────────────────────────────
    mkdir -p $out/share/wallpapers/RoudixCosmos/contents/images

    convert $src/wallpapers/roudix_wallpaper_cosmos.svg \
      -resize 3840x2160 \
      $out/share/wallpapers/RoudixCosmos/contents/images/3840x2160.png

    convert $src/wallpapers/roudix_wallpaper_cosmos.svg \
      -resize 400x250 \
      $out/share/wallpapers/RoudixCosmos/contents/screenshot.png

    cat <<JSONEOF > $out/share/wallpapers/RoudixCosmos/metadata.json
{
  "KPlugin": {
    "Authors": [ { "Name": "Roudix" } ],
    "Id": "RoudixCosmos",
    "License": "AGPL-3.0+",
    "Name": "Roudix Cosmos",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "RoudixCosmos"
}
JSONEOF

    # ── Wallpaper KDE Dark Logo ───────────────────────────────────────────────
    mkdir -p $out/share/wallpapers/RoudixDarkLogo/contents/images

    convert $src/wallpapers/roudix_wallpaper_dark_logo.svg \
      -resize 3840x2160 \
      $out/share/wallpapers/RoudixDarkLogo/contents/images/3840x2160.png

    convert $src/wallpapers/roudix_wallpaper_dark_logo.svg \
      -resize 400x250 \
      $out/share/wallpapers/RoudixDarkLogo/contents/screenshot.png

    cat <<JSONEOF > $out/share/wallpapers/RoudixDarkLogo/metadata.json
{
  "KPlugin": {
    "Authors": [ { "Name": "Roudix" } ],
    "Id": "RoudixDarkLogo",
    "License": "AGPL-3.0+",
    "Name": "Roudix Dark Logo",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "RoudixDarkLogo"
}
JSONEOF

    # ── Wallpaper KDE Light Logo ──────────────────────────────────────────────
    mkdir -p $out/share/wallpapers/RoudixLightLogo/contents/images

    convert $src/wallpapers/roudix_wallpaper_light_logo.svg \
      -resize 3840x2160 \
      $out/share/wallpapers/RoudixLightLogo/contents/images/3840x2160.png

    convert $src/wallpapers/roudix_wallpaper_light_logo.svg \
      -resize 400x250 \
      $out/share/wallpapers/RoudixLightLogo/contents/screenshot.png

    cat <<JSONEOF > $out/share/wallpapers/RoudixLightLogo/metadata.json
{
  "KPlugin": {
    "Authors": [ { "Name": "Roudix" } ],
    "Id": "RoudixLightLogo",
    "License": "AGPL-3.0+",
    "Name": "Roudix Light Logo",
    "Version": "1.0"
  },
  "KPackageStructure": "Wallpaper/Images",
  "X-KDE-PluginInfo-Name": "RoudixLightLogo"
}
JSONEOF

    # ── Entrées GNOME background properties ───────────────────────────────────
    mkdir -p $out/share/gnome-background-properties
    cat <<XMLEOF > $out/share/gnome-background-properties/roudix.xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">
<wallpapers>
  <wallpaper deleted="false">
    <name>Roudix</name>
    <filename>/run/current-system/sw/share/backgrounds/roudix/roudix-light.png</filename>
    <filename-dark>/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png</filename-dark>
    <options>zoom</options>
    <shade_type>solid</shade_type>
    <pcolor>#eff1f5</pcolor>
    <scolor>#1e1e2e</scolor>
  </wallpaper>
  <wallpaper deleted="false">
    <name>Roudix Cosmos</name>
    <filename>/run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_cosmos.png</filename>
    <options>zoom</options>
    <shade_type>solid</shade_type>
    <pcolor>#1e1e2e</pcolor>
    <scolor>#1e1e2e</scolor>
  </wallpaper>
  <wallpaper deleted="false">
    <name>Roudix Logo</name>
    <filename>/run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_light_logo.png</filename>
    <filename-dark>/run/current-system/sw/share/backgrounds/roudix/roudix_wallpaper_dark_logo.png</filename-dark>
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

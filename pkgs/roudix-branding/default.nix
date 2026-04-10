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
    # PNGs rescalés
    for SIZE in 16 32 48 64 128 256; do
      mkdir -p $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps
      convert $src/logo/roudix-logo.png \
        -resize ''${SIZE}x''${SIZE} \
        $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/roudix-logo.png
    done
  '';

  meta = {
    description = "Roudix branding";
    license = lib.licenses.agpl3Plus;
  };
}

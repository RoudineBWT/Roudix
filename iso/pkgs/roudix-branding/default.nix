{ stdenvNoCC, ... }:

stdenvNoCC.mkDerivation {
  name = "roudix-branding";
  version = "1.0";
  src = ./.;

  installPhase = ''
    mkdir -p $out/share/icons/hicolor/256x256/apps
    mkdir -p $out/share/icons/hicolor/scalable/apps
    mkdir -p $out/share/pixmaps

    cp roudix-logo.png $out/share/icons/hicolor/256x256/apps/roudix-logo.png
    cp roudix-logo.svg $out/share/icons/hicolor/scalable/apps/roudix-logo.svg
    cp roudix-logo.png $out/share/pixmaps/roudix-logo.png
  '';
}

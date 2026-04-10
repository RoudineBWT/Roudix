{ lib, stdenvNoCC, coreutils, bash }:

stdenvNoCC.mkDerivation {
  pname = "roudix-branding";
  version = "1.0.0";

  src = ../../assets;

  buildInputs = [ bash coreutils ];

  installPhase = ''
    mkdir -p $out/share/icons/hicolor/scalable/apps
    cp $src/logo/roudix-logo.svg $out/share/icons/hicolor/scalable/apps/roudix-logo.svg
  '';

  meta = {
    description = "Roudix branding";
    license = lib.licenses.agpl3Plus;
  };
}

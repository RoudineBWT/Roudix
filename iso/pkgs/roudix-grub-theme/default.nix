{ stdenvNoCC, ... }:

stdenvNoCC.mkDerivation {
  name = "roudix-grub-theme";
  version = "1.0";
  src = ./.;

  installPhase = ''
    mkdir -p $out/roudix
    cp theme.txt $out/roudix/
    cp logo.png $out/roudix/
    cp select_*.png $out/roudix/
  '';
}

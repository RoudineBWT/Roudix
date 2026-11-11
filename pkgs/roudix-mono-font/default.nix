# pkgs/roudix-mono-font/default.nix
# Installe : RoudixMono Nerd Font Mono (terminaux), RoudixMono Nerd Font, RoudixSans Nerd Font Propo (interface)
{ stdenvNoCC, lib }:
stdenvNoCC.mkDerivation {
  pname = "roudix-fonts";
  version = "1.1.0";
  src = ./fonts;
  dontBuild = true;
  installPhase = ''
    runHook preInstall
    install -Dm444 -t $out/share/fonts/truetype \
      nerd-font-mono/*.ttf nerd-font/*.ttf sans-nerd-font-propo/*.ttf
    runHook postInstall
  '';
  meta = {
    description = "Roudix Mono and Roudix Sans: faceted fonts patched with Nerd Fonts glyphs";
    license = lib.licenses.ofl;
    platforms = lib.platforms.all;
  };
}

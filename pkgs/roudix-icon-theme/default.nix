# roudix-icon-theme — the native Roudix icon theme: `Roudix` (dark tiles) and
# `Roudix-Light` (cream tiles).
#
# Unlike Papirus-Roudix / Tela-Roudix (modules/system/desktop/icon-theme.nix),
# which only recolour a few stock icons, this one is drawn for Roudix: brand
# logos recoloured into the Roudix tile, Tela / Papirus app icons converted to
# the Roudix palette, Roudix folders, file-type pages, device and category
# icons, and the Roudix logo as `start-here`. See README.md for the details
# and LICENSES.md for the (mixed) licences — the icons converted from Tela /
# Papirus are GPL-3.0.
#
# UI icons (go-previous, edit-find, audio-volume-*, tray/panel...) are Papirus-Dark /
# Papirus-Light's 16/22/24 px monochrome actions/panel/status sets, embedded as-is
# (tools/add_papirus_ui.py) so they no longer depend on the parent theme. Whatever the
# theme still doesn't draw falls back to
# Papirus-Dark (Papirus-Light for the light variant), then Adwaita / Breeze /
# hicolor, so Papirus has to be installed next to it — icon-theme.nix and
# modules/home/theming/gtk-theme.nix do that.
#
#   nix build .#roudix-icon-theme   # -> result/share/icons/{Roudix,Roudix-Light}
#
# Regenerate the SVGs (needs Tela, Papirus, simple-icons and lucide-static
# checked out): see tools/build_roudix.py and README.md.
{ lib, stdenvNoCC }:

stdenvNoCC.mkDerivation {
  pname = "roudix-icon-theme";
  version = "1.6";

  src = ./.;

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/share/icons"
    # -a keeps the alias symlinks (relative, inside the same folder).
    cp -a Roudix Roudix-Light "$out/share/icons/"
    chmod -R u+w "$out/share/icons"

    sed -i 's/^Inherits=.*/Inherits=Papirus-Dark,Adwaita,breeze,hicolor/' \
      "$out/share/icons/Roudix/index.theme"
    sed -i 's/^Inherits=.*/Inherits=Papirus-Light,Adwaita,breeze,hicolor/' \
      "$out/share/icons/Roudix-Light/index.theme"

    runHook postInstall
  '';

  passthru = {
    themeName = "Roudix";
    themeNameLight = "Roudix-Light";
  };

  meta = {
    description = "Native Roudix icon theme (dark and light tiles, orange glyphs)";
    license = with lib.licenses; [ mit gpl3Only cc0 isc ];
    platforms = lib.platforms.all;
  };
}

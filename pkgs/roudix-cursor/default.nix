# roudix-cursor — Bibata Modern recoloured with the Roudix palette.
#
# Not a rebuild from the SVGs (that needs cbmp/Puppeteer): it takes the
# pre-rendered Bibata-Modern-Ice bitmaps shipped by nixpkgs (white fill, black
# outline, alpha preserved) and maps black -> outline colour, white -> accent
# colour with ImageMagick, then repacks them into an XCursor theme with ctgen.
#
# This is the *static* theme (system closure: greeter, GNOME, KDE, Cinnamon, and
# the fallback everywhere else). Colours come from assets/palette/Roudix.json.
# On Noctalia sessions modules/home/theming/bibata-cursor.nix regenerates the
# same theme at runtime from the live Noctalia palette and shadows this one in
# ~/.local/share/icons.
#
#   nix build .#roudix-cursor        # -> result/share/icons/Bibata-Modern-Roudix
#
# Approach borrowed from Ly-sec's cursor module.
{
  lib,
  stdenvNoCC,
  bibata-cursors,
  clickgen,
  imagemagick,
  # Override to build another colourway, e.g.
  #   callPackage ./. { accentColor = "#E0661A"; outlineColor = "#14100D"; }
  # NOT named `accent` / `outline`: callPackage fills any argument that exists
  # in pkgs even when it has a default, and pkgs.outline is the (unfree) wiki.
  accentColor ? null,
  outlineColor ? null
}:

let
  palette = (builtins.fromJSON (builtins.readFile ../../assets/palette/Roudix.json)).dark;

  accent' = if accentColor != null then accentColor else palette.mPrimary;
  outline' = if outlineColor != null then outlineColor else palette.terminal.background;

  themeName = "Bibata-Modern-Roudix";
in
stdenvNoCC.mkDerivation {
  pname = "roudix-cursor";
  inherit (bibata-cursors) version src;

  nativeBuildInputs = [
    clickgen
    imagemagick
  ];

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild

    install -dm0755 "bitmaps/${themeName}"
    cp -r ${bibata-cursors.bitmaps}/Bibata-Modern-Ice/. "bitmaps/${themeName}/"
    chmod -R u+w "bitmaps/${themeName}"

    # Ice = white fill (#FFFFFF) + black outline (#000000): +level-colors maps
    # black -> first colour, white -> second colour; anti-aliased edges are
    # interpolated and the alpha channel is left alone (-channel RGB).
    magick mogrify \
      -channel RGB \
      +level-colors '${outline'},${accent'}' \
      -type TrueColorAlpha \
      -define png:color-type=6 \
      "bitmaps/${themeName}"/*.png

    ctgen configs/normal/x.build.toml \
      -p x11 \
      -d "bitmaps/${themeName}" \
      -n '${themeName}' \
      -c 'Bibata Modern cursor in the Roudix palette'

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    install -dm0755 "$out/share/icons"
    cp -r "themes/${themeName}" "$out/share/icons/"

    runHook postInstall
  '';

  passthru = { inherit themeName; };

  meta = {
    description = "Bibata Modern cursor recoloured with the Roudix palette";
    homepage = "https://github.com/ful1e5/Bibata_Cursor";
    license = lib.licenses.gpl3Only;
    platforms = lib.platforms.linux;
  };
}

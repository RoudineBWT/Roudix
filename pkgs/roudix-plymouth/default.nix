{
  stdenvNoCC,
  imagemagick,
}:

# Plymouth boot splash: Roudix logo (assets/logo/roudix-logo.png) on the
# near-black brown used by the Limine menu, gently pulsing, with a thin
# progress bar and a LUKS password prompt.
#
# Every image is generated here from the logo (single source of truth), so the
# repo stays free of binary copies. Wire it up with roudix.boot.plymouth
# (modules/system/boot/plymouth.nix).
stdenvNoCC.mkDerivation {
  pname = "roudix-plymouth";
  version = "1.0.0";

  src = ../../assets;

  nativeBuildInputs = [ imagemagick ];

  dontUnpack = true;
  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    theme=$out/share/plymouth/themes/roudix
    mkdir -p "$theme"

    # ── Logo (256px: the script re-draws it ~50 times/s, keep it light) ─────
    magick $src/logo/roudix-logo.png -resize 256x256 "$theme/logo.png"

    # ── Progress bar: track + fill (same size, the fill is scaled in the script)
    magick -size 320x4 xc:none -fill '#3a2010' \
      -draw 'roundrectangle 0,0 319,3 2,2' "$theme/track.png"
    magick -size 320x4 xc:none -fill '#ff8c42' \
      -draw 'roundrectangle 0,0 319,3 2,2' "$theme/fill.png"

    # ── Password prompt: entry box + bullet ──────────────────────────────────
    magick -size 320x40 xc:none -fill '#2a160b' -stroke '#5c2a12' -strokewidth 1 \
      -draw 'roundrectangle 1,1 318,38 8,8' "$theme/box.png"
    magick -size 12x12 xc:none -fill '#f6e2c4' \
      -draw 'circle 6,6 6,0' "$theme/bullet.png"

    # ── Theme descriptor + script ────────────────────────────────────────────
    cat > "$theme/roudix.plymouth" <<DESC
    [Plymouth Theme]
    Name=Roudix
    Description=Roudix boot splash
    ModuleName=script

    [script]
    ImageDir=$theme
    ScriptFile=$theme/roudix.script
    DESC

    cp ${./roudix.script} "$theme/roudix.script"
  '';

  meta = {
    description = "Roudix Plymouth boot splash";
    platforms = [ "x86_64-linux" "aarch64-linux" ];
  };
}

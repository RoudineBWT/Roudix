{
  stdenvNoCC,
  imagemagick,
}:

# Plymouth boot splashes for Roudix. One package, five themes (pick one with
# roudix.boot.plymouth.theme, modules/system/boot/plymouth.nix):
#
#   roudix           logo, gentle pulse, thin progress bar        (default)
#   roudix-spin      logo turning slowly
#   roudix-gradient  warm gradient background + pulsing glow behind the logo
#   roudix-ember     embers rising, a 72-tick progress ring, logo in a growing glow
#   roudix-panda     Pandoudix, the mascot (waves; sleeps on shutdown; teary on messages)
#
# All of them share the Limine menu colours and a LUKS password prompt. Every
# image is generated here from the logo / mascot (no binary copies to maintain).
stdenvNoCC.mkDerivation {
  pname = "roudix-plymouth";
  version = "1.3.0";

  src = ../../assets;

  nativeBuildInputs = [ imagemagick ];

  dontUnpack = true;
  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    mascot=${../../assets/mascot}

    # common <theme> <description>: bar, password box, descriptor, script
    common() {
      theme=$out/share/plymouth/themes/$1
      mkdir -p "$theme"

      # Progress bar: track + fill (same size, the fill is scaled in the script)
      magick -size 320x4 xc:none -fill '#3a2010' \
        -draw 'roundrectangle 0,0 319,3 2,2' "$theme/track.png"
      magick -size 320x4 xc:none -fill '#ff8c42' \
        -draw 'roundrectangle 0,0 319,3 2,2' "$theme/fill.png"

      # Password prompt: entry box + bullet
      magick -size 320x40 xc:none -fill '#2a160b' -stroke '#5c2a12' -strokewidth 1 \
        -draw 'roundrectangle 1,1 318,38 8,8' "$theme/box.png"
      magick -size 12x12 xc:none -fill '#f6e2c4' \
        -draw 'circle 6,6 6,0' "$theme/bullet.png"

      cat > "$theme/$1.plymouth" <<DESC
    [Plymouth Theme]
    Name=$1
    Description=$2
    ModuleName=script

    [script]
    ImageDir=$theme
    ScriptFile=$theme/$1.script
    DESC
      cp ${./.}/$1.script "$theme/$1.script"
    }

    # ── roudix: pulsing logo ────────────────────────────────────────────────
    common roudix "Roudix boot splash"
    magick $src/logo/roudix-logo.png -resize 256x256 "$theme/logo.png"

    # ── roudix-spin: rotating logo (a bit smaller: it is re-drawn while turning)
    common roudix-spin "Roudix boot splash, rotating logo"
    magick $src/logo/roudix-logo.png -resize 224x224 "$theme/logo.png"

    # ── roudix-gradient: logo + radial glow ─────────────────────────────────
    common roudix-gradient "Roudix boot splash, gradient and glow"
    magick $src/logo/roudix-logo.png -resize 256x256 "$theme/logo.png"
    magick -size 720x720 xc:'#ff8c42' \
      \( -size 720x720 radial-gradient:'gray30-black' \) \
      -alpha off -compose copy_opacity -composite "$theme/glow.png"

    # ── roudix-ember: embers + progress ring + glow + vignette ──────────────
    common roudix-ember "Roudix boot splash, embers and progress ring"
    magick $src/logo/roudix-logo.png -resize 200x200 "$theme/logo.png"
    magick -size 720x720 xc:'#ff8c42' \
      \( -size 720x720 radial-gradient:'gray30-black' \) \
      -alpha off -compose copy_opacity -composite "$theme/glow.png"
    magick -size 960x540 xc:black \
      \( -size 960x540 radial-gradient:'gray10-gray85' \) \
      -alpha off -compose copy_opacity -composite "$theme/vignette.png"
    # Ember sprites (3 sizes): warm dot, opaque centre fading to transparent
    mkember() {
      magick -size $1x$1 xc:'#ffb35c' \
        \( -size $1x$1 radial-gradient:'white-black' \) \
        -alpha off -compose copy_opacity -composite "$theme/ember-$2.png"
    }
    mkember 6 s
    mkember 10 m
    mkember 16 l
    # Progress ring: 72 ticks, each pre-rotated (5° steps) in a 28x28 square
    # canvas — dim (under) and lit (on top, faded in by the script)
    for i in $(seq 0 71); do
      for v in "dim #3a2010" "lit #ff8c42"; do
        set -- $v
        magick -size 28x28 xc:none -fill "$2" -draw 'roundrectangle 12,5 15,22 1,1' \
          -background none -rotate $((i * 5)) +repage -gravity center -extent 28x28 \
          "$theme/tick-$1-$i.png"
      done
    done

    # ── roudix-panda: Pandoudix, 3 poses (cut-outs in assets/mascot) ────────
    common roudix-panda "Roudix boot splash, Pandoudix"
    magick $mascot/pandoudix-wave.png  -resize 320x320 "$theme/panda-wave.png"
    magick $mascot/pandoudix-sleep.png -resize 320x320 "$theme/panda-sleep.png"
    magick $mascot/pandoudix-tear.png  -resize 320x320 "$theme/panda-tear.png"
  '';

  meta = {
    description = "Roudix Plymouth boot splashes";
    platforms = [ "x86_64-linux" "aarch64-linux" ];
  };
}

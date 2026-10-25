#!/usr/bin/env bash
# detect-boot-aspect.sh — which Limine boot wallpaper format fits this machine?
#
# Looks at every connected screen (/sys/class/drm) and keeps the MAIN one =
# the one with the highest resolution (your main monitor is virtually always
# the biggest). Then picks the closest roudix.boot.wallpaperAspect value and
# suggests roudix.boot.menuResolution (Limine's menu resolution).
#
#   scripts/detect-boot-aspect.sh              screens found, main one, line to use
#   scripts/detect-boot-aspect.sh --aspect     only the value, e.g. 16x10   (for scripts)
#   scripts/detect-boot-aspect.sh --resolution only the main screen's WxH   (for scripts)
#   scripts/detect-boot-aspect.sh --count      only the number of connected screens (for scripts)
#   scripts/detect-boot-aspect.sh 2560x1440    same as no argument, for a given resolution
#
# The installers (roudix-installer, roudix-installer.sh) and roudix-switcher
# do the same detection and suggest the result. Exit code 1 = no screen found.
set -euo pipefail

DRM_ROOT="${ROUDIX_DRM_ROOT:-/sys/class/drm}"          # overridable, for tests
FB_SIZE="${ROUDIX_FB_SIZE:-/sys/class/graphics/fb0/virtual_size}"

# One "WxH" per connected screen (its first listed mode = preferred / native).
screens() {
  local st modes res
  for st in "$DRM_ROOT"/card*-*/status; do
    [ -r "$st" ] || continue
    [ "$(cat "$st" 2>/dev/null)" = "connected" ] || continue
    modes="$(dirname "$st")/modes"
    [ -r "$modes" ] || continue
    res="$(head -n1 "$modes" | grep -oE '^[0-9]+x[0-9]+' || true)"
    [ -n "$res" ] && echo "$res"
  done
  return 0
}

# Fallback when DRM exposes nothing (some VMs, bare framebuffer): "1920,1080".
framebuffer() {
  if [ -r "$FB_SIZE" ]; then
    tr ',' 'x' < "$FB_SIZE" | grep -oE '^[0-9]+x[0-9]+' || true
  fi
  return 0
}

# Highest resolution (width*height) of the WxH lines on stdin; first wins a tie.
biggest() {
  awk -Fx '{ p = $1 * $2; if (p > best) { best = p; res = $0 } } END { if (res != "") print res }'
}

# Closest wallpaper format for a WxH.
aspect_of() {
  local w=${1%x*} h=${1#*x}
  awk -v w="$w" -v h="$h" 'BEGIN {
    r = w / h
    n = split("16x9:1.7778 16x10:1.6 21x9:2.3333 4x3:1.3333", c, " ")
    best = ""; bd = 99
    for (i = 1; i <= n; i++) {
      split(c[i], p, ":"); d = r - p[2]; if (d < 0) d = -d
      if (d < bd) { bd = d; best = p[1] }
    }
    printf "%s", best
  }'
}

mode="text"
case "${1:-}" in
  --aspect)     mode="aspect";     shift ;;
  --resolution) mode="resolution"; shift ;;
  --count)      mode="count";      shift ;;
  -h|--help)    sed -n '2,17p' "$0"; exit 0 ;;
esac

if [ $# -ge 1 ]; then
  all="$1"                                     # given on the command line
else
  all="$(screens)"
  [ -n "$all" ] || all="$(framebuffer)"
fi

main="$(printf '%s\n' "$all" | grep -E '^[0-9]+x[0-9]+$' | biggest || true)"
if [ -z "$main" ]; then
  echo "No connected screen found. Pass a resolution: $0 1920x1080" >&2
  exit 1
fi
aspect="$(aspect_of "$main")"

case "$mode" in
  aspect)     echo "$aspect" ;;
  count)      printf '%s\n' "$all" | grep -cE '^[0-9]+x[0-9]+$' || true ;;
  resolution) echo "$main" ;;
  text)
    count="$(printf '%s\n' "$all" | grep -cE '^[0-9]+x[0-9]+$' || true)"
    if [ "$count" -gt 1 ]; then
      echo "Screens found:"
      printf '%s\n' "$all" | grep -E '^[0-9]+x[0-9]+$' | while read -r r; do
        if [ "$r" = "$main" ]; then echo "  $r   <- main (highest resolution)"; else echo "  $r"; fi
      done
      echo
    fi
    echo "Main screen: $main"
    echo "  roudix.boot.wallpaperAspect = \"$aspect\";"
    if [ "$count" -gt 1 ]; then
      echo "  roudix.boot.menuResolution  = \"$main\";   # several screens: without it Limine may pick the smaller one"
    else
      echo "  roudix.boot.menuResolution  = \"auto\";   # or \"$main\" to force it"
    fi
    ;;
esac

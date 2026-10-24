#!/usr/bin/env bash
# Detects the native resolution of the connected screen(s) and tells which
# roudix.boot.wallpaperAspect value to use.
#   ./detect-boot-aspect.sh              -> reads /sys/class/drm
#   ./detect-boot-aspect.sh 2560x1440    -> test with a given resolution
set -euo pipefail

pick() { # $1 = WxH
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

list=()
if [ $# -ge 1 ]; then
  list=("$1")
else
  for st in /sys/class/drm/card*-*/status; do
    [ -r "$st" ] || continue
    [ "$(cat "$st")" = "connected" ] || continue
    modes="$(dirname "$st")/modes"
    # first listed mode = preferred / native
    [ -r "$modes" ] && list+=("$(head -n1 "$modes")")
  done
fi

if [ ${#list[@]} -eq 0 ]; then
  echo "No connected screen found. Pass a resolution: $0 1920x1080" >&2
  exit 1
fi

for res in "${list[@]}"; do
  echo "$res  ->  roudix.boot.wallpaperAspect = \"$(pick "$res")\";"
done

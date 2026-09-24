# gamescope + Steam Big Picture, tuned like a console session. Started by
# roudix-gaming-session, in a loop.

export PATH="/run/wrappers/bin:/run/current-system/sw/bin:$PATH"

# gamescope (and so --mangoapp) is a sibling process of steam, not a child of
# the Steam wrapper, so it doesn't inherit the TZ set on Steam itself.
# Without an explicit TZ, mangoapp can show the wrong time in Big Picture.
export TZ="@tz@"

# Highest refresh rate of the connected display at its native resolution, so
# nothing is hardcoded for one particular monitor (175 Hz here, 60 Hz there).
# Native = largest resolution advertised by the EDID; the mode flagged
# "preferred" is usually the 60 Hz base one, higher rates being extra modes.
refresh_hz() {
  local hz
  hz=$(drm_info -j 2>/dev/null | jq -r '
    [ .[] | .connectors[]? | select(.status == 1) ] | .[0] as $c |
    if $c == null then empty else
      ($c.modes | max_by(.hdisplay * .vdisplay) | {hdisplay, vdisplay}) as $native |
      ([ $c.modes[] | select(.hdisplay == $native.hdisplay and .vdisplay == $native.vdisplay) | .vrefresh ] | max)
    end
  ' 2>/dev/null || true)

  # Fall back to 60 Hz if no active connector or invalid output.
  if [ -z "$hz" ] || ! printf '%s' "$hz" | grep -Eq '^[0-9]+$'; then
    hz=60
  fi
  printf '%s\n' "$hz"
}

@decky_setup@

exec gamescope --steam \
  --adaptive-sync \
  --hdr-enabled \
  --hdr-itm-enabled \
  --mangoapp \
  -r "$(refresh_hz)" @extra_args@ \
  -- steam -tenfoot -pipewire-dmabuf -steamos3 -gamepadui

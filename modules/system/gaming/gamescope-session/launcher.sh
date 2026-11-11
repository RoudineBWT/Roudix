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
      # 4096x2160 est ignoré par gamescope lui-même (g_badModes) : le garder
      # fausserait -r si un écran l affiche parmi ses modes.
      [ $c.modes[] | select(.hdisplay != 4096 or .vdisplay != 2160) ] as $modes |
      ($modes | max_by(.hdisplay * .vdisplay) | {hdisplay, vdisplay}) as $native |
      ([ $modes[] | select(.hdisplay == $native.hdisplay and .vdisplay == $native.vdisplay) | .vrefresh ] | max)
    end
  ' 2>/dev/null || true)

  # Fall back to 60 Hz if no active connector or invalid output.
  if [ -z "$hz" ] || ! printf '%s' "$hz" | grep -Eq '^[0-9]+$'; then
    hz=60
  fi
  printf '%s\n' "$hz"
}

# MangoApp + niveaux du réglage Steam « Performance overlay » : même contrat que
# gamescope-session-plus (ChimeraOS). Sans ces variables, Steam ne propose pas
# les niveaux et ne sait pas piloter MangoApp. Steam écrit le niveau choisi
# (preset=N) dans $MANGOHUD_CONFIGFILE ; le rendu de chaque niveau vient de
# ~/.config/MangoHud/presets.conf (modules/home/theming/mangohud.nix), que
# MangoApp lit quel que soit ce fichier. Il est réécrit à chaque démarrage :
# le niveau de départ est roudix.gaming.mangohud.defaultPreset.
export STEAM_MANGOAPP_PRESETS_SUPPORTED=1
export STEAM_USE_MANGOAPP=1
export STEAM_DISABLE_MANGOAPP_ATOM_WORKAROUND=1
MANGOHUD_CONFIGFILE="${XDG_RUNTIME_DIR:-/tmp}/roudix-mangoapp.conf"
export MANGOHUD_CONFIGFILE
echo "preset=@mango_preset@" > "$MANGOHUD_CONFIGFILE"

@decky_setup@

exec gamescope --steam \
  --adaptive-sync \
  --mangoapp \
  -r "$(refresh_hz)" @hdr_args@ @extra_args@ \
  -- steam -tenfoot -pipewire-dmabuf -steamos3 -gamepadui

# Wrapper started by the display manager in place of a desktop compositor
# (session "Steam (Gaming Mode)"). It stays alive for the whole login and
# alternates between gamescope + Steam Big Picture and the regular desktop:
#
#   greeter -> roudix-gaming-session
#     |-> gamescope + Steam Big Picture
#     |     "Switch to desktop" -> steamos-session-select -> Steam quits
#     |-> the wrapper starts the desktop
#     |     "Return to Gaming Mode" -> roudix-return-to-gaming-mode
#     |-> back to gamescope, and so on
#
# The two helper scripts only talk to this wrapper through a small intent
# file in XDG_RUNTIME_DIR: per-user, and wiped by logind at session end.
#
# Design borrowed from GLF-OS (gamescope.nix), itself inspired by
# kronflux/nixos-gaming and SteamOS' steamos-session-select.
#
# @-placeholders are filled in by gamescope-session.nix.

# Sessions started by greetd/other DMs don't always get the NixOS PATH.
export PATH="/run/wrappers/bin:/run/current-system/sw/bin:$PATH"

runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
state_file="$runtime_dir/steamos-session-select"
active_marker="$runtime_dir/roudix-gaming-session.active"

# The XDG_* variables are set by hand: the display manager filled in those
# of the "Steam" session, and without correction xdg-desktop-portal would
# pick a generic backend (broken screen sharing and file pickers on the
# desktop half of the session).
start_desktop() {
  @desktop_env@ @desktop_start@
}

# The desktop's start command returns as soon as the session ends, but the
# compositor is stopped in parallel by systemd --user and can linger for a
# few seconds. Restarting gamescope meanwhile makes it abort: it can't create
# its DRM backend until the device is released. So wait until none of our
# processes has a /dev/dri/card* node open anymore (root-owned holders such
# as logind are invisible to us, which is what we want), then one more second
# for the kernel to really release the device.
wait_for_display() {
  for _ in $(seq 1 60); do
    fuser -s /dev/dri/card* 2>/dev/null || break
    sleep 0.5
  done
  sleep 1
}

# Marker read by roudix-return-to-gaming-mode: outside this wrapper, logging
# out of the desktop doesn't lead back to Gaming Mode.
: > "$active_marker"
trap 'rm -f "$active_marker"' EXIT

# Consecutive immediate gamescope failures. Past 3, hand control back to the
# display manager: otherwise a gamescope that can't start is relaunched
# forever, leaving a core dump of 2 MB+ per turn until the disk is full while
# the user stares at a black screen with no way out.
failures=0

while true; do
  rm -f "$state_file"

  started=$(date +%s)
  @launcher@ || true
  ran_for=$(( $(date +%s) - started ))

  # No intent recorded: gamescope stopped by itself (crash, Steam update).
  # Restart Gaming Mode rather than leave a black screen. A run that really
  # lasted resets the counter; only immediate failures accumulate.
  if [ "$(cat "$state_file" 2>/dev/null || true)" != "desktop" ]; then
    if [ "$ran_for" -lt 10 ]; then
      failures=$((failures + 1))
      if [ "$failures" -ge 3 ]; then
        echo "roudix-gaming-session: gamescope failed $failures times in a row, back to the display manager" >&2
        exit 1
      fi
    else
      failures=0
    fi
    sleep 2
    continue
  fi

  failures=0
  rm -f "$state_file"
  start_desktop || true

  # The desktop closed. Plain logout (nothing requested): leave, the session
  # ends and the greeter takes over, like any ordinary desktop session.
  # Explicit "Return to Gaming Mode": loop back to gamescope without ever
  # showing the greeter.
  [ "$(cat "$state_file" 2>/dev/null || true)" = "gaming" ] || break

  wait_for_display
done

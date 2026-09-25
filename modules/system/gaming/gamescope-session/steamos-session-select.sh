# Called by Steam when the user picks "Switch to Desktop" in Big Picture.
# The argument Steam passes (plasma, desktop...) is ignored: Roudix has a
# single active desktop, chosen at build time (roudix.desktop.type).

runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
state_file="$runtime_dir/steamos-session-select"

printf 'desktop\n' > "$state_file"

# Clean Steam shutdown first: it saves its config and syncs the cloud before
# giving control back. gamescope exits on its own when its child steam goes.
steam -shutdown || true

# Safety net if steam ignores -shutdown (frozen client): terminate gamescope
# ourselves. SIGTERM, never SIGKILL, or the DRM lease isn't released and the
# desktop that follows starts on a black screen.
for _ in $(seq 1 10); do
  pgrep -x steam >/dev/null || exit 0
  sleep 1
done
pkill -TERM -x gamescope || true

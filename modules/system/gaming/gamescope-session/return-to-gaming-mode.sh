# Soft logout from the desktop, back to Gaming Mode. It only ends the desktop
# processes, the ones the wrapper waits for. Never loginctl terminate-session:
# that would kill the whole logind scope, wrapper included, and land on the
# greeter instead of Gaming Mode.

runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
state_file="$runtime_dir/steamos-session-select"
active_marker="$runtime_dir/roudix-gaming-session.active"

# Desktop opened straight from the greeter, not through the wrapper: logging
# out would lead back to the login screen, not to the game. Say so instead
# of closing the user's session by surprise.
if [ ! -e "$active_marker" ]; then
  notify-send \
    "Gaming Mode unavailable" \
    "This session wasn't started in Gaming Mode. Pick the \"Steam (Gaming Mode)\" session on the login screen." \
    || true
  exit 1
fi

printf 'gaming\n' > "$state_file"
@desktop_quit@

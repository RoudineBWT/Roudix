# roudix-update — manual counterpart of roudix-autoupdate (the `update` alias).
#
# Body of the script only: modules/system/nix/roudix-update.nix prepends
#   CONFIG_PATH, BRANCH, MIN_FREE_GB, FLATPAK_ENABLED, BUMP_INPUTS_DEFAULT
# and wraps everything in writeShellApplication (strict mode + shellcheck).
#
# Runs as the *normal user*, never as root: sudo is only used where needed.
# (The old `sudo nix flake update` alias left a root-owned, locally modified
# flake.lock in the user's checkout, which made roudix-autoupdate's
# `git merge --ff-only` refuse to run as soon as CI had bumped the lock.)

usage() {
  cat <<'EOF'
Usage: update [options]

Pulls the Roudix config, updates Flatpaks and rebuilds the system.
The flake.lock you get from git is the one CI already built and validated.

Options:
  -i, --inputs [NAME...]  Also bump flake inputs locally (all of them, or only
                          the named ones) before building. Bypasses the CI
                          validation: flake.lock becomes a local modification.
      --no-inputs         Do not bump flake inputs (when roudix.update.bumpInputs is on).
  -b, --boot              Apply on next boot instead of switching right now.
      --no-pull           Do not git pull the config.
      --no-flatpak        Do not update Flatpaks.
  -c, --check             Only report whether new commits are available.
  -h, --help              Show this help.

Examples:
  update                       pull + rebuild + switch
  update --boot                pull + rebuild, applied after the next reboot
  update --inputs              bump every flake input, then rebuild
  update --inputs nixpkgs      bump only nixpkgs, then rebuild
EOF
}

# ── Output helpers ──────────────────────────────────────────────────────────
if [ -t 1 ]; then
  BOLD=$'\e[1m'
  RED=$'\e[31m'
  YELLOW=$'\e[33m'
  BLUE=$'\e[34m'
  RESET=$'\e[0m'
else
  BOLD='' RED='' YELLOW='' BLUE='' RESET=''
fi

step() { printf '%s==>%s %s%s%s\n' "$BLUE" "$RESET" "$BOLD" "$*" "$RESET"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '%swarning:%s %s\n' "$YELLOW" "$RESET" "$*" >&2; }

# notify <icon> <summary> <body> — best effort (no session bus over SSH, etc.)
notify() {
  notify-send --app-name=Roudix --icon="$1" "$2" "$3" 2>/dev/null || true
}

die() {
  printf '%serror:%s %s\n' "$RED" "$RESET" "$*" >&2
  notify dialog-error "Roudix — Échec de la mise à jour" "$*"
  exit 1
}

# ── Arguments ───────────────────────────────────────────────────────────────
BUMP_INPUTS=$BUMP_INPUTS_DEFAULT
INPUT_NAMES=()
ACTION=switch
DO_PULL=1
DO_FLATPAK=$FLATPAK_ENABLED
CHECK_ONLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    -i | --inputs)
      BUMP_INPUTS=1
      shift
      while [ $# -gt 0 ] && [[ $1 != -* ]]; do
        INPUT_NAMES+=("$1")
        shift
      done
      ;;
    --no-inputs) BUMP_INPUTS=0; INPUT_NAMES=(); shift ;;
    -b | --boot) ACTION=boot; shift ;;
    --no-pull) DO_PULL=0; shift ;;
    --no-flatpak) DO_FLATPAK=0; shift ;;
    -c | --check) CHECK_ONLY=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *)
      printf 'update: unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

# ── Preflight ───────────────────────────────────────────────────────────────
[ "$(id -u)" -ne 0 ] || die "run this as your normal user, not root (sudo is used where needed)."
[ -d "$CONFIG_PATH" ] || die "config directory $CONFIG_PATH is missing."

IS_GIT=0
if git -C "$CONFIG_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  IS_GIT=1
fi

# Sets PULL_STATE: skipped | uptodate | behind | ahead | diverged
# (same fast-forward-only rules as roudix-autoupdate: local work is never touched)
inspect_remote() {
  local current local_rev remote_rev

  PULL_STATE=skipped
  if [ "$IS_GIT" -ne 1 ]; then
    info "$CONFIG_PATH is not a git checkout — nothing to pull."
    return 0
  fi

  # Only follow the tracked branch: merging origin/$BRANCH into a feature
  # branch you are working on would be a nasty surprise.
  current=$(git -C "$CONFIG_PATH" symbolic-ref --quiet --short HEAD || true)
  if [ "$current" != "$BRANCH" ]; then
    info "checked out: ${current:-detached HEAD}, tracked branch: $BRANCH — not pulling."
    return 0
  fi

  git -C "$CONFIG_PATH" fetch --quiet origin "$BRANCH" ||
    die "git fetch failed — offline? (use --no-pull to skip the pull)"

  local_rev=$(git -C "$CONFIG_PATH" rev-parse HEAD)
  remote_rev=$(git -C "$CONFIG_PATH" rev-parse "origin/$BRANCH")

  if [ "$local_rev" = "$remote_rev" ]; then
    PULL_STATE=uptodate
  elif git -C "$CONFIG_PATH" merge-base --is-ancestor "$remote_rev" "$local_rev"; then
    PULL_STATE=ahead
  elif git -C "$CONFIG_PATH" merge-base --is-ancestor "$local_rev" "$remote_rev"; then
    PULL_STATE=behind
  else
    PULL_STATE=diverged
  fi
}

report_pull_state() {
  case "$PULL_STATE" in
    uptodate) info "config already up to date with origin/$BRANCH." ;;
    ahead) info "you have local commits not pushed to origin/$BRANCH — nothing to pull." ;;
    diverged) warn "local history has diverged from origin/$BRANCH — not pulling, building what is on disk." ;;
    behind) info "$(git -C "$CONFIG_PATH" rev-list --count "HEAD..origin/$BRANCH") new commit(s) available on origin/$BRANCH." ;;
    *) ;;
  esac
}

if [ "$CHECK_ONLY" -eq 1 ]; then
  step "Checking origin/$BRANCH"
  inspect_remote
  report_pull_state
  exit 0
fi

if [ "$BUMP_INPUTS" -eq 1 ] && [ -e "$CONFIG_PATH/flake.lock" ] && [ ! -w "$CONFIG_PATH/flake.lock" ]; then
  die "flake.lock is not writable (probably root-owned by the old 'sudo nix flake update'). Fix: sudo chown \"$USER\" \"$CONFIG_PATH/flake.lock\""
fi

# One run at a time, shared with roudix-autoupdate: the lock is held on the
# config directory itself (a normal user cannot create files in /run/lock).
exec 9<"$CONFIG_PATH"
if ! flock --nonblock 9; then
  warn "another update (roudix-autoupdate or update) is already running."
  exit 75
fi

avail_gb=$(($(df --output=avail -k /nix/store | tail -n 1) / 1024 / 1024))
if [ "$avail_gb" -lt "$MIN_FREE_GB" ]; then
  die "only ${avail_gb}GB free on /nix/store, need ${MIN_FREE_GB}GB."
fi

# Ask for the sudo password once, up front (system Flatpaks, activation).
sudo -v || die "sudo authentication failed."

# ── Restore flake.lock if a bumped lock does not build ──────────────────────
LOCK_BACKUP=""
BUILD_OK=0

cleanup() {
  if [ -n "$LOCK_BACKUP" ] && [ -f "$LOCK_BACKUP" ]; then
    if [ "$BUILD_OK" -ne 1 ]; then
      if cp -p -- "$LOCK_BACKUP" "$CONFIG_PATH/flake.lock"; then
        warn "flake.lock restored to its state before this run."
      fi
    fi
    rm -f -- "$LOCK_BACKUP"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ── 1. Pull the config ──────────────────────────────────────────────────────
if [ "$DO_PULL" -eq 1 ]; then
  step "Pulling the config (origin/$BRANCH)"
  inspect_remote
  if [ "$PULL_STATE" = behind ]; then
    old_rev=$(git -C "$CONFIG_PATH" rev-parse HEAD)
    report_pull_state
    git -C "$CONFIG_PATH" merge --quiet --ff-only "origin/$BRANCH" ||
      die "git merge --ff-only failed — local modifications in the way? Check: git -C $CONFIG_PATH status (an old locally-bumped flake.lock: git -C $CONFIG_PATH checkout flake.lock)"
    git -C "$CONFIG_PATH" log --oneline --no-decorate -n 15 "$old_rev..HEAD" | sed 's/^/      /'
  else
    report_pull_state
  fi
fi

# ── 2. Bump flake inputs (opt-in) ───────────────────────────────────────────
if [ "$BUMP_INPUTS" -eq 1 ]; then
  if [ -f "$CONFIG_PATH/flake.lock" ]; then
    LOCK_BACKUP=$(mktemp)
    cp -p -- "$CONFIG_PATH/flake.lock" "$LOCK_BACKUP"
  fi
  if [ "${#INPUT_NAMES[@]}" -gt 0 ]; then
    step "Updating flake inputs: ${INPUT_NAMES[*]}"
  else
    step "Updating all flake inputs"
  fi
  nix flake update "${INPUT_NAMES[@]}" --flake "path:$CONFIG_PATH" ||
    die "nix flake update failed."
fi

# ── 3. Rebuild ──────────────────────────────────────────────────────────────
# No '#<attr>': nh picks the nixosConfigurations entry matching this machine's
# hostname (see the note in roudix-autoupdate).
step "Building the system (nh os $ACTION)"
nh os "$ACTION" --accept-flake-config "path:$CONFIG_PATH" ||
  die "build failed — the running system is untouched."
BUILD_OK=1

# ── 4. Flatpaks (never fatal) ───────────────────────────────────────────────
if [ "$DO_FLATPAK" -eq 1 ]; then
  if command -v flatpak >/dev/null 2>&1; then
    step "Updating Flatpaks"
    flatpak update --user --noninteractive -y ||
      warn "user Flatpak update failed — continuing."
    sudo "$(command -v flatpak)" update --system --noninteractive -y ||
      warn "system Flatpak update failed — continuing."
  else
    info "flatpak is not installed — skipping."
  fi
fi

# ── Summary ─────────────────────────────────────────────────────────────────
reboot_needed() {
  local part
  [ "$ACTION" = boot ] && return 0
  for part in kernel initrd kernel-modules; do
    if [ "$(readlink -f "/run/booted-system/$part")" != "$(readlink -f "/run/current-system/$part")" ]; then
      return 0
    fi
  done
  return 1
}

echo
step "Update complete"
if reboot_needed; then
  info "Reboot to finish applying the update."
  notify system-reboot "Roudix — Mise à jour terminée" "Redémarre pour appliquer la mise à jour."
else
  notify software-update-available "Roudix — Mise à jour terminée" "Le système est à jour."
fi

if [ "$IS_GIT" -eq 1 ] && ! git -C "$CONFIG_PATH" diff --quiet -- flake.lock; then
  warn "flake.lock differs from git. Commit and push it, or run: git -C $CONFIG_PATH checkout flake.lock"
  warn "(otherwise the next roudix-autoupdate pull may refuse to run if CI touched flake.lock in the meantime)"
fi

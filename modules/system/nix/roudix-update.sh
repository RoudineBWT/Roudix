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

# ── Language ────────────────────────────────────────────────────────────────
# Same rule as the other Roudix apps (L(fr, en)): French when the first
# non-empty of LC_ALL / LC_MESSAGES / LANG / LANGUAGE starts with "fr",
# English otherwise. (Not called LANG here: that would clobber the env var.)
UI_LANG=en
for _lang_var in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}" "${LANGUAGE:-}"; do
  if [ -n "$_lang_var" ]; then
    case "$_lang_var" in
      fr* | FR*) UI_LANG=fr ;;
      *) ;;
    esac
    break
  fi
done

# L <french> <english> — prints the one matching the detected language.
L() {
  if [ "$UI_LANG" = fr ]; then
    printf '%s' "$1"
  else
    printf '%s' "$2"
  fi
}

usage_en() {
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
  -n, --dry               Ask nh for a dry run: nothing is pulled, bumped,
                          activated or updated (Flatpaks included).
      --changes           Show what the next-boot system changes compared to
                          the running one (useful after an auto-update).
      --log               Show the log of the last run (output of every run is
                          kept in ~/.local/state/roudix/update.log).
  -h, --help              Show this help.

Examples:
  update                       pull + rebuild + switch
  update --boot                pull + rebuild, applied after the next reboot
  update --inputs              bump every flake input, then rebuild
  update --inputs nixpkgs      bump only nixpkgs, then rebuild
EOF
}

usage_fr() {
  cat <<'EOF'
Usage : update [options]

Récupère la config Roudix, met à jour les Flatpaks et reconstruit le système.
Le flake.lock obtenu via git est celui que la CI a déjà construit et validé.

Options :
  -i, --inputs [NOM...]   Met aussi à jour les inputs du flake en local (tous, ou
                          seulement ceux nommés) avant de construire. Contourne la
                          validation de la CI : flake.lock devient une modification locale.
      --no-inputs         Ne met pas à jour les inputs (si roudix.update.bumpInputs est activé).
  -b, --boot              Applique au prochain démarrage au lieu de basculer tout de suite.
      --no-pull           Ne fait pas de git pull de la config.
      --no-flatpak        Ne met pas à jour les Flatpaks.
  -c, --check             Indique seulement si de nouveaux commits sont disponibles.
  -n, --dry               Demande un essai à blanc à nh : rien n'est récupéré, mis à jour,
                          activé ni installé (Flatpaks compris).
      --changes           Montre ce que le système du prochain démarrage change par rapport
                          à celui en cours (utile après une mise à jour automatique).
      --log               Affiche le log de la dernière exécution (la sortie de chaque
                          exécution est conservée dans ~/.local/state/roudix/update.log).
  -h, --help              Affiche cette aide.

Exemples :
  update                       pull + rebuild + switch
  update --boot                pull + rebuild, appliqué après le prochain redémarrage
  update --inputs              met à jour tous les inputs du flake, puis rebuild
  update --inputs nixpkgs      met à jour seulement nixpkgs, puis rebuild
EOF
}

usage() {
  if [ "$UI_LANG" = fr ]; then usage_fr; else usage_en; fi
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
warn() { printf '%s%s%s %s\n' "$YELLOW" "$(L 'attention :' 'warning:')" "$RESET" "$*" >&2; }

# notify <icon> <summary> <body> — best effort (no session bus over SSH, etc.)
notify() {
  notify-send --app-name=Roudix --icon="$1" "$2" "$3" 2>/dev/null || true
}

die() {
  printf '%s%s%s %s\n' "$RED" "$(L 'erreur :' 'error:')" "$RESET" "$*" >&2
  if [ -n "${ROUDIX_UPDATE_LOGGING:-}" ]; then
    printf '    %s update --log\n' "$(L 'log de cette exécution :' 'log of this run:')" >&2
  fi
  notify dialog-error "$(L 'Roudix — Échec de la mise à jour' 'Roudix — Update failed')" "$*"
  exit 1
}

# ── Arguments ───────────────────────────────────────────────────────────────
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/roudix"
LOG_FILE="$LOG_DIR/update.log"
ORIG_ARGS=("$@") # the parsing loop below shifts them away; the log wrapper re-execs with them
DRY=0
SHOW_CHANGES=0
SHOW_LOG=0
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
    -n | --dry) DRY=1; shift ;;
    --changes) SHOW_CHANGES=1; shift ;;
    --log) SHOW_LOG=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *)
      printf 'update: %s: %s\n\n' "$(L 'option inconnue' 'unknown option')" "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

# ── Preflight ───────────────────────────────────────────────────────────────
[ "$(id -u)" -ne 0 ] || die "$(L "lance ça avec ton utilisateur normal, pas en root (sudo est utilisé quand il faut)." "run this as your normal user, not root (sudo is used where needed).")"
[ -d "$CONFIG_PATH" ] || die "$(L "le dossier de config $CONFIG_PATH est introuvable." "config directory $CONFIG_PATH is missing.")"

if [ "$SHOW_LOG" -eq 1 ]; then
  if [ ! -f "$LOG_FILE" ]; then
    printf 'update: %s (%s)\n' "$(L 'pas encore de log' 'no log yet')" "$LOG_FILE" >&2
    exit 1
  fi
  # script(1) records raw terminal output: strip colours and carriage returns.
  sed -E 's/\x1b\[[0-9;?]*[ -\/]*[@-~]//g; s/\r//g' "$LOG_FILE"
  exit 0
fi

if [ "$SHOW_CHANGES" -eq 1 ]; then
  if [ "$(readlink -f /run/current-system)" = "$(readlink -f /nix/var/nix/profiles/system)" ]; then
    info "$(L "le système du prochain démarrage est celui déjà en cours — rien en attente." "the next-boot system is the one already running — nothing pending.")"
  else
    step "$(L "Prochain démarrage vs système en cours" "Next boot vs running system")"
    nix store diff-closures /run/current-system /nix/var/nix/profiles/system
  fi
  # What the last auto-update brought, as written by roudix-autoupdate (feat/fix commits).
  LAST_CHANGES=/var/lib/roudix-autoupdate/last-changes.txt
  if [ -s "$LAST_CHANGES" ]; then
    step "$(L "Nouveautés de la dernière mise à jour automatique" "What the last automatic update brought")"
    sed 's/^/  • /' "$LAST_CHANGES"
  fi
  exit 0
fi

# A dry run changes nothing: no merge, no lock bump, no Flatpak update.
if [ "$DRY" -eq 1 ]; then
  BUMP_INPUTS=0
  DO_FLATPAK=0
fi

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
    info "$(L "$CONFIG_PATH n'est pas un dépôt git — rien à récupérer." "$CONFIG_PATH is not a git checkout — nothing to pull.")"
    return 0
  fi

  # Only follow the tracked branch: merging origin/$BRANCH into a feature
  # branch you are working on would be a nasty surprise.
  current=$(git -C "$CONFIG_PATH" symbolic-ref --quiet --short HEAD || true)
  if [ "$current" != "$BRANCH" ]; then
    info "$(L "branche actuelle : ${current:-HEAD détaché}, branche suivie : $BRANCH — pas de pull." "checked out: ${current:-detached HEAD}, tracked branch: $BRANCH — not pulling.")"
    return 0
  fi

  git -C "$CONFIG_PATH" fetch --quiet origin "$BRANCH" ||
    die "$(L "git fetch a échoué — hors ligne ? (utilise --no-pull pour ignorer le pull)" "git fetch failed — offline? (use --no-pull to skip the pull)")"

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
    uptodate) info "$(L "config déjà à jour avec origin/$BRANCH." "config already up to date with origin/$BRANCH.")" ;;
    ahead) info "$(L "tu as des commits locaux non poussés sur origin/$BRANCH — rien à récupérer." "you have local commits not pushed to origin/$BRANCH — nothing to pull.")" ;;
    diverged) warn "$(L "l'historique local a divergé de origin/$BRANCH — pas de pull, build de ce qui est sur le disque." "local history has diverged from origin/$BRANCH — not pulling, building what is on disk.")" ;;
    behind)
      n_new=$(git -C "$CONFIG_PATH" rev-list --count "HEAD..origin/$BRANCH")
      info "$(L "$n_new nouveau(x) commit(s) disponible(s) sur origin/$BRANCH." "$n_new new commit(s) available on origin/$BRANCH.")"
      ;;
    *) ;;
  esac
}

if [ "$CHECK_ONLY" -eq 1 ]; then
  step "$(L "Vérification de origin/$BRANCH" "Checking origin/$BRANCH")"
  inspect_remote
  report_pull_state
  exit 0
fi

# Keep this run's output (last run only) without losing the terminal: re-exec
# under script(1), which gives the child a pty so nh keeps its colours and
# progress bars. Read it back with `update --log`.
if [ -z "${ROUDIX_UPDATE_LOGGING:-}" ] && command -v script >/dev/null 2>&1 && mkdir -p "$LOG_DIR" 2>/dev/null; then
  export ROUDIX_UPDATE_LOGGING=1
  # script(1) runs the command through $SHELL: force bash, otherwise the user's
  # fish loads its conf.d (fastfetch...) before every run.
  exec env SHELL="$BASH" script -qefc "$(printf '%q ' "$0" "${ORIG_ARGS[@]}")" "$LOG_FILE"
fi

if [ "$BUMP_INPUTS" -eq 1 ] && [ -e "$CONFIG_PATH/flake.lock" ] && [ ! -w "$CONFIG_PATH/flake.lock" ]; then
  die "$(L "flake.lock n'est pas modifiable (probablement à root à cause de l'ancien 'sudo nix flake update'). Correction : sudo chown \"$USER\" \"$CONFIG_PATH/flake.lock\"" "flake.lock is not writable (probably root-owned by the old 'sudo nix flake update'). Fix: sudo chown \"$USER\" \"$CONFIG_PATH/flake.lock\"")"
fi

# One run at a time, shared with roudix-autoupdate: the lock is held on the
# config directory itself (a normal user cannot create files in /run/lock).
exec 9<"$CONFIG_PATH"
if ! flock --nonblock 9; then
  warn "$(L "une autre mise à jour (roudix-autoupdate ou update) est déjà en cours." "another update (roudix-autoupdate or update) is already running.")"
  exit 75
fi

avail_gb=$(($(df --output=avail -k /nix/store | tail -n 1) / 1024 / 1024))
if [ "$avail_gb" -lt "$MIN_FREE_GB" ]; then
  die "$(L "seulement ${avail_gb} Go libres sur /nix/store, il en faut ${MIN_FREE_GB} Go." "only ${avail_gb}GB free on /nix/store, need ${MIN_FREE_GB}GB.")"
fi

# Ask for the sudo password once, up front (system Flatpaks, activation).
if [ "$DRY" -eq 0 ]; then
  sudo -v || die "$(L "l'authentification sudo a échoué." "sudo authentication failed.")"
fi

# ── Restore flake.lock if a bumped lock does not build ──────────────────────
LOCK_BACKUP=""
BUILD_OK=0

cleanup() {
  if [ -n "$LOCK_BACKUP" ] && [ -f "$LOCK_BACKUP" ]; then
    if [ "$BUILD_OK" -ne 1 ]; then
      if cp -p -- "$LOCK_BACKUP" "$CONFIG_PATH/flake.lock"; then
        warn "$(L "flake.lock restauré dans son état d'avant cette exécution." "flake.lock restored to its state before this run.")"
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
  step "$(L "Récupération de la config (origin/$BRANCH)" "Pulling the config (origin/$BRANCH)")"
  inspect_remote
  if [ "$PULL_STATE" = behind ] && [ "$DRY" -eq 0 ]; then
    old_rev=$(git -C "$CONFIG_PATH" rev-parse HEAD)
    report_pull_state
    git -C "$CONFIG_PATH" merge --quiet --ff-only "origin/$BRANCH" ||
      die "$(L "git merge --ff-only a échoué — des modifications locales gênent ? Vérifie : git -C $CONFIG_PATH status (ancien flake.lock mis à jour en local : git -C $CONFIG_PATH checkout flake.lock)" "git merge --ff-only failed — local modifications in the way? Check: git -C $CONFIG_PATH status (an old locally-bumped flake.lock: git -C $CONFIG_PATH checkout flake.lock)")"
    git -C "$CONFIG_PATH" log --oneline --no-decorate -n 15 "$old_rev..HEAD" | sed 's/^/      /'
  else
    report_pull_state
    if [ "$PULL_STATE" = behind ]; then
      info "$(L "(essai à blanc : pas de pull — build de ce qui est sur le disque)" "(dry run: not pulling — building what is on disk)")"
    fi
  fi
fi

# ── 2. Bump flake inputs (opt-in) ───────────────────────────────────────────
if [ "$BUMP_INPUTS" -eq 1 ]; then
  if [ -f "$CONFIG_PATH/flake.lock" ]; then
    LOCK_BACKUP=$(mktemp)
    cp -p -- "$CONFIG_PATH/flake.lock" "$LOCK_BACKUP"
  fi
  if [ "${#INPUT_NAMES[@]}" -gt 0 ]; then
    step "$(L "Mise à jour des inputs du flake : ${INPUT_NAMES[*]}" "Updating flake inputs: ${INPUT_NAMES[*]}")"
  else
    step "$(L "Mise à jour de tous les inputs du flake" "Updating all flake inputs")"
  fi
  nix flake update "${INPUT_NAMES[@]}" --flake "path:$CONFIG_PATH" ||
    die "$(L "nix flake update a échoué." "nix flake update failed.")"
fi

# ── 3. Rebuild ──────────────────────────────────────────────────────────────
# No '#<attr>': nh picks the nixosConfigurations entry matching this machine's
# hostname (see the note in roudix-autoupdate).
DRY_FLAG=()
if [ "$DRY" -eq 1 ]; then
  DRY_FLAG=(--dry)
  step "$(L "Essai à blanc (nh os $ACTION --dry)" "Dry run (nh os $ACTION --dry)")"
else
  step "$(L "Construction du système (nh os $ACTION)" "Building the system (nh os $ACTION)")"
fi
nh os "$ACTION" "${DRY_FLAG[@]}" --accept-flake-config "path:$CONFIG_PATH" ||
  die "$(L "le build a échoué — le système en cours n'est pas modifié." "build failed — the running system is untouched.")"
BUILD_OK=1

if [ "$DRY" -eq 1 ]; then
  echo
  step "$(L "Essai à blanc terminé — rien n'a été récupéré, mis à jour, activé ni installé" "Dry run complete — nothing was pulled, bumped, activated or updated")"
  exit 0
fi

# ── 4. Flatpaks (never fatal) ───────────────────────────────────────────────
if [ "$DO_FLATPAK" -eq 1 ]; then
  if command -v flatpak >/dev/null 2>&1; then
    step "$(L "Mise à jour des Flatpaks (et suppression des runtimes inutilisés)" "Updating Flatpaks (and removing unused runtimes)")"
    flatpak update --user --noninteractive -y ||
      warn "$(L "la mise à jour des Flatpaks utilisateur a échoué — on continue." "user Flatpak update failed — continuing.")"
    sudo "$(command -v flatpak)" update --system --noninteractive -y ||
      warn "$(L "la mise à jour des Flatpaks système a échoué — on continue." "system Flatpak update failed — continuing.")"
    flatpak uninstall --user --unused --noninteractive -y ||
      warn "$(L "impossible de supprimer les runtimes Flatpak utilisateur inutilisés — on continue." "could not remove unused user Flatpak runtimes — continuing.")"
    sudo "$(command -v flatpak)" uninstall --system --unused --noninteractive -y ||
      warn "$(L "impossible de supprimer les runtimes Flatpak système inutilisés — on continue." "could not remove unused system Flatpak runtimes — continuing.")"
  else
    info "$(L "flatpak n'est pas installé — ignoré." "flatpak is not installed — skipping.")"
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
step "$(L "Mise à jour terminée" "Update complete")"
if reboot_needed; then
  info "$(L "Redémarre pour finir d'appliquer la mise à jour." "Reboot to finish applying the update.")"
  notify system-reboot "$(L 'Roudix — Mise à jour terminée' 'Roudix — Update complete')" "$(L 'Redémarre pour appliquer la mise à jour.' 'Reboot to apply the update.')"
else
  notify software-update-available "$(L 'Roudix — Mise à jour terminée' 'Roudix — Update complete')" "$(L 'Le système est à jour.' 'The system is up to date.')"
fi

if [ "$IS_GIT" -eq 1 ] && ! git -C "$CONFIG_PATH" diff --quiet -- flake.lock; then
  warn "$(L "flake.lock diffère de git. Commit et push-le, ou lance : git -C $CONFIG_PATH checkout flake.lock" "flake.lock differs from git. Commit and push it, or run: git -C $CONFIG_PATH checkout flake.lock")"
  warn "$(L "(sinon le prochain pull de roudix-autoupdate peut refuser de tourner si la CI a touché flake.lock entre-temps)" "(otherwise the next roudix-autoupdate pull may refuse to run if CI touched flake.lock in the meantime)")"
fi

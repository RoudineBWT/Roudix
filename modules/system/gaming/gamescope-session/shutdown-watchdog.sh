# Filet de sécurité pour "Passer au bureau", lancé en tâche de fond par
# steamos-session-select (jamais au premier plan, voir ce script pour
# pourquoi). Ferme Steam proprement, puis force gamescope si besoin.

runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
state_file="$runtime_dir/steamos-session-select"

log() { logger -t roudix-gaming-session "$1"; }

# mangoapp plante s'il perd Xwayland avant de se terminer lui-même
# (popup de crash). On le coupe avant que Steam/gamescope ne partent.
pkill -TERM -f '^mangoapp( |$)' || true

# Arrêt propre : Steam enregistre sa config et synchronise le cloud.
# gamescope se termine tout seul quand son enfant steam s'en va.
steam -shutdown || true

# gamescope est wrappé par Nix (wrapProgram) : le nom du processus qui
# tourne réellement est tronqué à ".gamescope-wrap" (limite de 15
# caractères sur comm), donc pgrep/pkill -x gamescope ne trouve jamais
# rien. On filtre sur la ligne de commande à la place ; l'espace après
# "gamescope" évite d'attraper gamescope-wsi ou un wrapper de session.
for _ in $(seq 1 80); do
  pgrep -f '^gamescope ' >/dev/null 2>&1 || { log "gamescope terminé"; exit 0; }
  sleep 0.25
done

# Le fichier d'intention a pu être effacé par un retour au jeu entre-temps :
# dans ce cas, un gamescope encore présent est celui du jeu qui reprend, le
# terminer serait une régression.
[ "$(cat "$state_file" 2>/dev/null || true)" = "desktop" ] || exit 0

# Steam est figé. SIGTERM et jamais SIGKILL : sans libération propre du
# bail DRM, le bureau qui suit démarre sur un écran noir.
log "gamescope toujours présent après 20s, envoi de SIGTERM"
pkill -TERM -f '^gamescope ' || true

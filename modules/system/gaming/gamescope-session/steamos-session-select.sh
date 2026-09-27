# Appelé par Steam quand on choisit "Passer au bureau" dans Big Picture.
# L'argument transmis par Steam (plasma, desktop...) est ignoré : Roudix a
# un seul bureau actif, choisi au build (roudix.desktop.type).
#
# Doit rendre la main tout de suite : Steam attend la fin de ce script
# avant de poursuivre son propre arrêt, donc toute attente ici retarde
# exactement ce qu'elle est censée attendre. Le vrai travail (fermeture
# de Steam, filet de sécurité gamescope) part en tâche de fond, détaché
# de ce script, dans shutdown-watchdog.sh.

runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
state_file="$runtime_dir/steamos-session-select"

printf 'desktop\n' > "$state_file"

# setsid --fork : le filet de sécurité survit à la fin de ce script (et à
# celle de Steam et de gamescope) sans le retenir.
setsid --fork @watchdog@ >/dev/null 2>&1 || true

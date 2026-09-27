#!/usr/bin/env bash
# Toggle "mode jeu" : coupe animations/flou/ombres/rounding le temps de jouer,
# hyprctl reload restaure tout depuis le config Lua compilé.

STATE_FILE="/tmp/roudix-gamemode"

if [ -f "$STATE_FILE" ]; then
    hyprctl reload
    rm -f "$STATE_FILE"
    notify-send "Roudix" "Mode jeu désactivé" -i input-gaming
else
    hyprctl --batch "\
        keyword animations:enabled 0; \
        keyword decoration:blur:enabled 0; \
        keyword decoration:shadow:enabled 0; \
        keyword decoration:rounding 0; \
        keyword general:gaps_in 0; \
        keyword general:gaps_out 0; \
        keyword debug:vfr 1; \
        keyword misc:vrr 0"
    touch "$STATE_FILE"
    notify-send "Roudix" "Mode jeu activé" -i input-gaming
fi

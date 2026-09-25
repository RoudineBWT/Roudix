-- Roudix - Applications par défaut
-- Repris de niri-noc-v5 (terminal ghostty, nautilus, brave/zen)

TERMINAL      = "ghostty"
FILE_MANAGER  = "nautilus"          -- remplace dolphin du template CachyOS
BROWSER       = "brave-origin-beta" -- MOD+B dans ton niri
BROWSER_ALT   = "zen-twilight"      -- MOD+SHIFT+B dans ton niri
EDITOR        = "gnome-text-editor --new-window"
CALCULATOR    = "gnome-calculator"
MEDIA_PLAYER  = "clapper"           -- remplace mpv/haruna comme lecteur par défaut

-- Si tu n'utilises pas UWSM pour Hyprland, mets launchPrefix = "" dans keybinds.lua

-- Utilisé par windowrules.lua (règles .exe/launcher) ; ton monitors.lua code les sorties
-- en dur (DP-1/DP-3) plutôt que de passer par des variables MONITOR1/2/3 comme CachyOS,
-- donc cette variable doit être déclarée séparément ici.
PRIMARY_MONITOR = "DP-1" -- Legion 27Q-10, 2560x1440@240

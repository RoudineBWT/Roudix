-- Workspace rules wiki https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- Parité complète avec dotfiles/niri-noc-v5/cfg/rules.kdl
-- Les noms de workspaces SONT les glyphes Nerd Font (comme en Niri) : pas de mapping
-- icône séparé côté Noctalia, l'icône est directement le "name" lu par le widget workspaces.
-- Glyphes écrits en \u{XXXX} (échappement Lua natif) plutôt qu'en brut : certains
-- codepoints de la zone privée Unicode (U+E000-U+F8FF) étaient corrompus/supprimés
-- en UTF-8 littéral selon l'éditeur/pipeline utilisé pour écrire le fichier.
-- Adapte "monitor" aux noms confirmés par `hyprctl monitors`

-- Moniteur principal (équivalent "Lenovo Group Limited Legion 27Q-10 UNA07260" en Niri)
hl.workspace_rule({ workspace = "name:\u{f0239}", monitor = "DP-1", default = true }) -- web (Firefox/Zen/Brave)
hl.workspace_rule({ workspace = "name:\u{e8da}",   monitor = "DP-1" })                 -- code (Zed)
hl.workspace_rule({ workspace = "name:\u{e795}",   monitor = "DP-1" })                 -- term (kitty/Ptyxis)
hl.workspace_rule({ workspace = "name:\u{f0297}",  monitor = "DP-1" })                 -- gaming (Steam)
hl.workspace_rule({ workspace = "name:\u{f024b}",  monitor = "DP-1" })                 -- files (Nautilus)

-- Moniteur secondaire (équivalent "HKC OVERSEAS LIMITED 24E4 0000000000001" en Niri)
hl.workspace_rule({ workspace = "name:\u{f1ff}",  monitor = "DP-3" })                 -- comm (Discord/Element)
hl.workspace_rule({ workspace = "name:\u{f075a}", monitor = "DP-3" })                 -- music (Spotify/easyeffects)
hl.workspace_rule({ workspace = "name:\u{e743}",  monitor = "DP-3" })                 -- chat (Telegram)

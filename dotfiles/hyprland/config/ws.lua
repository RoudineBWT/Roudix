-- ws.lua — table de workspaces partagée, équivalent Hyprland de
-- niri/_ws.nix (mêmes glyphes Nerd Font, même rôle : source unique pour
-- workspaces.lua, binds/common.lua et rules/*.lua, pour éviter les copier-
-- coller de glyphes divergents entre fichiers).
--
-- POURQUOI (bug d'ordre corrigé ici) :
-- Hyprland ne permet pas de fixer l'id d'un workspace *nommé*
-- (hyprwm/Hyprland#665) : un "name:xxx" reçoit le prochain id libre dans
-- l'ordre de *création à l'exécution*, pas dans l'ordre écrit ici — donc
-- l'ordre affiché par la barre Noctalia dépendait de quel workspace était
-- focus en premier, pas de ce fichier. Discussion upstream confirmée en
-- 2026 (hyprwm/Hyprland#14520) : "named workspaces do not have a stable ID".
-- C'est exactement le piège que niri/_output.nix a déjà contourné côté
-- niri avec la clé numérique "1-glyph"/"2-glyph" (id = ordre de tri) et
-- `name` séparé (juste l'icône affichée).
--
-- Fix Hyprland : ne plus cibler les workspaces par `name:<glyphe>` (id
-- instable) mais par id numérique brut (id stable, PAS besoin d'astuce
-- de tri comme niri, l'ordre numérique suffit) ; le glyphe ne sert plus
-- que de `default_name` cosmétique sur un workspace_rule persistent.
-- Recommandation officielle Noctalia pour Hyprland :
-- https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/#persistent-workspaces
local ws = {}

-- Ordre = id (le tableau EST la clé de tri, comme les clés "N-glyphe" de
-- niri/_output.nix). Ajouter/retirer un workspace ici suffit : id et binds
-- (Mod+N) suivent automatiquement dans binds/common.lua.
local order = {
    { key = "web",   glyph = "\u{f0239}", monitor = "DP-1" }, -- Firefox/Zen/Brave
    { key = "code",  glyph = "\u{e8da}",  monitor = "DP-1" }, -- Zed
    { key = "term",  glyph = "\u{e795}",  monitor = "DP-1" }, -- kitty/Ptyxis
    { key = "games", glyph = "\u{f0297}", monitor = "DP-1" }, -- Steam
    { key = "files", glyph = "\u{f024b}", monitor = "DP-1" }, -- Nautilus
    { key = "comm",  glyph = "\u{f1ff}",  monitor = "DP-3" }, -- Discord/Element
    { key = "chat",  glyph = "\u{e743}",  monitor = "DP-3" }, -- Telegram
    { key = "music", glyph = "\u{f075a}", monitor = "DP-3" }, -- Spotify/EasyEffects
}

for i, w in ipairs(order) do
    ws[w.key] = { id = i, glyph = w.glyph, monitor = w.monitor }
end

-- Exposé pour itérer dans l'ordre (workspaces.lua, binds/common.lua) sans
-- dépendre de l'ordre non garanti de pairs() sur une table indexée par nom.
ws.__order = order

return ws

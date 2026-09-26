-- nix-noctalia.lua — charge le thème généré par Noctalia (matugen) via le
-- template enregistré par hyprland/_include-noctalia.nix. Ce fichier est un
-- dotfile normal (versionné), pas Nix-généré : c'est ~/.config/hypr/noctalia.lua
-- (écrit par matugen) qui est dynamique et régénéré à chaque changement de
-- wallpaper.
--
-- Le fichier généré ne renvoie PAS un mapping plat de couleurs : il renvoie
-- { colors = {...}, apply_theme = function }. apply_theme() construit et
-- appelle déjà lui-même hl.config() en interne (bordures + groupes de
-- fenêtres), donc on se contente de l'invoquer — c'est l'équivalent Hyprland
-- de l'`include` KDL de niri / `settings.include.files` d'umbriel.
--
-- pcall : no-op silencieux tant que Noctalia n'a pas encore tourné une
-- première fois (le fichier n'existe pas), ou si le shell actif n'est pas
-- Noctalia.
local home = os.getenv("HOME")
local ok, theme = pcall(dofile, home .. "/.config/hypr/noctalia.lua")

if ok and type(theme) == "table" and type(theme.apply_theme) == "function" then
    theme.apply_theme()
end

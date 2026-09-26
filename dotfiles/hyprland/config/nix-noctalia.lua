-- nix-noctalia.lua — charge les couleurs générées par Noctalia (matugen) via
-- le template enregistré par hyprland/_include-noctalia.nix. Ce fichier est
-- un dotfile normal (versionné), pas Nix-généré : c'est
-- ~/.config/hypr/noctalia/colors.lua (écrit par matugen) qui est dynamique.
--
-- pcall(dofile, ...) : no-op silencieux tant que Noctalia n'a pas encore
-- tourné une première fois (le fichier n'existe pas), ou si le shell actif
-- n'est pas Noctalia.
local home = os.getenv("HOME")
local ok, colors = pcall(dofile, home .. "/.config/hypr/noctalia.lua")

if ok and type(colors) == "table" then
    hl.config({
        general = {
            ["col.active_border"] = colors.active_border,
            ["col.inactive_border"] = colors.inactive_border,
        },
    })
end

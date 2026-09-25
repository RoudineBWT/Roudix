-- Look & feel, portés du focus-ring/border teal de noctalia.kdl

hl.config({
    general = {
        border_size = 1,
        extend_border_grab_area = 10,
        resize_on_border = true,
        col = {
            active_border = { colors = { ROUDIX_ACCENT, ROUDIX_ACCENT2 }, angle = 45 },
            inactive_border = ROUDIX_BG,
        },
    },
    -- Couleurs des groupes (mainMod+W / togglegroup dans keybinds.lua) : sans ce bloc,
    -- Hyprland utilise ses couleurs par défaut au lieu du thème teal (repris de CachyOS,
    -- palette adaptée à ROUDIX_ACCENT).
    group = {
        col = {
            border_active = ROUDIX_ACCENT,
            border_inactive = ROUDIX_BG,
            border_locked_active = ROUDIX_ACCENT2,
            border_locked_inactive = ROUDIX_BG,
        },
        groupbar = {
            col = {
                active = ROUDIX_ACCENT,
                inactive = ROUDIX_BG,
                locked_active = ROUDIX_ACCENT2,
                locked_inactive = ROUDIX_BG,
            },
        },
    },
    decoration = {
        dim_special = 0.3,
        rounding = 0,
        active_opacity = 0.95,
        inactive_opacity = 0.85,
        fullscreen_opacity = 1,
        blur = { size = 5, passes = 4, special = true },
        shadow = { color = ROUDIX_SHADOW },
    },
})

-- Plugin: hypr-dynamic-cursors (curseur qui s'incline avec le mouvement)
-- Clé réelle : plugin.dynamic_cursors (underscore, pas "dynamic-cursors").
-- Enveloppé en `if` pour ne jamais faire planter le config si le plugin
-- n'est pas chargé (cf. recommandation officielle du plugin).
if hl.plugin.dynamic_cursors then
    hl.config({
        plugin = {
            dynamic_cursors = {
                enabled = true,
                mode = "tilt",
                tilt = { limit = 5000 },
                shake = { enabled = true },
            },
        },
    })
end

-- Plugin: borders-plus-plus (liseré extérieur en plus du dégradé teal existant)
-- Clé réelle : plugin.borders_plus_plus (underscore), champ border_size_1
-- (pas "size_1").
if hl.plugin.borders_plus_plus then
    hl.config({
        plugin = {
            borders_plus_plus = {
                add_borders = 1,
                col = {
                    border_1 = ROUDIX_ACCENT2,
                },
                border_size_1 = 1,
            },
        },
    })
end

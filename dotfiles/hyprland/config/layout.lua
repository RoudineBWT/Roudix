-- Layout configuration
-- "scrolling" est un layout NATIF de Hyprland 0.55+ (plus un plugin tiers comme
-- l'ancien hyprscroller, retiré/déprécié). category name: scrolling.
-- Réf: https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/

hl.config({
    general = {
        layout = "dwindle" -- or "master", "scrolling"
    },
    dwindle = {
        force_split = 0,
        smart_split = false,
        default_split_ratio = 1.0,
        split_bias = 0
    },
    master = {
        mfact = 0.55,
        orientation = "left",
        new_status = "slave",
        allow_small_split = false
    },
    scrolling = {
        column_width = 0.5,
        direction = "right",
        focus_fit_method = 1
    }
})

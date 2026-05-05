-- ──────────────────────────────────────
-- ANIMATIONS
-- ──────────────────────────────────────

hl.config({
    animations = {
        enabled = true,

        -- Custom bezier curves
        bezier = {
            { name = "easeOutQuad",  points = { 0.25, 0.46, 0.45, 0.94 } },
            { name = "easeOutCubic", points = { 0.215, 0.61, 0.355, 1.0 } },
            { name = "spring",       points = { 0.68, -0.55, 0.265, 1.55 } },
        },

        animation = {
            -- Windows
            { name = "windowsIn",   enable = true, speed = 2, bezier = "easeOutQuad",  style = "slide" },
            { name = "windowsOut",  enable = true, speed = 2, bezier = "easeOutCubic", style = "slide" },
            { name = "windowsMove", enable = true, speed = 3, bezier = "spring" },

            -- Workspaces
            { name = "workspaces",  enable = true, speed = 3, bezier = "easeOutQuad",  style = "slide" },

            -- Fade
            { name = "fadeIn",      enable = true, speed = 2, bezier = "easeOutQuad" },
            { name = "fadeOut",     enable = true, speed = 2, bezier = "easeOutCubic" },
            { name = "fadeSwitch",  enable = true, speed = 2, bezier = "easeOutQuad" },
            { name = "fadeShadow",  enable = true, speed = 2, bezier = "easeOutQuad" },
            { name = "fadeDim",     enable = true, speed = 2, bezier = "easeOutQuad" },

            -- Borders
            { name = "border",      enable = true, speed = 5, bezier = "default" },
        },
    },
})

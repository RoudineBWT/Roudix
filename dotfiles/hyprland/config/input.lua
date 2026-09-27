-- Portés depuis dotfiles/niri-noc-v5/cfg/input.kdl

hl.config({
    input = {
        kb_layout  = "us",
        kb_variant = "intl", -- clavier US International (dead-keys), comme sur ton niri
        numlock_by_default = true,
        accel_profile = "flat",
        follow_mouse = 1, -- focus-follows-mouse, comme dans ton niri
    },
})

-- Gestes tactiles (identiques à input.kdl : tap-to-click + scroll naturel)
hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "down",       action = "close" })
hl.gesture({ fingers = 3, direction = "up",         action = "fullscreen" })
hl.gesture({ fingers = 3, direction = "left",       action = "float" })

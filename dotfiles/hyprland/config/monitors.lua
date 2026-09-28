-- Monitor config synced from niri display.kdl
-- Run `hyprctl monitors` to verify output names match

hl.monitor({
    output   = "DP-3",
    mode     = "1920x1080@165",
    position = "0x0",
    scale    = 1,
})

hl.monitor({
    output   = "DP-1",
    mode     = "2560x1440@240",
    position = "1920x0",
    scale    = 1
})

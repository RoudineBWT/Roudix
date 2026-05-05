-- ──────────────────────────────────────
-- MONITORS
-- ──────────────────────────────────────
-- Run `hyprctl monitors` to list connected displays

-- HKC 1080p@165 — left monitor
hl.monitor({
    output   = "desc:HKC OVERSEAS LIMITED 24E4 0000000000001",
    mode     = "1920x1080@165",
    position = "0x0",
    scale    = "1",
})

-- Legion 1440p@240 — right monitor, VRR on-demand
hl.monitor({
    output   = "desc:Lenovo Group Limited Legion 27Q-10 UNA07260",
    mode     = "2560x1440@240",
    position = "1920x0",
    scale    = "1",
    vrr      = 2,
})

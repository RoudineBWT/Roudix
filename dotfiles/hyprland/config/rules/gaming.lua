-- Gaming rules for Roudix Hyprland.

local gamingWorkspace = "name:\u{f0297}"
local gamingApps = "^(steam_app.*|gamescope)$"

hl.window_rule({ match = { content = "game" }, workspace = gamingWorkspace })
hl.window_rule({ match = { content = "game" }, confine_pointer = true, immediate = true, idle_inhibit = "fullscreen" })
hl.window_rule({ match = { class = gamingApps }, workspace = gamingWorkspace })
hl.window_rule({
    match = { class = gamingApps, title = "^(.+)$", initial_title = "negative:^.*\\/home\\/.*$" },
    size = "monitor_w monitor_h", fullscreen_state = 2, sync_fullscreen = true,
    decorate = false, content = "game",
})
hl.window_rule({ match = { class = "^(steam)$" }, workspace = gamingWorkspace })
hl.window_rule({ match = { class = "^(steam)$", title = "^(Friends List)$" }, float = true })
hl.window_rule({ match = { class = "^(steam)$", title = "^(Launching\\.{3})$" }, float = true, center = true, workspace = gamingWorkspace })
hl.window_rule({ match = { class = "^(steam_app.*)$", initial_title = "^$" }, float = true, center = true, fullscreen = false, fullscreen_state = 0, workspace = gamingWorkspace })
hl.window_rule({ match = { class = "^(Minecraft)$" }, size = "monitor_w monitor_h", fullscreen_state = 2, content = "game" })
hl.window_rule({ match = { class = "^(heroic)$" }, workspace = gamingWorkspace, size = "monitor_w monitor_h", fullscreen_state = 2, content = "game" })

-- No VRR for the shell itself; games are allowed to use the compositor's global VRR policy.

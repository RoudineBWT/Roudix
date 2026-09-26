-- Workspace rules wiki https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- Parity with niri/_output.nix (same Nerd Font glyphs, same role).
--
-- Targeting by numeric ID (stable), NOT by name:<glyph> (ID is unstable on the
-- Hyprland side: hyprwm/Hyprland#665 / #14520 — see config/ws.lua). The icon
-- becomes a cosmetic `default_name` on a `persistent` workspace_rule,
-- exactly following Noctalia's official recommendation:
-- https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/#persistent-workspaces
--
-- `persistent = true` keeps the workspace visible in the Noctalia bar even
-- when empty (otherwise, only workspaces containing a window appear).
-- Single source of truth: config/ws.lua (shared with binds/common.lua and
-- rules/apps.lua, rules/gaming.lua) — adding/removing a workspace there
-- is sufficient; this file updates automatically.
local ws = require("config.ws")

for i, w in ipairs(ws.__order) do
    hl.workspace_rule({
        workspace = tostring(i),
        monitor = w.monitor,
        persistent = true,
        default_name = w.glyph,
        default = (i == 1), -- premier workspace déclaré = défaut (web, DP-1)
    })
end

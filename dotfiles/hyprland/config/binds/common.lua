-- Common Roudix Hyprland keybinds. Shell-specific binds live in config/shell.lua.

-- 1. Applications
local mainMod = "SUPER"
local launchPrefix = "uwsm app -- "

hl.bind(mainMod .. " + Return", hl.dsp.exec_cmd(launchPrefix .. TERMINAL), { description = "Terminal" })
-- BROWSER / BROWSER_ALT sont résolus depuis roudix.* par config/nix-apps.lua
-- (généré par hyprland/default.nix) et peuvent être nil si aucun navigateur
-- n'est configuré côté NixOS — binds gardés conditionnels pour ne pas planter
-- au chargement dans ce cas.
if BROWSER then
    hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(launchPrefix .. BROWSER), { description = "Browser" })
end
if BROWSER_ALT then
    hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd(launchPrefix .. BROWSER_ALT), { description = "Alternate browser" })
end
-- Un bind par navigateur supplémentaire (au-delà de BROWSER/BROWSER_ALT),
-- même principe que le Mod+Ctrl+Alt+N de niri/umbriel/mangowc pour
-- roudix.browser.commands.
if EXTRA_BROWSERS then
    for i, b in ipairs(EXTRA_BROWSERS) do
        hl.bind(mainMod .. " + CONTROL + ALT + " .. i, hl.dsp.exec_cmd(launchPrefix .. b.command), { description = "Additional browser " .. i })
    end
end
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(launchPrefix .. FILE_MANAGER), { description = "File manager" })
hl.bind(mainMod .. " + T", hl.dsp.window.float({ action = "toggle" }), { description = "Toggle floating" })
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(launchPrefix .. CALCULATOR), { description = "Calculator" })
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd(launchPrefix .. MEDIA_PLAYER), { description = "Media player" })
hl.bind(mainMod .. " + Q", hl.dsp.window.close(), { description = "Close window" })

-- 2. Media

local function bindMedia(key, cmd, flags) hl.bind(key, hl.dsp.exec_cmd(cmd), flags) end
bindMedia("XF86AudioPlay", "playerctl play-pause", { locked = true, description = "Play / pause" })
bindMedia("XF86AudioPause", "playerctl play-pause", { locked = true, description = "Play / pause" })
bindMedia("XF86AudioNext", "playerctl next", { locked = true, description = "Next track" })
bindMedia("XF86AudioPrev", "playerctl previous", { locked = true, description = "Previous track" })

-- 3. Navigation

for _, pair in ipairs({{"Left","left"},{"H","left"},{"Right","right"},{"L","right"},{"Up","up"},{"K","up"},{"Down","down"},{"J","down"}}) do
    hl.bind(mainMod .. " + " .. pair[1], hl.dsp.focus({ direction = pair[2] }), { description = "Focus " .. pair[2] })
end
for _, pair in ipairs({{"Left","l"},{"H","l"},{"Right","r"},{"L","r"},{"Up","u"},{"K","u"},{"Down","d"},{"J","d"}}) do
    hl.bind(mainMod .. " + CONTROL + " .. pair[1], hl.dsp.window.move({ direction = pair[2] }), { description = "Move window " .. pair[2] })
end

hl.bind(mainMod .. " + SHIFT + Left", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor l"), { description = "Focus monitor left" })
hl.bind(mainMod .. " + SHIFT + Right", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor r"), { description = "Focus monitor right" })
hl.bind(mainMod .. " + SHIFT + Up", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor u"), { description = "Focus monitor up" })
hl.bind(mainMod .. " + SHIFT + Down", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor d"), { description = "Focus monitor down" })
for _, pair in ipairs({{"Left","l"},{"Right","r"},{"Up","u"},{"Down","d"}}) do
    hl.bind(mainMod .. " + SHIFT + CONTROL + " .. pair[1], hl.dsp.exec_cmd("hyprctl dispatch movewindow mon:" .. pair[2]), { description = "Move window to monitor " .. pair[2] })
end
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { description = "Drag window" })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { description = "Resize window" })

-- 4. Workspaces

-- Ciblage par id numérique (stable) plutôt que name:<glyphe> (id instable,
-- voir config/ws.lua) — Mod+1..8 suit l'ordre déclaré dans ws.lua.
local ws = require("config.ws")
for i in ipairs(ws.__order) do
    hl.bind(mainMod .. " + " .. i, hl.dsp.focus({ workspace = i }), { description = "Workspace " .. i })
    hl.bind(mainMod .. " + CONTROL + " .. i, hl.dsp.window.move({ workspace = i, follow = false }), { description = "Move window to workspace " .. i })
end
hl.bind(mainMod .. " + 9", hl.dsp.focus({ workspace = 9 }), { description = "Workspace 9" })
hl.bind(mainMod .. " + CONTROL + 9", hl.dsp.window.move({ workspace = 9, follow = false }), { description = "Move window to workspace 9" })
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }), { description = "Next workspace" })
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }), { description = "Previous workspace" })
hl.bind(mainMod .. " + CONTROL + mouse_down", hl.dsp.window.move({ workspace = "r+1" }), { description = "Move window to next workspace" })
hl.bind(mainMod .. " + CONTROL + mouse_up", hl.dsp.window.move({ workspace = "r-1" }), { description = "Move window to previous workspace" })
hl.bind(mainMod .. " + Tab", hl.dsp.exec_cmd("hyprctl dispatch workspace previous"), { description = "Previous workspace" })

-- 5. Window management

hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special" }), { description = "Move window to special workspace" })
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special(), { description = "Toggle special workspace" })
hl.bind(mainMod .. " + CONTROL + F", hl.dsp.window.fullscreen({ mode = 1 }), { description = "Fullscreen (mode 1)" })
hl.bind(mainMod .. " + CONTROL + C", hl.dsp.exec_cmd("hyprctl dispatch centerwindow"), { description = "Center window" })
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen(), { description = "Toggle fullscreen" })
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("hyprctl dispatch togglegroup"), { description = "Toggle window group" })
hl.bind(mainMod .. " + ALT + J", hl.dsp.layout("togglesplit"), { description = "Toggle split direction" })

local layoutCycle = { "dwindle", "master", "scrolling" }
local layoutIndex = 1
local function resizeWidth(direction)
    if layoutCycle[layoutIndex] == "scrolling" then hl.exec_cmd('hyprctl dispatch layoutmsg "colresize ' .. direction .. 'conf"')
    else hl.exec_cmd("hyprctl dispatch resizeactive " .. direction .. "10% 0") end
end
hl.bind(mainMod .. " + minus", function() resizeWidth("-") end, { description = "Decrease width" })
hl.bind(mainMod .. " + equal", function() resizeWidth("+") end, { description = "Increase width" })
hl.bind(mainMod .. " + SHIFT + minus", hl.dsp.exec_cmd("hyprctl dispatch resizeactive 0 -10%"), { description = "Decrease height" })
hl.bind(mainMod .. " + SHIFT + equal", hl.dsp.exec_cmd("hyprctl dispatch resizeactive 0 10%"), { description = "Increase height" })
local function cycleLayout()
    layoutIndex = (layoutIndex % #layoutCycle) + 1
    local nextLayout = layoutCycle[layoutIndex]
    hl.config({ general = { layout = nextLayout } })
    hl.exec_cmd("hyprctl notify -1 2500 'rgb(2980b9)' 'Layout: " .. nextLayout .. "'")
end
hl.bind(mainMod .. " + ALT + Space", cycleLayout, { description = "Cycle layout" })
for _, pair in ipairs({{"comma","move -col"},{"period","move +col"},{"SHIFT + comma","swapcol l"},{"SHIFT + period","swapcol r"},{"ALT + minus","colresize -conf"},{"ALT + equal","colresize +conf"}}) do hl.bind(mainMod .. " + " .. pair[1], hl.dsp.layout(pair[2]), { description = "Layout: " .. pair[2] }) end
hl.bind(mainMod .. " + P", hl.dsp.layout("promote"), { description = "Promote window" })
hl.bind(mainMod .. " + bracketleft", hl.dsp.layout("consume"), { description = "Consume window" })
hl.bind(mainMod .. " + bracketright", hl.dsp.layout("expel"), { description = "Expel window" })
hl.bind(mainMod .. " + Home", hl.dsp.layout("fit tobeg"), { description = "Fit layout to beginning" })
hl.bind(mainMod .. " + End", hl.dsp.layout("fit toend"), { description = "Fit layout to end" })
hl.bind(mainMod .. " + ALT + F", hl.dsp.layout("fit expand"), { description = "Fit layout to expand" })
hl.bind(mainMod .. " + I", hl.dsp.layout("inhibit_scroll"), { description = "Toggle scrolling inhibition" })

-- 6. Hyprland

hl.bind("CONTROL + ALT + Delete", hl.dsp.exec_cmd("hyprctl dispatch exit"), { description = "Exit Hyprland" })
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.exec_cmd("hyprctl dispatch dpms off"), { description = "Turn monitors off" })
hl.bind(mainMod .. " + Escape", hl.dsp.exec_cmd("hyprctl kill"), { description = "Kill active window" })

local gameModeOn = false

local function toggleGameMode()
    gameModeOn = not gameModeOn

    hl.config({
        animations = { enabled = not gameModeOn },
        decoration = {
            blur     = { enabled = not gameModeOn },
            shadow   = { enabled = not gameModeOn },
            rounding = gameModeOn and 0 or 10,
        },
        general = {
            gaps_in  = gameModeOn and 0 or 3,
            gaps_out = gameModeOn and 0 or 9,
        },
    })

    hl.exec_cmd("notify-send 'Roudix' '" .. (gameModeOn and "Mode jeu activé" or "Mode jeu désactivé") .. "'")
end

hl.bind(mainMod .. " + SHIFT + G", toggleGameMode)

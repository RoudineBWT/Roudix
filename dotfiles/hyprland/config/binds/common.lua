-- Common Roudix Hyprland keybinds. Shell-specific binds live in config/shell.lua.
local mainMod = "SUPER"
local launchPrefix = "uwsm app -- "

hl.bind(mainMod .. " + Return", hl.dsp.exec_cmd(launchPrefix .. TERMINAL))
-- BROWSER / BROWSER_ALT sont résolus depuis roudix.* par config/nix-apps.lua
-- (généré par hyprland/default.nix) et peuvent être nil si aucun navigateur
-- n'est configuré côté NixOS — binds gardés conditionnels pour ne pas planter
-- au chargement dans ce cas.
if BROWSER then
    hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(launchPrefix .. BROWSER))
end
if BROWSER_ALT then
    hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd(launchPrefix .. BROWSER_ALT))
end
-- Un bind par navigateur supplémentaire (au-delà de BROWSER/BROWSER_ALT),
-- même principe que le Mod+Ctrl+Alt+N de niri/umbriel/mangowc pour
-- roudix.browser.commands.
if EXTRA_BROWSERS then
    for i, b in ipairs(EXTRA_BROWSERS) do
        hl.bind(mainMod .. " + CONTROL + ALT + " .. i, hl.dsp.exec_cmd(launchPrefix .. b.command))
    end
end
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(launchPrefix .. FILE_MANAGER))
hl.bind(mainMod .. " + T", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(launchPrefix .. CALCULATOR))
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd(launchPrefix .. MEDIA_PLAYER))
hl.bind(mainMod .. " + Q", hl.dsp.window.close())

local function bindMedia(key, cmd, flags) hl.bind(key, hl.dsp.exec_cmd(cmd), flags) end
bindMedia("XF86AudioPlay", "playerctl play-pause", { locked = true })
bindMedia("XF86AudioPause", "playerctl play-pause", { locked = true })
bindMedia("XF86AudioNext", "playerctl next", { locked = true })
bindMedia("XF86AudioPrev", "playerctl previous", { locked = true })

for _, pair in ipairs({{"Left","left"},{"H","left"},{"Right","right"},{"L","right"},{"Up","up"},{"K","up"},{"Down","down"},{"J","down"}}) do
    hl.bind(mainMod .. " + " .. pair[1], hl.dsp.focus({ direction = pair[2] }))
end
for _, pair in ipairs({{"Left","l"},{"H","l"},{"Right","r"},{"L","r"},{"Up","u"},{"K","u"},{"Down","d"},{"J","d"}}) do
    hl.bind(mainMod .. " + CONTROL + " .. pair[1], hl.dsp.window.move({ direction = pair[2] }))
end

hl.bind(mainMod .. " + SHIFT + Left", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor l"))
hl.bind(mainMod .. " + SHIFT + Right", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor r"))
hl.bind(mainMod .. " + SHIFT + Up", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor u"))
hl.bind(mainMod .. " + SHIFT + Down", hl.dsp.exec_cmd("hyprctl dispatch focusmonitor d"))
for _, pair in ipairs({{"Left","l"},{"Right","r"},{"Up","u"},{"Down","d"}}) do
    hl.bind(mainMod .. " + SHIFT + CONTROL + " .. pair[1], hl.dsp.exec_cmd("hyprctl dispatch movewindow mon:" .. pair[2]))
end
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag())
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize())

-- Ciblage par id numérique (stable) plutôt que name:<glyphe> (id instable,
-- voir config/ws.lua) — Mod+1..8 suit l'ordre déclaré dans ws.lua.
local ws = require("config.ws")
for i in ipairs(ws.__order) do
    hl.bind(mainMod .. " + " .. i, hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + CONTROL + " .. i, hl.dsp.window.move({ workspace = i, follow = false }))
end
hl.bind(mainMod .. " + 9", hl.dsp.focus({ workspace = 9 }))
hl.bind(mainMod .. " + CONTROL + 9", hl.dsp.window.move({ workspace = 9, follow = false }))
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(mainMod .. " + CONTROL + mouse_down", hl.dsp.window.move({ workspace = "r+1" }))
hl.bind(mainMod .. " + CONTROL + mouse_up", hl.dsp.window.move({ workspace = "r-1" }))
hl.bind(mainMod .. " + Tab", hl.dsp.exec_cmd("hyprctl dispatch workspace previous"))

hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special" }))
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special())
hl.bind(mainMod .. " + CONTROL + F", hl.dsp.window.fullscreen({ mode = 1 }))
hl.bind(mainMod .. " + CONTROL + C", hl.dsp.exec_cmd("hyprctl dispatch centerwindow"))
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen())
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("hyprctl dispatch togglegroup"))
hl.bind(mainMod .. " + ALT + J", hl.dsp.layout("togglesplit"))

local layoutCycle = { "dwindle", "master", "scrolling" }
local layoutIndex = 1
local function resizeWidth(direction)
    if layoutCycle[layoutIndex] == "scrolling" then hl.exec_cmd('hyprctl dispatch layoutmsg "colresize ' .. direction .. 'conf"')
    else hl.exec_cmd("hyprctl dispatch resizeactive " .. direction .. "10% 0") end
end
hl.bind(mainMod .. " + minus", function() resizeWidth("-") end)
hl.bind(mainMod .. " + equal", function() resizeWidth("+") end)
hl.bind(mainMod .. " + SHIFT + minus", hl.dsp.exec_cmd("hyprctl dispatch resizeactive 0 -10%"))
hl.bind(mainMod .. " + SHIFT + equal", hl.dsp.exec_cmd("hyprctl dispatch resizeactive 0 10%"))
local function cycleLayout()
    layoutIndex = (layoutIndex % #layoutCycle) + 1
    local nextLayout = layoutCycle[layoutIndex]
    hl.config({ general = { layout = nextLayout } })
    hl.exec_cmd("hyprctl notify -1 2500 'rgb(2980b9)' 'Layout: " .. nextLayout .. "'")
end
hl.bind(mainMod .. " + ALT + Space", cycleLayout)
for _, pair in ipairs({{"comma","move -col"},{"period","move +col"},{"SHIFT + comma","swapcol l"},{"SHIFT + period","swapcol r"},{"ALT + minus","colresize -conf"},{"ALT + equal","colresize +conf"}}) do hl.bind(mainMod .. " + " .. pair[1], hl.dsp.layout(pair[2])) end
hl.bind(mainMod .. " + P", hl.dsp.layout("promote"))
hl.bind(mainMod .. " + bracketleft", hl.dsp.layout("consume"))
hl.bind(mainMod .. " + bracketright", hl.dsp.layout("expel"))
hl.bind(mainMod .. " + Home", hl.dsp.layout("fit tobeg"))
hl.bind(mainMod .. " + End", hl.dsp.layout("fit toend"))
hl.bind(mainMod .. " + ALT + F", hl.dsp.layout("fit expand"))
hl.bind(mainMod .. " + I", hl.dsp.layout("inhibit_scroll"))

hl.bind("CONTROL + ALT + Delete", hl.dsp.exec_cmd("hyprctl dispatch exit"))
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.exec_cmd("hyprctl dispatch dpms off"))
hl.bind(mainMod .. " + Escape", hl.dsp.exec_cmd("hyprctl kill"))

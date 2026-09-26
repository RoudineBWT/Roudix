-- DankMaterialShell integration for Roudix Hyprland.
local dms = "dms "

hl.bind(
    "SUPER + SHIFT + Escape",
    hl.dsp.exec_cmd(dms .. "ipc call keybinds toggle hyprland"),
    { description = "Keybind Cheatsheet" }
)
hl.bind("SUPER + D", hl.dsp.exec_cmd(dms .. "ipc call spotlight toggle"))
hl.bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd(dms .. "ipc call powermenu toggle"))
hl.bind("SUPER + ALT + L", hl.dsp.exec_cmd(dms .. "ipc call lock lock"))
hl.bind("ALT + TAB", hl.dsp.exec_cmd(dms .. "ipc call hypr toggleOverview"))

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(dms .. "ipc call audio increment 3"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(dms .. "ipc call audio decrement 3"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd(dms .. "ipc call audio mute"), { locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd(dms .. "ipc call audio micmute"), { locked = true })

hl.bind("Print", hl.dsp.exec_cmd("dms screenshot"), { locked = true })
hl.bind("SUPER + Print", hl.dsp.exec_cmd("dms screenshot full"))
hl.bind("CONTROL + SHIFT + 1", hl.dsp.exec_cmd("dms screenshot"))
hl.bind("CONTROL + SHIFT + 2", hl.dsp.exec_cmd("dms screenshot full"))
hl.bind("CONTROL + SHIFT + 3", hl.dsp.exec_cmd("dms screenshot window"))

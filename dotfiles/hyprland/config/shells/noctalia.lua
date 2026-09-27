-- Noctalia integration for Roudix Hyprland.

-- 7. Noctalia
local ipc = "noctalia msg "

hl.bind("SUPER + D", hl.dsp.exec_cmd(ipc .. "panel-toggle launcher"), { description = "Open launcher" })
hl.bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd(ipc .. "panel-toggle session"), { description = "Open session menu" })
hl.bind("SUPER + ALT + L", hl.dsp.exec_cmd(ipc .. "screen-lock"), { description = "Lock screen" })
hl.bind("ALT + TAB", hl.dsp.exec_cmd(ipc .. "window-switcher"), { description = "Window switcher" })
hl.bind("SUPER + Z", hl.dsp.exec_cmd(ipc .. "settings-toggle"), { description = "Toggle settings" })
hl.bind("SUPER + X", hl.dsp.exec_cmd(ipc .. "panel-toggle control-center"), { description = "Open control center" })
hl.bind("SUPER + A", hl.dsp.exec_cmd(ipc .. "panel-toggle control-center notifications"), { description = "Open notifications" })
hl.bind("SUPER + V", hl.dsp.exec_cmd(ipc .. "panel-toggle clipboard"), { description = "Open clipboard" })
hl.bind("SUPER + SHIFT + W", hl.dsp.exec_cmd(ipc .. "panel-toggle wallpaper"), { description = "Open wallpaper picker" })
hl.bind("SUPER + O", hl.dsp.exec_cmd(ipc .. "overview-toggle"), { description = "Toggle overview" })
hl.bind("SUPER + SHIFT + Escape", hl.dsp.exec_cmd(ipc .. "panel-toggle kenn/keybind-cheatsheet:cheatsheet"), { description = "Open keybind cheatsheet" })

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(ipc .. "volume-up"), { locked = true, repeating = true, description = "Volume up" })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(ipc .. "volume-down"), { locked = true, repeating = true, description = "Volume down" })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd(ipc .. "volume-mute"), { locked = true, description = "Mute output" })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd(ipc .. "mic-mute"), { locked = true, description = "Mute microphone" })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd(ipc .. "brightness-up"), { locked = true, repeating = true, description = "Brightness up" })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(ipc .. "brightness-down"), { locked = true, repeating = true, description = "Brightness down" })

hl.bind("Print", hl.dsp.exec_cmd(ipc .. "screenshot-region"), { description = "Screenshot region" })
hl.bind("SUPER + Print", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen"), { description = "Screenshot fullscreen" })
hl.bind("CONTROL + SHIFT + 1", hl.dsp.exec_cmd(ipc .. "screenshot-region"), { description = "Screenshot region" })
hl.bind("CONTROL + SHIFT + 2", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen"), { description = "Screenshot fullscreen" })
hl.bind("CONTROL + SHIFT + 3", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen pick"), { description = "Screenshot monitor" })

hl.layer_rule({ name = "noctalia", match = { namespace = "^noctalia-(bar-.+|notification|dock|panel|attached-panel|osd|window-switcher)$" }, no_anim = true, ignore_alpha = 0.5, blur = true, blur_popups = true })

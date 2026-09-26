-- Noctalia integration for Roudix Hyprland.
local ipc = "noctalia msg "

hl.bind(
    "SUPER + SHIFT + Escape",
    hl.dsp.exec_cmd(ipc .. "panel-toggle kenn/keybind-cheatsheet:cheatsheet"),
    { description = "Keybind Cheatsheet" }
)
hl.bind("SUPER + D", hl.dsp.exec_cmd(ipc .. "panel-toggle launcher"))
hl.bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd(ipc .. "panel-toggle session"))
hl.bind("SUPER + ALT + L", hl.dsp.exec_cmd(ipc .. "screen-lock"))
hl.bind("ALT + TAB", hl.dsp.exec_cmd(ipc .. "window-switcher"))
hl.bind("SUPER + Z", hl.dsp.exec_cmd(ipc .. "settings-toggle"))
hl.bind("SUPER + X", hl.dsp.exec_cmd(ipc .. "panel-toggle control-center"))
hl.bind("SUPER + A", hl.dsp.exec_cmd(ipc .. "panel-toggle control-center notifications"))
hl.bind("SUPER + V", hl.dsp.exec_cmd(ipc .. "panel-toggle clipboard"))
hl.bind("SUPER + SHIFT + W", hl.dsp.exec_cmd(ipc .. "panel-toggle wallpaper"))
hl.bind("SUPER + O", hl.dsp.exec_cmd(ipc .. "overview-toggle"))

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(ipc .. "volume-up"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(ipc .. "volume-down"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd(ipc .. "volume-mute"), { locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd(ipc .. "mic-mute"), { locked = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd(ipc .. "brightness-up"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(ipc .. "brightness-down"), { locked = true, repeating = true })

hl.bind("Print", hl.dsp.exec_cmd(ipc .. "screenshot-region"))
hl.bind("SUPER + Print", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen"))
hl.bind("CONTROL + SHIFT + 1", hl.dsp.exec_cmd(ipc .. "screenshot-region"))
hl.bind("CONTROL + SHIFT + 2", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen"))
hl.bind("CONTROL + SHIFT + 3", hl.dsp.exec_cmd(ipc .. "screenshot-fullscreen pick"))

hl.layer_rule({ name = "noctalia", match = { namespace = "^noctalia-(bar-.+|notification|dock|panel|attached-panel|osd|window-switcher)$" }, no_anim = true, ignore_alpha = 0.5, blur = true, blur_popups = true })

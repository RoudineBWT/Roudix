-- Caelestia integration for Roudix Hyprland.
local global = hl.dsp.global

hl.bind("SUPER + D", global("caelestia:launcher"))
hl.bind("SUPER + SHIFT + Q", global("caelestia:session"))
hl.bind("SUPER + ALT + L", global("caelestia:lock"))
hl.bind("ALT + TAB", global("caelestia:sidebar"))

hl.bind("XF86AudioRaiseVolume", global("caelestia:volumeUp"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", global("caelestia:volumeDown"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", global("caelestia:mute"), { locked = true })
hl.bind("XF86MonBrightnessUp", global("caelestia:brightnessUp"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", global("caelestia:brightnessDown"), { locked = true, repeating = true })

hl.bind("Print", hl.dsp.exec_cmd("caelestia screenshot"), { locked = true })
hl.bind("SUPER + Print", global("caelestia:screenshotFreeze"))
hl.bind("CONTROL + SHIFT + 1", global("caelestia:screenshot"))
hl.bind("CONTROL + SHIFT + 2", hl.dsp.exec_cmd("caelestia screenshot"))
hl.bind("CONTROL + SHIFT + 3", global("caelestia:screenshot"))

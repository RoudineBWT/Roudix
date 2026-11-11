-- Caelestia integration for Roudix Hyprland.
local global = hl.dsp.global

hl.bind("SUPER + D", global("caelestia:launcher"))
hl.bind("SUPER + SHIFT + Q", global("caelestia:session"))
hl.bind("SUPER + ALT + L", global("caelestia:lock"))
hl.bind("ALT + TAB", global("caelestia:sidebar"))

-- Caelestia declares no volume/mute global shortcuts (caelestia:volumeUp,
-- volumeDown and mute do not exist), only brightnessUp/brightnessDown. Audio keys
-- go through wpctl, like the upstream caelestia-dots keybinds.
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { locked = true })
hl.bind("XF86MonBrightnessUp", global("caelestia:brightnessUp"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", global("caelestia:brightnessDown"), { locked = true, repeating = true })

hl.bind("Print", hl.dsp.exec_cmd("caelestia screenshot"), { locked = true })
hl.bind("SUPER + Print", global("caelestia:screenshotFreeze"))
hl.bind("CONTROL + SHIFT + 1", global("caelestia:screenshot"))
hl.bind("CONTROL + SHIFT + 2", hl.dsp.exec_cmd("caelestia screenshot"))
hl.bind("CONTROL + SHIFT + 3", global("caelestia:screenshot"))

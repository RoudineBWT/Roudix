-- ──────────────────────────────────────
-- KEYBINDINGS
-- ──────────────────────────────────────

local mod = "SUPER"

-- ─── Noctalia Shell ───
hl.bind(mod .. " SHIFT + ESCAPE", hl.dsp.exec("noctalia-shell ipc call hotkeyOverlay toggle"))
hl.bind(mod .. " SHIFT + Q",      hl.dsp.exec("noctalia-shell ipc call sessionMenu toggle"))

-- ─── Applications ───
hl.bind(mod .. " + RETURN",       hl.dsp.exec("ghostty"))
hl.bind(mod .. " + D",            hl.dsp.exec("noctalia-shell ipc call launcher toggle"))
hl.bind(mod .. " + B",            hl.dsp.exec("zen-beta"))
hl.bind(mod .. " SHIFT + B",      hl.dsp.exec("brave"))
hl.bind(mod .. " ALT + L",        hl.dsp.exec("noctalia-shell ipc call lockScreen lock"))
hl.bind(mod .. " + E",            hl.dsp.exec("nautilus"))

-- ─── Window management ───
hl.bind(mod .. " + Q",            hl.dsp.killactive())
hl.bind(mod .. " + F",            hl.dsp.fullscreen(0))
hl.bind(mod .. " + T",            hl.dsp.togglefloating())
hl.bind(mod .. " + C",            hl.dsp.centerwindow())

-- ─── Focus (HJKL + arrows) ───
hl.bind(mod .. " + H",            hl.dsp.movefocus("l"))
hl.bind(mod .. " + LEFT",         hl.dsp.movefocus("l"))
hl.bind(mod .. " + L",            hl.dsp.movefocus("r"))
hl.bind(mod .. " + RIGHT",        hl.dsp.movefocus("r"))
hl.bind(mod .. " + K",            hl.dsp.movefocus("u"))
hl.bind(mod .. " + UP",           hl.dsp.movefocus("u"))
hl.bind(mod .. " + J",            hl.dsp.movefocus("d"))
hl.bind(mod .. " + DOWN",         hl.dsp.movefocus("d"))

-- ─── Move window ───
hl.bind(mod .. " CTRL + H",       hl.dsp.movewindow("l"))
hl.bind(mod .. " CTRL + LEFT",    hl.dsp.movewindow("l"))
hl.bind(mod .. " CTRL + L",       hl.dsp.movewindow("r"))
hl.bind(mod .. " CTRL + RIGHT",   hl.dsp.movewindow("r"))
hl.bind(mod .. " CTRL + K",       hl.dsp.movewindow("u"))
hl.bind(mod .. " CTRL + UP",      hl.dsp.movewindow("u"))
hl.bind(mod .. " CTRL + J",       hl.dsp.movewindow("d"))
hl.bind(mod .. " CTRL + DOWN",    hl.dsp.movewindow("d"))

-- ─── Focus monitor ───
hl.bind(mod .. " SHIFT + LEFT",   hl.dsp.focusmonitor("l"))
hl.bind(mod .. " SHIFT + RIGHT",  hl.dsp.focusmonitor("r"))
hl.bind(mod .. " SHIFT + UP",     hl.dsp.focusmonitor("u"))
hl.bind(mod .. " SHIFT + DOWN",   hl.dsp.focusmonitor("d"))

-- ─── Move window to monitor ───
hl.bind(mod .. " SHIFT CTRL + LEFT",  hl.dsp.movewindow("mon:l"))
hl.bind(mod .. " SHIFT CTRL + RIGHT", hl.dsp.movewindow("mon:r"))
hl.bind(mod .. " SHIFT CTRL + UP",    hl.dsp.movewindow("mon:u"))
hl.bind(mod .. " SHIFT CTRL + DOWN",  hl.dsp.movewindow("mon:d"))

-- ─── Resize window ───
hl.bind(mod .. " + MINUS",        hl.dsp.resizeactive(-100, 0))
hl.bind(mod .. " + EQUAL",        hl.dsp.resizeactive(100,  0))
hl.bind(mod .. " SHIFT + MINUS",  hl.dsp.resizeactive(0, -100))
hl.bind(mod .. " SHIFT + EQUAL",  hl.dsp.resizeactive(0,  100))

-- ─── Move/resize floating windows with mouse ───
hl.bindm(mod .. " + mouse:272",   hl.dsp.movewindow())
hl.bindm(mod .. " + mouse:273",   hl.dsp.resizewindow())

-- ─── Workspaces ───
for i = 1, 9 do
    hl.bind(mod .. " + " .. i,       hl.dsp.workspace(i))
    hl.bind(mod .. " CTRL + " .. i,  hl.dsp.movetoworkspace(i))
end

-- ─── Previous workspace ───
hl.bind(mod .. " + TAB",          hl.dsp.workspace("previous"))

-- ─── Scroll through workspaces ───
hl.bind(mod .. " + mouse_down",   hl.dsp.workspace("e+1"))
hl.bind(mod .. " + mouse_up",     hl.dsp.workspace("e-1"))

-- ─── Screenshots (requires grimblast) ───
hl.bind("CTRL SHIFT + 1",         hl.dsp.exec("grimblast copy area"))
hl.bind("CTRL SHIFT + 2",         hl.dsp.exec("grimblast copy screen"))
hl.bind("CTRL SHIFT + 3",         hl.dsp.exec("grimblast copy active"))

-- ─── Audio controls (repeat while held) ───
hl.bindel(" + XF86AudioRaiseVolume", hl.dsp.exec("noctalia-shell ipc call volume increase"))
hl.bindel(" + XF86AudioLowerVolume", hl.dsp.exec("noctalia-shell ipc call volume decrease"))
hl.bindl(" + XF86AudioMute",         hl.dsp.exec("noctalia-shell ipc call volume muteOutput"))
hl.bindl(" + XF86AudioMicMute",      hl.dsp.exec("noctalia-shell ipc call volume muteInput"))

-- ─── Media controls ───
hl.bindl(" + XF86AudioPlay",         hl.dsp.exec("playerctl play-pause"))
hl.bindl(" + XF86AudioPrev",         hl.dsp.exec("playerctl previous"))
hl.bindl(" + XF86AudioNext",         hl.dsp.exec("playerctl next"))

-- ─── Power ───
hl.bind(mod .. " SHIFT + P",     hl.dsp.dpms("off"))
hl.bind("CTRL ALT + Delete",     hl.dsp.exit())

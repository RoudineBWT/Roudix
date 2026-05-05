-- ──────────────────────────────────────
-- WINDOW RULES
-- ──────────────────────────────────────

-- ─── Discord → ws 4 (Chat), fixed size, floating ───
hl.window_rule({ rule = "workspace 4",     match = { class = "^discord$" } })
hl.window_rule({ rule = "float",           match = { class = "^discord$" } })
hl.window_rule({ rule = "size 1316 1011",  match = { class = "^discord$" } })

-- ─── Element → ws 4, fixed size, floating ───
hl.window_rule({ rule = "workspace 4",     match = { class = "^Element$" } })
hl.window_rule({ rule = "float",           match = { class = "^Element$" } })
hl.window_rule({ rule = "size 1316 1011",  match = { class = "^Element$" } })

-- ─── Telegram → ws 4, fixed size, top-right corner ───
hl.window_rule({ rule = "workspace 4",                             match = { class = "^org.telegram.desktop$" } })
hl.window_rule({ rule = "float",                                   match = { class = "^org.telegram.desktop$" } })
hl.window_rule({ rule = "size 555 1011",                           match = { class = "^org.telegram.desktop$" } })
hl.window_rule({ rule = "move ((monitor_w*1)-555) (0)",            match = { class = "^org.telegram.desktop$" } })

-- ─── Ghostty → ws 3 (Terminal), floating, fixed size, centered ───
hl.window_rule({ rule = "workspace 3",     match = { class = "^com.mitchellh.ghostty$" } })
hl.window_rule({ rule = "float",           match = { class = "^com.mitchellh.ghostty$" } })
hl.window_rule({ rule = "size 1505 755",   match = { class = "^com.mitchellh.ghostty$" } })
hl.window_rule({ rule = "center",          match = { class = "^com.mitchellh.ghostty$" } })

-- ─── Kitty → ws 3, floating ───
hl.window_rule({ rule = "workspace 3",     match = { class = "^kitty$" } })
hl.window_rule({ rule = "float",           match = { class = "^kitty$" } })

-- ─── Ptyxis → ws 3 ───
hl.window_rule({ rule = "workspace 3",     match = { class = "^org.gnome.Ptyxis$" } })

-- ─── Zen Browser → ws 1 (Browser), maximized ───
hl.window_rule({ rule = "workspace 1",     match = { class = "^zen$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^zen$" } })

-- ─── Zen PiP → floating, pinned on top ───
hl.window_rule({ rule = "float",           match = { class = "^zen$", title = "^Picture-in-Picture$" } })
hl.window_rule({ rule = "pin",             match = { class = "^zen$", title = "^Picture-in-Picture$" } })

-- ─── Zen About dialog → floating ───
hl.window_rule({ rule = "float",           match = { class = "^zen$", title = "^About Zen$" } })

-- ─── Firefox → ws 1, maximized ───
hl.window_rule({ rule = "workspace 1",     match = { class = "^firefox$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^firefox$" } })

-- ─── Firefox PiP → floating, pinned on top ───
hl.window_rule({ rule = "float",           match = { class = "^firefox$", title = "^Picture-in-Picture$" } })
hl.window_rule({ rule = "pin",             match = { class = "^firefox$", title = "^Picture-in-Picture$" } })

-- ─── Firefox About dialog → floating ───
hl.window_rule({ rule = "float",           match = { class = "^firefox$", title = "^About Mozilla Firefox$" } })

-- ─── Brave → ws 2 (Code), maximized ───
hl.window_rule({ rule = "workspace 2",     match = { class = "^brave-browser$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^brave-browser$" } })

-- ─── Zed → ws 2, maximized ───
hl.window_rule({ rule = "workspace 2",     match = { class = "^dev.zed.Zed$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^dev.zed.Zed$" } })

-- ─── Steam → ws 5 (Gaming), maximized ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^steam$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^steam$" } })

-- ─── Steam notification toasts → floating, bottom-right corner ───
hl.window_rule({ rule = "float",                                             match = { class = "^steam$", title = "^notificationtoasts_.*$" } })
hl.window_rule({ rule = "move ((monitor_w*1)-320) ((monitor_h*1)-120)",      match = { class = "^steam$", title = "^notificationtoasts_.*$" } })

-- ─── Steam Friends List → ws 5, floating ───
hl.window_rule({ rule = "workspace 5",     match = { title = "^Friends List$" } })
hl.window_rule({ rule = "float",           match = { title = "^Friends List$" } })

-- ─── Steam games → ws 5, fullscreen ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^steam_app_.*$" } })
hl.window_rule({ rule = "fullscreen",      match = { class = "^steam_app_.*$" } })

-- ─── Heroic → ws 5, fullscreen ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^heroic$" } })
hl.window_rule({ rule = "fullscreen",      match = { class = "^heroic$" } })

-- ─── Prism Launcher → ws 5, maximized ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^org.prismlauncher.PrismLauncher$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^org.prismlauncher.PrismLauncher$" } })

-- ─── Minecraft → ws 5, fullscreen ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^Minecraft.*$" } })
hl.window_rule({ rule = "fullscreen",      match = { class = "^Minecraft.*$" } })

-- ─── OpenRGB → ws 5 ───
hl.window_rule({ rule = "workspace 5",     match = { class = "^openrgb$" } })

-- ─── Nautilus → ws 6 (Files), maximized ───
hl.window_rule({ rule = "workspace 6",     match = { class = "^org.gnome.Nautilus$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^org.gnome.Nautilus$" } })

-- ─── Nautilus file dialogs → floating ───
hl.window_rule({ rule = "float",           match = { class = "^org.gnome.Nautilus$", title = "^Save As$" } })
hl.window_rule({ rule = "float",           match = { class = "^org.gnome.Nautilus$", title = "^Open$" } })

-- ─── Text Editor → ws 6 ───
hl.window_rule({ rule = "workspace 6",     match = { class = "^org.gnome.TextEditor$" } })

-- ─── Spotify → ws 7 (Music), maximized ───
hl.window_rule({ rule = "workspace 7",     match = { class = "^spotify$" } })
hl.window_rule({ rule = "maximize",        match = { class = "^spotify$" } })

-- ─── EasyEffects → ws 7 ───
hl.window_rule({ rule = "workspace 7",     match = { class = "^com.github.wwmm.easyeffects$" } })

-- ──────────────────────────────────────
-- ENVIRONMENT VARIABLES
-- ──────────────────────────────────────

hl.env("MOZ_ENABLE_WAYLAND",              "1")
hl.env("XDG_SESSION_TYPE",                "wayland")
hl.env("XDG_CURRENT_DESKTOP",             "Hyprland")
hl.env("XDG_SESSION_DESKTOP",             "Hyprland")
hl.env("MOZ_DBUS_REMOTE",                 "1")
hl.env("GDK_BACKEND",                     "wayland")
hl.env("QT_AUTO_SCREEN_SCALE_FACTOR",     "1")
hl.env("EGL_PLATFORM",                    "wayland")
hl.env("CLUTTER_BACKEND",                 "wayland")
hl.env("TERM",                            "ghostty")
hl.env("TERMINAL",                        "ghostty")
hl.env("_JAVA_AWT_WM_NONREPARENTING",     "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT",    "auto")
hl.env("QT_QPA_PLATFORMTHEME",            "qt6ct")
hl.env("XCURSOR_THEME",                   "capitaine-cursors-white")
hl.env("XCURSOR_SIZE",                    "32")

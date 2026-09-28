-- Portées depuis dotfiles/niri-noc-v5/cfg/misc.kdl
-- Si tu utilises UWSM, préfère les mettre dans ~/.config/uwsm/env plutôt qu'ici

hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("MOZ_DBUS_REMOTE", "1")
hl.env("GDK_BACKEND", "wayland")
hl.env("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
hl.env("QT_WAYLAND_FORCE_DPI", "physical")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("_JAVA_AWT_WM_NONREPARENTING", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
hl.env("WLR_NO_HARDWARE_CURSORS", "1")
hl.env("TZDIR", "/etc/zoneinfo")
hl.env("AMD_DEBUG", "nodcc")

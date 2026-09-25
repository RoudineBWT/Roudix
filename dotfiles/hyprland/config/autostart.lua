-- Roudix autostart.
-- The selected shell is started by Hyprland itself, exactly once.
-- Shell startup is intentionally compositor-owned, not systemd-owned.
local shell = os.getenv("ROUDIX_HYPR_SHELL") or "noctalia"

hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd --all")

    if shell == "noctalia" then
        hl.exec_cmd("noctalia")
    elseif shell == "dms" then
        hl.exec_cmd("dms run")
    elseif shell == "caelestia" then
        hl.exec_cmd("caelestia-shell")
    end

    if os.getenv("ROUDIX_HYPR_START_DISCORD") == "1" then
        hl.exec_cmd("discord")
    end
end)

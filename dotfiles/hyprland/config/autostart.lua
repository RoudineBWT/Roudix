-- Roudix autostart.
-- The shell itself is managed by its Nix/Home Manager systemd integration.
-- Keep only session environment initialization and optional application startup here.
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd --all")
    if os.getenv("ROUDIX_HYPR_START_DISCORD") == "1" then
        hl.exec_cmd("discord")
    end
end)

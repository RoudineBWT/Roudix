-- Select the Roudix Hyprland shell at runtime.
-- Roudix sets ROUDIX_HYPR_SHELL from roudix.desktop.shell in NixOS.
local shell = os.getenv("ROUDIX_HYPR_SHELL") or "noctalia"
if shell == "dms" then
    require("config.shells.dms")
elseif shell == "caelestia" then
    require("config.shells.caelestia")
else
    require("config.shells.noctalia")
end

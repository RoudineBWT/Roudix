-- Roudix Hyprland 0.55+ (Lua configuration)
-- Nix generates config/nix-plugins.lua so packaged plugins are loaded first.
require("config.nix-plugins")
-- Modularized for Roudix: common settings + common/apps/gaming rules + shell-specific binds.
require("config.colors")
require("config.defaults")
-- Généré par hyprland/default.nix depuis roudix.terminal / roudix.fileManager /
-- roudix.browser.* — TERMINAL/FILE_MANAGER/BROWSER/BROWSER_ALT/EXTRA_BROWSERS
-- réassignés ici gagnent sur config.defaults (pas de merge attrsOf à forcer
-- en Lua, contrairement à umbriel/niri/mangowc : la dernière affectation
-- l'emporte simplement). pcall : no-op silencieux si le fichier n'existe pas
-- encore (première évaluation avant que home-manager ne l'ait écrit).
pcall(require, "config.nix-apps")
require("config.animations")
require("config.autostart")
require("config.decorations")
require("config.environment")
require("config.input")
require("config.layout")
require("config.misc")
require("config.monitors")
require("config.workspaces")
require("config.binds.common")
require("config.rules.common")
require("config.rules.apps")
require("config.rules.gaming")
require("config.shell")
-- Couleurs Noctalia (matugen) live — voir _include-noctalia.nix. pcall :
-- no-op si le shell actif n'est pas Noctalia (fichier jamais généré) ou si
-- Noctalia n'a pas encore tourné une première fois.
pcall(require, "config.nix-noctalia")

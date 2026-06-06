-- ──────────────────────────────────────
-- ENTRY POINT
-- ──────────────────────────────────────
-- Ajoute le dossier cfg/ au path Lua pour que require() trouve les modules.
-- Adapte le chemin si ton dossier cfg/ n'est pas au même endroit.

local cfg = os.getenv("HOME") .. "/.config/hypr/cfg"
package.path = package.path .. ";" .. cfg .. "/?.lua"

require("environment")
require("monitors")
require("autostart")
require("input")
require("appearance")
require("animations")
require("workspaces")
require("rules")
require("keybinds")
require("misc")

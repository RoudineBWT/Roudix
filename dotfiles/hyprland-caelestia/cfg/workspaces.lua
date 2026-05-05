-- ──────────────────────────────────────
-- WORKSPACES
-- ──────────────────────────────────────
-- Workspace mapping:
--   󰈹  Browser   → ws 1  (Legion 1440p)
--      Code      → ws 2  (Legion 1440p)
--      Terminal  → ws 3  (HKC 1080p)
--      Chat      → ws 4  (Legion 1440p)
--   󰊗  Gaming    → ws 5  (Legion 1440p)
--   󰉋  Files     → ws 6  (Legion 1440p)
--   󰝚  Music     → ws 7  (HKC 1080p)
--      Misc      → ws 8  (HKC 1080p)

local legion = "desc:Lenovo Group Limited Legion 27Q-10 UNA07260"
local hkc    = "desc:HKC OVERSEAS LIMITED 24E4 0000000000001"

hl.workspace_rule({ workspace = "1", monitor = legion, default = true })
hl.workspace_rule({ workspace = "2", monitor = legion })
hl.workspace_rule({ workspace = "3", monitor = hkc })
hl.workspace_rule({ workspace = "4", monitor = legion })
hl.workspace_rule({ workspace = "5", monitor = legion })
hl.workspace_rule({ workspace = "6", monitor = legion })
hl.workspace_rule({ workspace = "7", monitor = hkc })
hl.workspace_rule({ workspace = "8", monitor = hkc })

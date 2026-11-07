-- Courbes/animations, ressenti proche des springs de dotfiles/niri-noc-v5/cfg/animation.kdl

hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}    } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}     } })
-- Hyprland >= 0.56 : springs recalibrés (plus lents à valeurs égales), et 0.57 renomme
-- dampening -> damping. Valeurs = nouveaux défauts de l'exemple officiel.
-- Un spring ignore `speed` : pour accélérer, augmenter stiffness.
hl.curve("easy",           { type = "spring", mass = 1, stiffness = 238.1191, damping = 24.21279333 })

hl.animation({ leaf = "global",     enabled = true, speed = 3, bezier = "quick" })
hl.animation({ leaf = "windows",    enabled = true, speed = 3, spring = "easy", style = "slide" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 5, bezier = "quick", style = "slide" })

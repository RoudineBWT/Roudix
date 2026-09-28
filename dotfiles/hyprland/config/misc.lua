hl.config({
    dwindle = {
        preserve_split = true,
    },
    general = {
        gaps_in = 3,
        gaps_out = 9, -- correspond au `gaps 9` de layout.kdl
    },
    misc = {
        col = { splash = ROUDIX_ACCENT },
        middle_click_paste = false,
        enable_swallow = true,
        swallow_regex = "(ghostty|kitty|com\\.mitchellh\\.ghostty)",
        -- niri gère la VRR par sortie ("on-demand" sur ton Legion 27Q-10).
        -- Hyprland ne l'a qu'en global : vrr = 2 = "activé seulement en plein écran",
        -- le plus proche du comportement on-demand. Vu que le VRR est un suspect secondaire
        -- dans tes crashs Star Wars Outlaws, teste aussi vrr = 0 (désactivé) pour comparer.
        vrr = 2,
    },
    -- direct_scanout=2 (repris de CachyOS) : laisse le compositeur bypasser le compositing
    -- pour les surfaces plein écran quand possible -> moins de latence en jeu/vidéo.
    render = {
        direct_scanout = 2,
    },
    xwayland = {
        force_zero_scaling = true,
    },
    ecosystem = {
        no_update_news = true,
        no_donation_nag = true,
    },
})

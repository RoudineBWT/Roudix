## _binds.nix — Umbriel: [keybinds].
##
## Doc : https://docs.noctalia.dev/umbriel/keybinds/
##       https://docs.noctalia.dev/umbriel/actions/
##       https://docs.noctalia.dev/umbriel/scratchpads/
{ ... }:
{
  programs.umbriel.settings = {
  keybinds = {
    # ─── Applications ───
    "Mod+Q" = "window-close";
    "Mod+Return" = "spawn:ghostty";
    "Mod+D" = "spawn:noctalia msg panel-toggle launcher";
    "Mod+Shift+B" = "spawn:zen-twilight";
    "Mod+B" = "spawn:brave-origin-beta";
    "Mod+Alt+L" = "spawn:noctalia msg screen-lock";
    "Mod+E" = "spawn:nautilus";
    "Mod+Shift+Q" = "spawn:noctalia msg panel-toggle session";
    "Mod+Shift+Escape" = "cheatsheet-toggle";

    # ─── Panneaux Noctalia additionnels ───
    # Repris tel quel de l'exemple officiel "Noctalia shell integration"
    # de la doc keybinds — absents de ta config d'origine (tu n'avais que
    # le launcher, pas les autres panneaux Noctalia).
    "Mod+V" = "spawn:noctalia msg panel-toggle clipboard";  # gestionnaire de presse-papier
    "Mod+W" = "spawn:noctalia msg panel-toggle wallpaper";  # sélecteur de wallpaper
    "Mod+Z" = "spawn:noctalia msg panel-toggle launcher /emo"; # sélecteur d'emoji
    "Mod+N" = "spawn:noctalia msg panel-toggle noctalia/notes:panel"; # panneau notes

    # ─── Audio ───
    # Fix : `allow_when_locked` (n'existait pas dans ta première traduction
    # niri→umbriel) permet à ces raccourcis de fonctionner même écran
    # verrouillé, comme sous niri avec allow-when-locked=true.
    "XF86AudioRaiseVolume" = { action = "spawn:noctalia msg volume-up"; allow_when_locked = true; };
    "XF86AudioLowerVolume" = { action = "spawn:noctalia msg volume-down"; allow_when_locked = true; };
    "XF86AudioMute" = { action = "spawn:noctalia msg volume-mute"; allow_when_locked = true; };
    "XF86AudioMicMute" = { action = "spawn:noctalia msg mic-mute"; allow_when_locked = true; };
    "XF86AudioPlay" = { action = "spawn:playerctl play-pause"; allow_when_locked = true; };
    "XF86AudioPrev" = { action = "spawn:playerctl previous"; allow_when_locked = true; };
    "XF86AudioNext" = { action = "spawn:playerctl next"; allow_when_locked = true; };

    # ─── Fenêtres : focus / déplacement ───
    "Mod+Left" = "window-focus-left";
    "Mod+H" = "window-focus-left";
    "Mod+Right" = "window-focus-right";
    "Mod+L" = "window-focus-right";
    "Mod+Up" = "window-focus-up";
    "Mod+K" = "window-focus-up";
    "Mod+Down" = "window-focus-down";
    "Mod+J" = "window-focus-down";

    "Mod+Ctrl+Left" = "column-move-left";
    "Mod+Ctrl+H" = "column-move-left";
    "Mod+Ctrl+Right" = "column-move-right";
    "Mod+Ctrl+L" = "column-move-right";
    "Mod+Ctrl+Up" = "window-move-up";
    "Mod+Ctrl+K" = "window-move-up";
    "Mod+Ctrl+Down" = "window-move-down";
    "Mod+Ctrl+J" = "window-move-down";

    # Fix : ces actions n'existaient pas (ou n'avaient pas été trouvées) au
    # moment de ta traduction — elles couvrent maintenant l'équivalent niri
    # de focus-column-first/last et move-column-to-first/last.
    "Mod+Home" = "column-focus-first";
    "Mod+End" = "column-focus-last";
    "Mod+Ctrl+Home" = "column-move-to-first";
    "Mod+Ctrl+End" = "column-move-to-last";

    "Mod+Shift+Left" = "output-focus-left";
    "Mod+Shift+Right" = "output-focus-right";
    "Mod+Shift+Up" = "output-focus-up";
    "Mod+Shift+Down" = "output-focus-down";

    "Mod+Shift+Ctrl+Left" = "column-move-to-output-left";
    "Mod+Shift+Ctrl+Right" = "column-move-to-output-right";
    "Mod+Shift+Ctrl+Up" = "column-move-to-output-up";
    "Mod+Shift+Ctrl+Down" = "column-move-to-output-down";

    # ─── Molette : navigation ───
    "Mod+WheelDown" = { action = "workspace-next"; repeat = false; };
    "Mod+WheelUp" = { action = "workspace-previous"; repeat = false; };

    "Mod+WheelRight" = "window-focus-right";
    "Mod+WheelLeft" = "window-focus-left";
    "Mod+Ctrl+WheelRight" = "column-move-right";
    "Mod+Ctrl+WheelLeft" = "column-move-left";

    "Mod+Shift+WheelDown" = "window-focus-right";
    "Mod+Shift+WheelUp" = "window-focus-left";
    "Mod+Ctrl+Shift+WheelDown" = "column-move-right";
    "Mod+Ctrl+Shift+WheelUp" = "column-move-left";

    # ─── Workspaces (Mod+1..5) ───
    # Comportement RELATIF au moniteur qui a le focus (comme sous niri), et
    # non plus un saut absolu vers un nom précis : voir doc Workspaces
    # #workspace-selectors — "when no exact numeric name exists, the number
    # selects that 1-based position on the preferred output" (le moniteur
    # focus, qui suit ta souris vu focus.follows_mouse=true). Comme aucun
    # workspace ne s'appelle littéralement "1", "2"... (ce sont des icônes),
    # Mod+1 résout donc TOUJOURS vers "position 1 du moniteur focus" :
    # Legion (DP-1) → web, HKC (DP-3) → chat. Mod+6/7/8 disparaissent : HKC
    # n'a que 3 positions, donc au-delà de Mod+3 ça n'a de sens que sur
    # Legion (positions 4 et 5).
    "Mod+1" = "workspace-switch:1"; # Legion: web · HKC: chat
    "Mod+2" = "workspace-switch:2"; # Legion: zed · HKC: musique
    "Mod+3" = "workspace-switch:3"; # Legion: term · HKC: web (brave)
    "Mod+4" = "workspace-switch:4"; # Legion: jeux
    "Mod+5" = "workspace-switch:5"; # Legion: fichiers

    "Mod+Ctrl+1" = "window-move-to-workspace:1";
    "Mod+Ctrl+2" = "window-move-to-workspace:2";
    "Mod+Ctrl+3" = "window-move-to-workspace:3";
    "Mod+Ctrl+4" = "window-move-to-workspace:4";
    "Mod+Ctrl+5" = "window-move-to-workspace:5";

    # ⚠ workspace-previous reste positionnel (pas de wrap, pas de "dernier
    # actif" comme le MRU de niri) — toujours une approximation.
    "Mod+Tab" = "workspace-previous";
    "Alt+Tab" = "spawn:noctalia msg window-switcher";

    # ─── Layout ───
    "Mod+Ctrl+F" = "window-toggle-maximize";
    # Nouveau : maximize-to-edges (sans gap ni bordure) n'existait pas non
    # plus dans ta traduction — utile pour un vrai plein cadre sans
    # dépendre du gap du workspace.
    "Mod+Shift+F" = "window-toggle-maximize-to-edges";
    "Mod+Minus" = "window-modify-width:-0.1";
    "Mod+Equal" = "window-modify-width:0.1";
    # Fix : center-column/center-visible-columns de niri ont enfin un
    # équivalent trouvé (column-center), + window-center pour les flottantes.
    "Mod+C" = "column-center";
    "Mod+Shift+C" = "window-center";
    # ⚠ Toujours aucune action de hauteur de fenêtre (set-window-height) ni
    # de tabbed-column-display trouvée dans la doc Umbriel. Non mappés.

    # ─── Modes ───
    "Mod+T" = "window-toggle-floating";
    "Mod+F" = "window-toggle-fullscreen";
    "Mod+Shift+T" = "window-toggle-pinned"; # nouveau : épingle au-dessus du plein écran

    # ─── Captures d'écran ───
    "Ctrl+Shift+1" = "spawn:noctalia msg screenshot-region";
    "Ctrl+Shift+2" = "spawn:noctalia msg screenshot-fullscreen";
    # Fix : capture de la "fenêtre active" — grim+slurp en ciblage manuel
    # (clic sur la fenêtre), la doc ne liste toujours pas d'action native
    # "fenêtre focus" ; c'est l'équivalent le plus proche disponible.
    "Ctrl+Shift+3" = ''spawn:sh -c "grim -g \"$(slurp -w)\" - | wl-copy"'';

    # ⚠ Toujours pas d'équivalent à toggle-keyboard-shortcuts-inhibit de
    # niri (débloquer les raccourcis capturés par une appli plein écran).
    # `submap:reset` existe mais résout un problème différent (sortir d'un
    # submap).

    "Ctrl+Alt+Delete" = "session-quit";
    "Mod+Shift+R" = "config-reload";
    "Mod+Shift+P" = "dpms-off";
    "Mod+Shift+Alt+P" = "dpms-on";
    "Mod+O" = { action = "overview-toggle"; repeat = false; };

    # ─── Scratchpad ───
    # Fonctionnalité Umbriel sans équivalent niri, absente de ta config
    # d'origine. Bindings inspirés de la config packagée par défaut, avec
    # Mod+Tab laissé libre pour workspace-previous ci-dessus.
    "Mod+Shift+Space" = "window-move-to-scratchpad";
    "Mod+Space" = "scratchpad-toggle";
    "Mod+Ctrl+Space" = "window-restore-from-scratchpad";
    "Mod+Alt+Space" = "scratchpad-focus-next";
  };
  };
}

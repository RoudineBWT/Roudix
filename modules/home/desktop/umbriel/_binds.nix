## _binds.nix — Umbriel: [keybinds].
##
## Doc : https://docs.noctalia.dev/umbriel/keybinds/
##       https://docs.noctalia.dev/umbriel/actions/
##       https://docs.noctalia.dev/umbriel/scratchpads/
{ ... }:
{
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

    # ─── Workspaces nommés (Mod+1..8) ───
    # ⚠ Comportement absolu (pas relatif au output courant comme sous niri) :
    # workspace-switch résout un nom exact et global, cf. doc Actions.
    "Mod+1" = "workspace-switch:󰈹"; # Firefox / Zen / Brave (Legion #1)
    "Mod+2" = "workspace-switch:";  # Zed (Legion #2)
    "Mod+3" = "workspace-switch:";  # kitty / Ptyxis (Legion #3)
    "Mod+4" = "workspace-switch:󰊗"; # Steam / jeux (Legion #4)
    "Mod+5" = "workspace-switch:󰉋"; # Fichiers (Legion #5)
    "Mod+6" = "workspace-switch:";  # Discord / Element / Telegram (HKC #1)
    "Mod+7" = "workspace-switch:󰝚"; # Spotify / EasyEffects (HKC #2)
    "Mod+8" = "workspace-switch:";  # brave-browser (HKC #3)

    "Mod+Ctrl+1" = "window-move-to-workspace:󰈹";
    "Mod+Ctrl+2" = "window-move-to-workspace:";
    "Mod+Ctrl+3" = "window-move-to-workspace:";
    "Mod+Ctrl+4" = "window-move-to-workspace:󰊗";
    "Mod+Ctrl+5" = "window-move-to-workspace:󰉋";
    "Mod+Ctrl+6" = "window-move-to-workspace:";
    "Mod+Ctrl+7" = "window-move-to-workspace:󰝚";
    "Mod+Ctrl+8" = "window-move-to-workspace:";

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
    "Mod+Shift+R" = "spawn:noctalia msg config-reload";
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
}

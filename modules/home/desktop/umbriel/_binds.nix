## _binds.nix — Umbriel: [keybinds].
##
## Docs: https://docs.noctalia.dev/umbriel/keybinds/
##       https://docs.noctalia.dev/umbriel/actions/
##       https://docs.noctalia.dev/umbriel/scratchpads/
{ lib, osConfig, ... }:
let
  scratchpadApps = osConfig.roudix.umbriel.scratchpadApps or false;
in
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

    # ─── Additional Noctalia panels ───
    # From the official "Noctalia shell integration" example in the
    # keybinds doc.
    "Mod+V" = "spawn:noctalia msg panel-toggle clipboard";  # clipboard manager
    "Mod+W" = "spawn:noctalia msg panel-toggle wallpaper";  # wallpaper picker
    "Mod+Z" = "spawn:noctalia msg panel-toggle launcher /emo"; # emoji picker
    "Mod+N" = "spawn:noctalia msg panel-toggle noctalia/notes:panel"; # notes panel

    # ─── Audio ───
    # allow_when_locked lets these shortcuts work even with the screen
    # locked, equivalent to niri's allow-when-locked=true.
    "XF86AudioRaiseVolume" = { action = "spawn:noctalia msg volume-up"; allow_when_locked = true; };
    "XF86AudioLowerVolume" = { action = "spawn:noctalia msg volume-down"; allow_when_locked = true; };
    "XF86AudioMute" = { action = "spawn:noctalia msg volume-mute"; allow_when_locked = true; };
    "XF86AudioMicMute" = { action = "spawn:noctalia msg mic-mute"; allow_when_locked = true; };
    "XF86AudioPlay" = { action = "spawn:playerctl play-pause"; allow_when_locked = true; };
    "XF86AudioPrev" = { action = "spawn:playerctl previous"; allow_when_locked = true; };
    "XF86AudioNext" = { action = "spawn:playerctl next"; allow_when_locked = true; };

    # ─── Windows: focus / movement ───
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

    # niri equivalent of focus-column-first/last and move-column-to-first/last.
    "Mod+Home" = "column-focus-first";
    "Mod+End" = "column-focus-last";
    "Mod+Ctrl+Home" = "column-move-to-first";
    "Mod+Ctrl+End" = "column-move-to-last";

    # niri-style consume/expel: stack the focused window into the
    # neighboring column, or split it back out into its own column.
    "Mod+BracketLeft" = "window-consume-or-expel-left";
    "Mod+BracketRight" = "window-consume-or-expel-right";
    "Mod+Shift+BracketLeft" = "window-consume-left";
    "Mod+Shift+BracketRight" = "window-consume-right";

    "Mod+Shift+Left" = "output-focus-left";
    "Mod+Shift+Right" = "output-focus-right";
    "Mod+Shift+Up" = "output-focus-up";
    "Mod+Shift+Down" = "output-focus-down";

    "Mod+Shift+Ctrl+Left" = "column-move-to-output-left";
    "Mod+Shift+Ctrl+Right" = "column-move-to-output-right";
    "Mod+Shift+Ctrl+Up" = "column-move-to-output-up";
    "Mod+Shift+Ctrl+Down" = "column-move-to-output-down";

    # ─── Wheel: navigation ───
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

    # ─── Workspaces (Mod+1..9) ───
    # Relative to the focused monitor (like niri), not an absolute jump to
    # an exact name: per the Actions doc, a unique numeric name resolves
    # globally, but when no exact name matches, the number selects that
    # 1-based position on the focused output.
    # ⚠ Workspace names in _output.nix are chosen so no name is an exact
    # number ("L6".."L9" / "H4".."H9" etc.) — a literal numeric name that's
    # unique to one output would otherwise always jump to that output,
    # ignoring which monitor has focus. Current layout:
    # Legion (DP-1) → 1 web, 2 zed, 3 term, 4 games, 5 files, 6-9 empty.
    # HKC (DP-3)    → 1 chat, 2 music, 3 web (brave), 4-9 empty.
    "Mod+1" = "workspace-switch:1"; # Legion: web · HKC: chat
    "Mod+2" = "workspace-switch:2"; # Legion: zed · HKC: music
    "Mod+3" = "workspace-switch:3"; # Legion: term · HKC: web (brave)
    "Mod+4" = "workspace-switch:4"; # Legion: games · HKC: empty (H4)
    "Mod+5" = "workspace-switch:5"; # Legion: files · HKC: empty (H5)
    "Mod+6" = "workspace-switch:6"; # empty on both sides (L6 / H6)
    "Mod+7" = "workspace-switch:7"; # empty on both sides (L7 / H7)
    "Mod+8" = "workspace-switch:8"; # empty on both sides (L8 / H8)
    "Mod+9" = "workspace-switch:9"; # empty on both sides (L9 / H9)

    "Mod+Ctrl+1" = "window-move-to-workspace:1";
    "Mod+Ctrl+2" = "window-move-to-workspace:2";
    "Mod+Ctrl+3" = "window-move-to-workspace:3";
    "Mod+Ctrl+4" = "window-move-to-workspace:4";
    "Mod+Ctrl+5" = "window-move-to-workspace:5";
    "Mod+Ctrl+6" = "window-move-to-workspace:6";
    "Mod+Ctrl+7" = "window-move-to-workspace:7";
    "Mod+Ctrl+8" = "window-move-to-workspace:8";
    "Mod+Ctrl+9" = "window-move-to-workspace:9";

    # ⚠ workspace-previous is positional (no wrap, no "last active" like
    # niri's MRU) — always an approximation.
    "Mod+Tab" = "workspace-previous";
    "Alt+Tab" = "spawn:noctalia msg window-switcher";

    # ─── Layout ───
    "Mod+Ctrl+F" = "window-toggle-maximize";
    # maximize-to-edges: true edge-to-edge fullscreen, ignoring the
    # workspace gap.
    "Mod+Shift+F" = "window-toggle-maximize-to-edges";
    # window-modify-primary-extent replaces the old generic
    # window-modify-width action (removed from Umbriel in favor of an
    # "extent" vocabulary shared across the 3 layouts — scrolling/dwindle/
    # master — plus edge-anchored variants like
    # window-modify-width-left/-right). It resizes the column/lane along
    # the active layout's main axis, with no particular anchor.
    "Mod+Minus" = "window-modify-primary-extent:-0.1";
    "Mod+Equal" = "window-modify-primary-extent:0.1";
    # Secondary extent (row height within a column/master area/stack) —
    # niri's set-window-height equivalent, now available.
    "Mod+Shift+Minus" = "window-modify-secondary-extent:-0.1";
    "Mod+Shift+Equal" = "window-modify-secondary-extent:0.1";
    # niri's center-column/center-visible-columns equivalents.
    "Mod+C" = "column-center";
    "Mod+Shift+C" = "window-center";
    # No tabbed-column-display equivalent in Umbriel. Not mapped.

    # ─── Master layout (chat workspace, DP-3/1) ───
    # No-op outside master layout (see Actions → Layout differences).
    "Mod+Ctrl+Equal" = "layout-master-count-increase";
    "Mod+Ctrl+Minus" = "layout-master-count-decrease";

    # ─── Modes ───
    "Mod+T" = "window-toggle-floating";
    "Mod+F" = "window-toggle-fullscreen";
    "Mod+Shift+T" = "window-toggle-pinned"; # pins above fullscreen

    # ─── Screenshots ───
    "Ctrl+Shift+1" = "spawn:noctalia msg screenshot-region";
    "Ctrl+Shift+2" = "spawn:noctalia msg screenshot-fullscreen";
    # Active-window capture via grim+slurp with manual targeting (click on
    # the window) — Umbriel has no native "focused window" action.
    "Ctrl+Shift+3" = ''spawn:sh -c "grim -g \"$(slurp -w)\" - | wl-copy"'';

    # niri's toggle-keyboard-shortcuts-inhibit equivalent: releases
    # shortcuts captured by a fullscreen game/remote-desktop client.
    # allow_when_inhibited=true keeps this one escape hatch working even
    # while inhibited — Umbriel would otherwise pass it through too.
    "Mod+Ctrl+Shift+Escape" = { action = "shortcuts-inhibit-toggle"; allow_when_inhibited = true; repeat = false; };

    "Ctrl+Alt+Delete" = "session-quit";
    "Mod+Shift+R" = "config-reload";
    "Mod+Shift+P" = "dpms-off";
    "Mod+Shift+Alt+P" = "dpms-on";
    "Mod+O" = { action = "overview-toggle"; repeat = false; };
  }
  # ─── Scratchpad ───
  # scratchpadApps=false: implicit "default" scratchpad (no [[scratchpad]]
  # entry in _rules.nix), so the 4 actions below have no suffix.
  // (if !scratchpadApps then {
    "Mod+Shift+Space" = "window-move-to-scratchpad";
    "Mod+Space" = "scratchpad-toggle";
    "Mod+Ctrl+Space" = "window-restore-from-scratchpad";
    "Mod+Alt+Space" = "scratchpad-focus-next";
  } else {
    # scratchpadApps=true: 3 named scratchpads (see _rules.nix). Declaring
    # a named scratchpad disables the implicit "default", so every action
    # takes a ":name" suffix.

    "Mod+Shift+Space" = ''spawn:sh -c "umbriel msg window-toggle-pinned; umbriel msg window-move-to-scratchpad:misc"'';
    "Mod+Space" = "scratchpad-toggle:misc";
    "Mod+Ctrl+Space" = "window-restore-from-scratchpad:misc";
    "Mod+Alt+Space" = "scratchpad-focus-next:misc";

    # "communication" (Discord+Telegram) and "music" (Spotify): *-toggle
    # shows/hides everything the rule assigned there. *-Shift-* uses
    # window-toggle-scratchpad (bidirectional on the focused window)
    # rather than the one-way window-restore-from-scratchpad, so a window
    # can also be sent back into the scratchpad.
    "Mod+Alt+D" = "scratchpad-toggle:communication";
    "Mod+Alt+Shift+D" = "window-toggle-scratchpad:communication";
    "Mod+Ctrl+D" = "window-restore-from-scratchpad:communication";
    "Mod+Alt+M" = "scratchpad-toggle:music";
    "Mod+Alt+Shift+M" = "window-toggle-scratchpad:music";
    "Mod+Ctrl+M" = "window-restore-from-scratchpad:music";
  });
  };
}

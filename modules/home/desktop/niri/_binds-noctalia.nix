## _binds-noctalia.nix — niri: [binds] variante Noctalia.
##
## Syntaxe vérifiée contre un config niri-flake réel qui build
## (github.com/Ly-sec/nixos, desktops/niri/home/keybinds.nix) : les
## actions paramétrées prennent une LISTE (`action.set-column-width =
## [ "-10%" ];`, pas une valeur nue), et le titre affiché dans l'overlay
## est `hotkey-overlay.title`, pas `hotkey-overlay-title`.
{ ... }:
{
  programs.niri.settings = {
  binds = {
    "Mod+Shift+Escape".action = "show-hotkey-overlay";

    # ─── Applications ───
    "Mod+Return" = { hotkey-overlay.title = "Open Terminal: Ghostty"; action.spawn = [ "ghostty" ]; };
    "Mod+D" = { hotkey-overlay.title = "Open App Launcher: noctalia launcher"; action.spawn-sh = [ "noctalia msg panel-toggle launcher" ]; };
    "Mod+Shift+B" = { hotkey-overlay.title = "Open Browser: Zen"; action.spawn = [ "zen-twilight" ]; };
    "Mod+B" = { hotkey-overlay.title = "Open Browser: brave"; action.spawn = [ "brave-origin-beta" ]; };
    "Mod+Alt+L" = { hotkey-overlay.title = "Lock Screen: noctalia lock"; action.spawn-sh = [ "noctalia msg screen-lock" ]; };
    "Mod+E" = { hotkey-overlay.title = "File Manager: Nautilus"; action.spawn = [ "nautilus" ]; };
    "Mod+Shift+Q".action.spawn-sh = [ "noctalia msg panel-toggle session" ];

    # ─── Audio ───
    "XF86AudioRaiseVolume" = { allow-when-locked = true; action.spawn-sh = [ "noctalia msg volume-up" ]; };
    "XF86AudioLowerVolume" = { allow-when-locked = true; action.spawn-sh = [ "noctalia msg volume-down" ]; };
    "XF86AudioMute" = { allow-when-locked = true; action.spawn-sh = [ "noctalia msg volume-mute" ]; };
    "XF86AudioMicMute" = { allow-when-locked = true; action.spawn-sh = [ "noctalia msg mic-mute" ]; };
    "XF86AudioPlay" = { allow-when-locked = true; action.spawn = [ "playerctl" "play-pause" ]; };
    "XF86AudioPrev" = { allow-when-locked = true; action.spawn = [ "playerctl" "previous" ]; };
    "XF86AudioNext" = { allow-when-locked = true; action.spawn = [ "playerctl" "next" ]; };

    # ─── Fenêtres : focus / déplacement ───
    "Mod+Q".action = "close-window";

    "Mod+Left".action = "focus-column-left";
    "Mod+H".action = "focus-column-left";
    "Mod+Right".action = "focus-column-right";
    "Mod+L".action = "focus-column-right";
    "Mod+Up".action = "focus-window-up";
    "Mod+K".action = "focus-window-up";
    "Mod+Down".action = "focus-window-down";
    "Mod+J".action = "focus-window-down";

    "Mod+Ctrl+Left".action = "move-column-left";
    "Mod+Ctrl+H".action = "move-column-left";
    "Mod+Ctrl+Right".action = "move-column-right";
    "Mod+Ctrl+L".action = "move-column-right";
    "Mod+Ctrl+Up".action = "move-window-up";
    "Mod+Ctrl+K".action = "move-window-up";
    "Mod+Ctrl+Down".action = "move-window-down";
    "Mod+Ctrl+J".action = "move-window-down";

    "Mod+Home".action = "focus-column-first";
    "Mod+End".action = "focus-column-last";
    "Mod+Ctrl+Home".action = "move-column-to-first";
    "Mod+Ctrl+End".action = "move-column-to-last";

    "Mod+Shift+Left".action = "focus-monitor-left";
    "Mod+Shift+Right".action = "focus-monitor-right";
    "Mod+Shift+Up".action = "focus-monitor-up";
    "Mod+Shift+Down".action = "focus-monitor-down";

    "Mod+Shift+Ctrl+Left".action = "move-column-to-monitor-left";
    "Mod+Shift+Ctrl+Right".action = "move-column-to-monitor-right";
    "Mod+Shift+Ctrl+Up".action = "move-column-to-monitor-up";
    "Mod+Shift+Ctrl+Down".action = "move-column-to-monitor-down";

    # ─── Molette ───
    "Mod+WheelScrollDown" = { cooldown-ms = 150; action = "focus-workspace-down"; };
    "Mod+WheelScrollUp" = { cooldown-ms = 150; action = "focus-workspace-up"; };
    "Mod+Ctrl+WheelScrollDown" = { cooldown-ms = 150; action = "move-column-to-workspace-down"; };
    "Mod+Ctrl+WheelScrollUp" = { cooldown-ms = 150; action = "move-column-to-workspace-up"; };

    "Mod+WheelScrollRight".action = "focus-column-right";
    "Mod+WheelScrollLeft".action = "focus-column-left";
    "Mod+Ctrl+WheelScrollRight".action = "move-column-right";
    "Mod+Ctrl+WheelScrollLeft".action = "move-column-left";

    "Mod+Shift+WheelScrollDown".action = "focus-column-right";
    "Mod+Shift+WheelScrollUp".action = "focus-column-left";
    "Mod+Ctrl+Shift+WheelScrollDown".action = "move-column-right";
    "Mod+Ctrl+Shift+WheelScrollUp".action = "move-column-left";

    # ─── Workspaces (index numériques 1..9) ───
    "Mod+1".action.focus-workspace = [ 1 ];
    "Mod+2".action.focus-workspace = [ 2 ];
    "Mod+3".action.focus-workspace = [ 3 ];
    "Mod+4".action.focus-workspace = [ 4 ];
    "Mod+5".action.focus-workspace = [ 5 ];
    "Mod+6".action.focus-workspace = [ 6 ];
    "Mod+7".action.focus-workspace = [ 7 ];
    "Mod+8".action.focus-workspace = [ 8 ];
    "Mod+9".action.focus-workspace = [ 9 ];

    "Mod+Ctrl+1".action.move-column-to-workspace = [ 1 ];
    "Mod+Ctrl+2".action.move-column-to-workspace = [ 2 ];
    "Mod+Ctrl+3".action.move-column-to-workspace = [ 3 ];
    "Mod+Ctrl+4".action.move-column-to-workspace = [ 4 ];
    "Mod+Ctrl+5".action.move-column-to-workspace = [ 5 ];
    "Mod+Ctrl+6".action.move-column-to-workspace = [ 6 ];
    "Mod+Ctrl+7".action.move-column-to-workspace = [ 7 ];
    "Mod+Ctrl+8".action.move-column-to-workspace = [ 8 ];
    "Mod+Ctrl+9".action.move-column-to-workspace = [ 9 ];

    "Mod+Tab".action = "focus-workspace-previous";
    "Alt+Tab".action.spawn-sh = [ "noctalia msg window-switcher" ];

    # ─── Layout ───
    "Mod+Ctrl+F".action = "expand-column-to-available-width";
    "Mod+C".action = "center-column";
    "Mod+Ctrl+C".action = "center-visible-columns";
    "Mod+Minus".action.set-column-width = [ "-10%" ];
    "Mod+Equal".action.set-column-width = [ "+10%" ];
    "Mod+Shift+Minus".action.set-window-height = [ "-10%" ];
    "Mod+Shift+Equal".action.set-window-height = [ "+10%" ];

    # ─── Modes ───
    "Mod+T".action = "toggle-window-floating";
    "Mod+F".action = "fullscreen-window";
    "Mod+W".action = "toggle-column-tabbed-display";

    # ─── Captures d'écran ───
    "Ctrl+Shift+1".action.screenshot = { };
    "Ctrl+Shift+2".action.screenshot-screen = { };
    "Ctrl+Shift+3".action.screenshot-window = { };

    # ─── Échappement d'urgence ───
    "Mod+Escape" = { allow-inhibiting = false; action = "toggle-keyboard-shortcuts-inhibit"; };

    # ─── Sortie / Alimentation ───
    "Ctrl+Alt+Delete".action = "quit";
    "Mod+Shift+R".action.spawn-sh = [ "noctalia msg config-reload" ];
    "Mod+Shift+P".action = "power-off-monitors";
    "Mod+O" = { repeat = false; action = "toggle-overview"; };
  };
  };
}

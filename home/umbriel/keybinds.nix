{ pkgs, config, lib, osConfig, ... }:

let
  terminalCmd = osConfig.roudix.terminal or "ghostty";
  terminal = "${pkgs.${terminalCmd}}/bin/${terminalCmd}";

  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  fileManager = "${pkgs.${fileManagerCmd}}/bin/${fileManagerCmd}";

  browserCmd = osConfig.roudix.browser.command or null;
  browser = if browserCmd != null then "${pkgs.${browserCmd}}/bin/${browserCmd}" else null;

  browserList = osConfig.roudix.browser.commands or [ ];
  browserDefault = osConfig.roudix.browser.default or null;
  extraBrowsers = lib.filter (b: b.name != browserDefault) browserList;

  noctalia = lib.getExe config.programs.noctalia.package;
  playerctl = "${pkgs.playerctl}/bin/playerctl";
in
{
  programs.umbriel.settings.keybinds = {
    # ─── Applications ──────────────────────────────────────────────────────
    "Mod+Return" = "spawn:${terminal}";
    "Mod+E" = "spawn:${fileManager}";
    "Mod+D" = "spawn:${noctalia} msg panel-toggle launcher";
    "Mod+Alt+L" = "spawn:${noctalia} msg screen-lock";
    "Mod+Shift+Q" = "spawn:${noctalia} msg panel-toggle session";
    "Mod+Shift+R" = "spawn:${noctalia} msg config-reload";
    "Mod+Shift+B" = "spawn:${browser}";

    # Navigateurs supplémentaires (MOD+CTRL+ALT+1,2,3...)
  } // (if browser != null then {
    "Mod+B" = "spawn:${browser}";
  } else {}) // (lib.listToAttrs (lib.imap1 (i: b: {
    name = "Mod+Ctrl+Alt+${toString i}";
    value = "spawn:${b.command}";
  }) extraBrowsers)) // {

    # ─── Audio (Niri avait XF86) ──────────────────────────────────────────
    "XF86AudioRaiseVolume" = "spawn:${noctalia} msg volume-up";
    "XF86AudioLowerVolume" = "spawn:${noctalia} msg volume-down";
    "XF86AudioMute" = "spawn:${noctalia} msg volume-mute";
    "XF86AudioMicMute" = "spawn:${noctalia} msg mic-mute";

    # ─── Media ─────────────────────────────────────────────────────────────
    "XF86AudioPlay" = "spawn:${playerctl} play-pause";
    "XF86AudioPrev" = "spawn:${playerctl} previous";
    "XF86AudioNext" = "spawn:${playerctl} next";

    # ─── Window / Focus (adapté de Niri) ──────────────────────────────────
    "Mod+Q" = "window-close";
    "Mod+Left" = "window-focus-left";
    "Mod+H" = "window-focus-left";
    "Mod+Right" = "window-focus-right";
    "Mod+L" = "window-focus-right";
    "Mod+Up" = "window-focus-up";
    "Mod+K" = "window-focus-up";
    "Mod+Down" = "window-focus-down";
    "Mod+J" = "window-focus-down";

    # ─── Move Windows ──────────────────────────────────────────────────────
    "Mod+Ctrl+Left" = "column-move-left";
    "Mod+Ctrl+H" = "column-move-left";
    "Mod+Ctrl+Right" = "column-move-right";
    "Mod+Ctrl+L" = "column-move-right";
    "Mod+Ctrl+Up" = "window-move-up";
    "Mod+Ctrl+K" = "window-move-up";
    "Mod+Ctrl+Down" = "window-move-down";
    "Mod+Ctrl+J" = "window-move-down";

    # ─── Workspace Navigation (Niri avait MOD+WheelScroll) ───────────────
    "Mod+WheelScrollDown" = "workspace-switch-down";
    "Mod+WheelScrollUp" = "workspace-switch-up";
    "Mod+Ctrl+WheelScrollDown" = "window-move-to-workspace-down";
    "Mod+Ctrl+WheelScrollUp" = "window-move-to-workspace-up";

    # ─── Workspace Quick Switch ───────────────────────────────────────────
    "Mod+1" = "workspace-switch:1";
    "Mod+2" = "workspace-switch:2";
    "Mod+3" = "workspace-switch:3";
    "Mod+4" = "workspace-switch:4";
    "Mod+5" = "workspace-switch:5";
    "Mod+6" = "workspace-switch:6";
    "Mod+7" = "workspace-switch:7";
    "Mod+8" = "workspace-switch:8";
    "Mod+9" = "workspace-switch:9";

    "Mod+Ctrl+1" = "window-move-to-workspace:1";
    "Mod+Ctrl+2" = "window-move-to-workspace:2";
    "Mod+Ctrl+3" = "window-move-to-workspace:3";
    "Mod+Ctrl+4" = "window-move-to-workspace:4";
    "Mod+Ctrl+5" = "window-move-to-workspace:5";
    "Mod+Ctrl+6" = "window-move-to-workspace:6";
    "Mod+Ctrl+7" = "window-move-to-workspace:7";
    "Mod+Ctrl+8" = "window-move-to-workspace:8";
    "Mod+Ctrl+9" = "window-move-to-workspace:9";

    "Mod+Tab" = "workspace-switch-previous";
    "Alt+Tab" = "spawn:${noctalia} msg window-switcher";

    # ─── Layout ────────────────────────────────────────────────────────────
    "Mod+Ctrl+F" = "window-toggle-maximize";  # Niri avait expand-column-to-available-width
    "Mod+C" = "column-center";  # Niri avait center-column
    "Mod+Ctrl+C" = "workspace-center";  # Niri avait center-visible-columns
    "Mod+minus" = "column-resize:-10%";
    "Mod+equal" = "column-resize:+10%";
    "Mod+Shift+minus" = "window-resize:-10%";
    "Mod+Shift+equal" = "window-resize:+10%";

    # ─── Modes ─────────────────────────────────────────────────────────────
    "Mod+T" = "window-toggle-floating";
    "Mod+F" = "window-toggle-fullscreen";
    "Mod+W" = "window-toggle-tabbed";  # Niri avait toggle-column-tabbed-display

    # ─── Screenshots ──────────────────────────────────────────────────────
    "Ctrl+Shift+1" = "screenshot";
    "Ctrl+Shift+2" = "screenshot-output";
    "Ctrl+Shift+3" = "screenshot-window";

    # ─── Emergency ─────────────────────────────────────────────────────────
    "Mod+Escape" = "shortcuts-inhibit-toggle";

    # ─── Exit / Power ─────────────────────────────────────────────────────
    "Ctrl+Alt+Delete" = "session-quit";
    "Mod+Shift+P" = "outputs-power-off";
    "Mod+O" = "overview-toggle";
  };
}

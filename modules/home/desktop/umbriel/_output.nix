## _output.nix — Umbriel: [output.NAME] + [[workspace]] (per-workspace
## rules).
##
## TODO: run `umbriel outputs` in session and replace DP-1/DP-3 below with
## the actual connector names if needed (e.g. DP-1, HDMI-A-1 — Umbriel
## wants the physical connector name, not "Vendor Model Serial" like niri).
##
## Docs: https://docs.noctalia.dev/umbriel/outputs/
##       https://docs.noctalia.dev/umbriel/workspaces/#workspace-rules
{ ... }:
{
  programs.umbriel.settings = {
  output = {
    "DP-1" = { # Lenovo Legion 27Q-10, 2560x1440@240
      mode = "2560x1440@240.000";
      position = [ 1920 0 ];
      scale = 1;
      vrr = "fullscreen"; # niri: variable-refresh-rate on-demand=true
      # Allows async tearing on this output. This is a safety gate: Umbriel
      # only uses it for a fullscreen window that requests it (or via
      # window_rule tearing=true in _rules.nix). Remove if tearing shows up
      # outside games.
      tearing = true;
      # ⚠ A workspace name that's a plain number ("4", "5"...) and exists
      # ONLY on this output becomes a globally unique name. Per the docs
      # (docs.noctalia.dev/umbriel/actions/), workspace selectors resolve
      # exact names globally first, and a unique name jumps to its own
      # output regardless of which monitor has focus. "4"/"5" used to be
      # unique to DP-3, so Mod+4/Mod+5 always jumped to the HKC. The
      # L/H-prefixed "6".."9" below are no longer exact numeric names, so
      # Mod+1..9 now always resolves by "position N on the focused
      # monitor" per-screen, as intended.
      workspaces = [ "󰈹" "" "" "󰊗" "󰉋" "L6" "L7" "L8" "L9"  ];
    };

    "DP-3" = { # HKC 24E4, 1920x1080@165
      mode = "1920x1080@165.001";
      position = [ 0 0 ];
      scale = 1;
      workspaces = [ "" "󰝚" "" "H4" "H5" "H6" "H7" "H8" "H9" ];
    };
  };

  # ── Workspace rules ──────────────────────────────────────────────────
  # Global mode (_layout.nix): "scrolling". Each workspace gets its own
  # layout.mode override here ("scrolling", "dwindle" or "master").
  #
  # Web (DP-1/1, DP-3/3)  → scrolling
  # Zed (DP-1/2)          → dwindle
  # Term (DP-1/3)         → dwindle
  # Games (DP-1/4)        → master
  # Files (DP-1/5)        → dwindle
  # Chat (DP-3/1)         → master
  # Music (DP-3/2)        → dwindle
  workspace = [
    {
      output = "DP-1";
      index = 1; # web (firefox / zen / brave-origin-beta)
      layout.mode = "scrolling";
    }
    {
      output = "DP-1";
      index = 2; # zed
      layout.mode = "dwindle";
    }
    {
      output = "DP-1";
      index = 3; # term (kitty / ptyxis)
      layout.mode = "dwindle";
    }
    {
      output = "DP-1";
      index = 4; # games — no gap since Steam/Heroic/PrismLauncher/
                 # Minecraft already open maximized or fullscreen
                 # (see _rules.nix); avoids a visible gap strip in-game.
      layout.mode = "scrolling";
      layout.gap = 0;
    }
    {
      output = "DP-1";
      index = 5; # files (nautilus / gnome-text-editor)
      layout.mode = "dwindle";
    }
    {
      output = "DP-3";
      index = 1; # chat (discord / element / telegram — already floating
                 # via _rules.nix, so the mode only affects anything else
                 # tiled on this workspace)
      layout.mode = "master";
    }
    {
      output = "DP-3";
      index = 2; # music (spotify / easyeffects)
      layout.mode = "dwindle";
    }
    {
      output = "DP-3";
      index = 3; # web (brave-browser)
      layout.mode = "scrolling";
    }
  ];
  };
}

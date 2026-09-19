## _output.nix — niri: [output.NAME] + [workspaces] (identical between
## noctalia and dms).
##
## Uses connector names (DP-1/DP-3) rather than "Vendor Model Serial" —
## same identifiers as on the Umbriel side, for consistency between the
## two compositors.
## ⚠ Trade-off: if a monitor moves to a different DP port on the card, the
## config stays attached to the PORT, not the physical monitor. Reconfirm
## with `niri msg outputs` after any cabling change.
{ ... }:
let
  ws = import ./_ws.nix { };
  legion = "DP-1";
  hkc    = "DP-3";
in
{
  programs.niri.settings = {
    outputs = {
      "${hkc}" = {
        mode = { width = 1920; height = 1080; refresh = 165.001; };
        scale = 1.0;
        position = { x = 0; y = 0; };
      };

      "${legion}" = {
        mode = { width = 2560; height = 1440; refresh = 240.000; };
        scale = 1.0;
        position = { x = 1920; y = 0; };
        variable-refresh-rate = "on-demand";
      };
    };

    # niri-flake creates named workspaces sorted by the attrset KEY (per
    # the docs: workspaces are created in key order, with an optional
    # `name` for a friendlier display name). Since our keys used to be
    # the Nerd Font glyphs directly (Unicode codepoints), the bar ended up
    # sorted by codepoint value instead of the intended order. Fixed by
    # using an explicit numeric prefix as the key (controls ordering per
    # output) and moving the actual glyph into `name` — `name` is what
    # niri uses as the workspace name (referenced by _rules-*.nix /
    # _binds-*.nix via `ws.xxx`); the key is now purely for sorting.
    workspaces = {
      "1-${ws.web}"   = { name = ws.web; open-on-output = legion; };
      "2-${ws.code}"  = { name = ws.code; open-on-output = legion; };
      "3-${ws.term}"  = { name = ws.term; open-on-output = legion; };
      "4-${ws.games}" = {
        name = ws.games;
        open-on-output = legion;
        # Per-workspace layout override (niri 25.11+). No gap on the games
        # workspace since Steam/Heroic/PrismLauncher/Minecraft already
        # open maximized or fullscreen (see _rules-*.nix).
        layout.gaps = 0;
      };
      "5-${ws.files}"    = { name = ws.files; open-on-output = legion; };

      "1-${ws.chat}"     = { name = ws.chat; open-on-output = hkc; };
      "2-${ws.music}"    = { name = ws.music; open-on-output = hkc; };
      "3-${ws.browser2}" = { name = ws.browser2; open-on-output = hkc; };
    };
  };
}

## _rules-dms.nix — niri: extra rules specific to DMS. Concatenated
## automatically with _rules-common.nix by the module system (see
## default.nix).
##
## ⚠ These layer-rules target `dms:*` namespaces managed by DMS itself.
## Check for overlap with what DMS already applies via its own live files
## (wpblur.kdl, colors.kdl, included by _include-dms.nix).
{ ... }:
{
  programs.niri.settings = {
    window-rules = [
      {
        matches = [ { app-id = "spotify"; } ];
        open-on-workspace = (import ./_ws.nix { }).music;
        open-maximized = true;
      }
    ];

    layer-rules = [
      {
        matches = [ { namespace = "^dms:clipboard$"; } ];
        block-out-from = "screencast";
      }
      # Same logic as the noctalia side (_rules-noctalia.nix): hides
      # notification toasts from capture/streaming, not the bar/dock.
      # ⚠ Namespace not directly confirmed — verify with `niri msg layers`
      # in a DMS session that notifications are really "dms:osd" (inferred
      # by analogy with the confirmed dms:bar/dms:dock/dms:clipboard).
      {
        matches = [ { namespace = "^dms:osd$"; } ];
        block-out-from = "screencast";
      }
      {
        matches = [ { namespace = "^dms:bar$"; } { namespace = "^dms:dock$"; } ];
        shadow = {
          on = true;
          softness = 40;
          spread = 5;
          offset = { x = 0; y = 5; };
          draw-behind-window = true;
          color = "#00000064";
        };
      }
    ];
  };
}

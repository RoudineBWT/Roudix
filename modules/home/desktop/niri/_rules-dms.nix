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
      # DMS's own wallpaper layer isn't placed on niri's overview backdrop
      # by default; without this it gets cloned onto every workspace card
      # in the overview instead of staying fixed. "quickshell" is the raw
      # namespace DMS's wallpaper surface uses (regardless of the
      # dms:-prefixed convention for the rest of its layers).
      {
        matches = [ { namespace = "^quickshell$"; } ];
        place-within-backdrop = true;
      }
      # Only relevant if DMS's "Blur Layer" wallpaper option is enabled
      # (Settings → Wallpaper): that variant runs on its own namespace.
      {
        matches = [ { namespace = "dms:blurwallpaper"; } ];
        place-within-backdrop = true;
      }
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

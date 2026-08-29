## _rules-dms.nix — niri: règles additionnelles spécifiques à DMS.
## Concaténé automatiquement avec _rules-common.nix par le système de
## modules (voir default.nix).
##
## ⚠ Ces layer-rules ciblent les namespaces `dms:*` gérés par DMS
## lui-même. Vérifie qu'il n'y a pas de double emploi avec ce que DMS
## applique déjà via ses propres fichiers live (wpblur.kdl, colors.kdl,
## inclus par _include-dms.nix).
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

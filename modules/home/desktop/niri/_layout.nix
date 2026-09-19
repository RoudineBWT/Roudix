## _layout.nix — niri: [layout].
##
## Colors (focus-ring/border/shadow/tab-indicator/insert-hint) are NOT
## set here: they live in noctalia.kdl / dms/colors.kdl, regenerated live
## by Noctalia (matugen) / DMS and injected via `include` in
## _include-noctalia.nix / _include-dms.nix (see default.nix).
{ osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
in
{
  programs.niri.settings.layout = {
    gaps = 9;
    center-focused-column = if isNoctalia then "never" else "on-overflow";
    background-color = "transparent"; # let the shell handle the wallpaper

    preset-column-widths = [
      { proportion = 0.33333; }
      { proportion = 0.5; }
      { proportion = 0.66667; }
    ];

    struts = { };
  };
}

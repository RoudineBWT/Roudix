## _layout.nix — niri: [layout].
##
## Les couleurs (focus-ring/border/shadow/tab-indicator/insert-hint) ne
## sont PAS ici : elles vivent dans noctalia.kdl / dms/colors.kdl,
## régénérés en live par Noctalia (matugen) / DMS et injectés via
## `include` dans _include-noctalia.nix / _include-dms.nix (cf. default.nix).
{ osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
in
{
  programs.niri.settings.layout = {
    gaps = 9;
    center-focused-column = if isNoctalia then "never" else "on-overflow";
    background-color = "transparent"; # laisse le shell gérer le wallpaper

    preset-column-widths = [
      { proportion = 0.33333; }
      { proportion = 0.5; }
      { proportion = 0.66667; }
    ];

    struts = { };
  };
}

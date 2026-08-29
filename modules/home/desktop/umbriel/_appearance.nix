## _appearance.nix — Umbriel: [appearance], [appearance.blur],
## [appearance.shadow].
##
## Les couleurs ([colors], border_focused/unfocused, insert_hint_color)
## ne sont PAS ici : Umbriel a un vrai mécanisme d'include natif
## (programs.umbriel.settings.include.files, voir _include-noctalia.nix)
## qui charge ~/.config/umbriel/noctalia.toml — regénéré en live par le
## matugen de Noctalia à chaque wallpaper. Technique confirmée par
## github.com/Ly-sec/nixos (desktops/umbriel/home/noctalia-include.nix).
{ ... }:
{
  programs.umbriel.settings = {
    appearance = {
      prefer_no_csd = true;
      corner_radius = 20;

      blur = {
        enabled = true;
        optimized = true;
        passes = 2;
        noise = 0.03;
        saturation = 1.0;
      };

      shadow = {
        enabled = true;
        color = "#00000070";
      };
    };
  };
}

## _include-noctalia.nix — charge ~/.config/umbriel/noctalia.toml,
## regénéré en live par le matugen de Noctalia à chaque changement de
## wallpaper. C'est le mécanisme natif d'Umbriel pour ça (contrairement à
## niri, pas besoin d'astuce de concaténation de texte).
{ ... }:
{
  programs.umbriel.settings.include.files = [ "noctalia.toml" ];
}

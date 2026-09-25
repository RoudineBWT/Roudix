## _include-noctalia.nix — loads ~/.config/umbriel/noctalia.toml,
## regenerated live by Noctalia's matugen on every wallpaper change.
## This is Umbriel's native mechanism for this (unlike niri, no
## text-concatenation trick needed).
{ ... }:
{
  programs.mango.settings.include.files = [ "noctalia.conf" ];
}

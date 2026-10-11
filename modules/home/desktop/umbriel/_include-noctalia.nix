## _include-noctalia.nix — loads ~/.config/umbriel/noctalia.toml,
## regenerated live by Noctalia's matugen on every wallpaper change.
## This is Umbriel's native mechanism for this (unlike niri, no
## text-concatenation trick needed).
##
## It goes under `include.optional`: a missing *required* include is an
## error ("include not found"), and noctalia.toml does not exist until
## Noctalia has generated it (first boot / before the first theme apply).
## Missing optional files are ignored and watched, so the config reloads
## by itself as soon as the file appears.
{ ... }:
{
  programs.umbriel.settings.include.optional.files = [ "~/.config/umbriel/noctalia.toml" ];
}

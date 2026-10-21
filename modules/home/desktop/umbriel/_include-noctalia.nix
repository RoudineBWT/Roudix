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
##
## The path is written exactly as `"noctalia.toml"` (relative to config.toml,
## so it is still ~/.config/umbriel/noctalia.toml) on purpose: Noctalia's
## umbriel template runs an apply.sh post_hook that rewrites config.toml to
## add `files = ["noctalia.toml"]` unless that exact entry is already the only
## one in [include.optional]. With any other spelling (e.g. "~/.config/...")
## it tries to edit/create config.toml, which Home Manager owns (read-only
## store symlink). Keep this string as is.
{ ... }:
{
  programs.umbriel.settings.include.optional.files = [ "noctalia.toml" ];
}

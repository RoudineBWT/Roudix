## _include-cursor.nix — OPT-IN: live cursor reload on Umbriel.
##
## theming/bibata-cursor.nix renders ~/.config/umbriel/bibata-cursor.toml
## ([input.cursor] theme = "Bibata-Modern-Roudix-<accent>-<outline>") on every
## Noctalia palette change. Including it makes Umbriel reload the cursor by
## itself; without it the new colours apply at the next login instead.
##
## NOT imported by default, because _include-noctalia.nix documents that
## Noctalia's umbriel template runs an apply.sh post_hook that rewrites
## config.toml unless "noctalia.toml" is the ONLY entry of [include.optional].
## Adding a second file may make that hook try to edit the Home Manager-owned
## config.toml. To enable: uncomment ./_include-cursor.nix in umbriel/default.nix,
## rebuild, change the wallpaper and check (a) no apply.sh error in Noctalia's
## log, (b) the cursor colours follow, (c) the included theme wins over
## `input.cursor.theme` of _input.nix. If (a) fails, drop this file again.
{ ... }:
{
  programs.umbriel.settings.include.optional.files = [ "bibata-cursor.toml" ];
}

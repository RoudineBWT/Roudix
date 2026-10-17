{ lib, ... }:
# Owned by scripts/roudix-config.py — do not edit by hand.
#
# Reads umbriel-managed.json (gitignored, written by the tool) and turns its
# `window_rule` list into Umbriel window rules. Nothing to do when the JSON
# doesn't exist. Imported from umbriel-custom.nix.
#
# mkAfter: Umbriel applies the LAST matching rule, so rules added through the
# tool must come after the ones shipped by the repo to be able to override them.
let
  file = ./umbriel-managed.json;
  data = if builtins.pathExists file then builtins.fromJSON (builtins.readFile file) else { };
in
{
  programs.umbriel.settings = lib.mkAfter {
    window_rule = data.window_rule or [ ];
  };
}

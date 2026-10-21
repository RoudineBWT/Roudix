# Roudix colour palette — single source of truth: assets/palette/Roudix.json
# (Noctalia colour-scheme format: mPrimary, mSurface, ... + terminal ANSI set).
#
# Exposes, to every Home Manager module:
#   config.roudix.palette.dark / .light   flat attrsets (primary, onPrimary,
#                                         surface, outline, error, hover, ...
#                                         plus .terminal.{normal,bright,...})
#   config.roudix.palette.active          dark or light, per roudix.palette.mode
#   config.roudix.palette.lib             helpers: noHash, hypr, hyprA
#   roudixPalette                         module argument = palette.active
#
# Also drops the JSON where other tools can read it:
#   ~/.config/roudix/palette.json
#   ~/.config/noctalia/colorschemes/Roudix/Roudix.json
{ lib, config, ... }:

let
  cfg = config.roudix.palette;

  paletteFile = ../../../assets/palette/Roudix.json;
  raw = builtins.fromJSON (builtins.readFile paletteFile);

  # "mOnPrimary" -> "onPrimary"
  unM = name:
    let rest = lib.removePrefix "m" name;
    in lib.toLower (builtins.substring 0 1 rest) + builtins.substring 1 (-1) rest;

  flatten = scheme:
    lib.mapAttrs' (n: v: lib.nameValuePair (if n == "terminal" then n else unM n) v) scheme;

  noHash = lib.removePrefix "#";
in
{
  options.roudix.palette = {
    mode = lib.mkOption {
      type = lib.types.enum [ "dark" "light" ];
      default = "dark";
      description = "Which variant of Roudix.json `roudix.palette.active` points to.";
    };
    dark = lib.mkOption { type = lib.types.attrs; readOnly = true; description = "Dark variant of the Roudix palette."; };
    light = lib.mkOption { type = lib.types.attrs; readOnly = true; description = "Light variant of the Roudix palette."; };
    active = lib.mkOption { type = lib.types.attrs; readOnly = true; description = "Palette variant selected by roudix.palette.mode."; };
    lib = lib.mkOption { type = lib.types.attrs; readOnly = true; description = "Colour helpers (noHash, hypr, hyprA)."; };
  };

  config = {
    roudix.palette = {
      dark = flatten raw.dark;
      light = flatten raw.light;
      active = flatten raw.${cfg.mode};
      lib = {
        inherit noHash;
        # "#FF8C42" -> "rgba(ff8c42ff)" (Hyprland)
        hypr = c: "rgba(${lib.toLower (noHash c)}ff)";
        hyprA = c: a: "rgba(${lib.toLower (noHash c)}${a})";
      };
    };

    _module.args.roudixPalette = cfg.active;

    xdg.configFile."roudix/palette.json".source = paletteFile;
    xdg.configFile."noctalia/palettes/Roudix.json".source = paletteFile;
  };
}

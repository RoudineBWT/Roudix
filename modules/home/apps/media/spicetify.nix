{ pkgs, inputs, lib, osConfig, ... }:
let
  spicePkgs = inputs.spicetify-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system};
  cfg = osConfig.roudix.spicetify;

  themeSrc = {
    colorful = ./spicetify/Colorful;
    comfy    = ./spicetify/Comfy;
  }.${cfg.theme};

  themeName = {
    colorful = "Colorful";
    comfy    = "Comfy";
  }.${cfg.theme};

  # Each theme's own default scheme, from its color.ini — used unless the
  # user sets roudix.spicetify.colorScheme explicitly.
  defaultScheme = {
    colorful = "noctalia";
    comfy    = "Comfy";
  }.${cfg.theme};
in
{
  imports = [ inputs.spicetify-nix.homeManagerModules.default ];

  programs.spicetify = {
    enable = true;
    theme = {
      name = themeName;
      src = themeSrc;
      injectCss = true;
      replaceColors = true;
      overwriteAssets = true;
    };
    colorScheme = if cfg.colorScheme != null then cfg.colorScheme else defaultScheme;

    enabledExtensions = with spicePkgs.extensions;
      lib.optional cfg.extensions.adblock.enable adblock
      ++ lib.optional cfg.extensions.hidePodcasts.enable hidePodcasts;

    enabledCustomApps = with spicePkgs.apps;
      lib.optional cfg.marketplace.enable marketplace;
  };
}

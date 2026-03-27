{ pkgs,inputs, ... }:
let
  spicePkgs = inputs.spicetify-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system};
in
{
  imports = [ inputs.spicetify-nix.homeManagerModules.default ];

  programs.spicetify = {
    enable = true;
     theme = {
    name = "Comfy";
    src = ./spicetify/Comfy;
    injectCss = true;
    replaceColors = true;
    overwriteAssets = true;
  };
  colorScheme = "Comfy";
    enabledExtensions = with spicePkgs.extensions; [
      adblock
      hidePodcasts
    ];
    enabledCustomApps = with spicePkgs.apps; [
      marketplace
    ];
  };
}

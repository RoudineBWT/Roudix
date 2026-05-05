{ config, lib, pkgs, inputs, ... }:

{
  imports = [ inputs.nix-gaming-edge.nixosModules.mesa-git ];

  options.roudix.mesa = {
    useGit = lib.mkEnableOption "mesa-git (bleeding-edge) au lieu de mesa stable";
  };

  # L'overlay doit être toujours présent pour que le module puisse
  # wrapper buildFHSEnv correctement, même quand useGit = false
  #nixpkgs.overlays = [ inputs.nix-gaming-edge.overlays.default ];

  config = lib.mkIf config.roudix.mesa.useGit {
    drivers.mesa-git = {
      enable = true;
      cacheCleanup = {
         enable = true;
         protonPackage = pkgs.proton-cachyos-x86_64-v3;
       };
     };
    };
}

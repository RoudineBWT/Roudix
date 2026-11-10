{ config, lib, pkgs, inputs, ... }:

let
  cfg = config.roudix.mesa;
in
{
  # drivers.mesa-git (nix-gaming-edge): only defines options until enabled.
  imports = [ inputs.nix-gaming-edge.nixosModules.mesa-git ];

  options.roudix.mesa = {
    useGit = lib.mkEnableOption "mesa-git (bleeding-edge) au lieu de mesa stable";

    gitSource = lib.mkOption {
      type = lib.types.enum [ "chaotic" "gaming-edge" ];
      default = "chaotic";
      description = ''
        Where mesa-git comes from when roudix.mesa.useGit = true (ignored
        otherwise: false = the stable Mesa from nixpkgs).

        "chaotic":     Chaotic-Nyx (chaotic.mesa-git).
        "gaming-edge": powerofthe69/nix-gaming-edge (drivers.mesa-git), which
                       also adds a "stable-mesa" boot entry as a fallback.
      '';
    };
  };

  config = lib.mkMerge [
    (lib.mkIf (cfg.useGit && cfg.gitSource == "chaotic") {
      chaotic.mesa-git.enable = true;
    })

    (lib.mkIf (cfg.useGit && cfg.gitSource == "gaming-edge") {
      # drivers.mesa-git asserts that pkgs.mesa-git exists; gaming.nix only adds
      # the nix-gaming-edge overlay when roudix.gaming.enable is on.
      nixpkgs.overlays = [ inputs.nix-gaming-edge.overlays.mesa-git ];
      drivers.mesa-git.enable = true;
    })
  ];
}

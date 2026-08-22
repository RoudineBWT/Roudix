{ inputs, pkgs, lib, config, ... }:

{
  imports = [
    inputs.umbriel.homeModules.default
    ./settings.nix
    ./keybinds.nix
    ./autostart.nix
    ./rules.nix
    ../../modules/home/mangohud.nix
    ../../modules/home/papirus-icon.nix
    ../../modules/home/tela-icon.nix
  ];

  programs.umbriel = {
    enable = true;
  };

  # Activation de Noctalia
  programs.noctalia = {
    enable = true;
    package = inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default;
  };
}

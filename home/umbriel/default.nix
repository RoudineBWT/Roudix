{ inputs, ... }:

{
  imports = [
    inputs.umbriel.homeModules.default
    ./settings.nix
    ./keybinds.nix
    ./autostart.nix
    ./rules.nix
  ];

  programs.umbriel.enable = true;
}

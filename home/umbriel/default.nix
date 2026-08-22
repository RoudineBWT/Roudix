{ inputs, ... }:

{
  imports = [
    inputs.umbriel.homeModules.default
    ./settings.nix
    ./keybinds.nix
    ./autostart.nix
  ];

  programs.umbriel.enable = true;
}

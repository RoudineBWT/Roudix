{ pkgs, osConfig, ... }:
let
  terminalType = osConfig.roudix.terminal or "ghostty";

  terminalPackage = {
    ghostty   = pkgs.ghostty;
    kitty     = pkgs.kitty;
    alacritty = pkgs.alacritty;
    foot      = pkgs.foot;
    wezterm   = pkgs.wezterm;
    ptyxis    = pkgs.ptyxis;
    konsole   = pkgs.kdePackages.konsole;
  }.${terminalType};
in
{
  # Terminal choisi par l'utilisateur (roudix.terminal) — pas de choix
  # "none", il y en a toujours un. Option déclarée dans
  # modules/system/apps/utilities/terminal.nix
  home.packages = [ terminalPackage ];
}

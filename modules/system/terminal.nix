{ lib, ... }:
with lib;
{
  options.roudix.terminal = mkOption {
    type = types.enum [ "ghostty" "kitty" "alacritty" "foot" "wezterm" ];
    default = "ghostty";
    description = "Terminal émulateur par défaut installé et configuré comme terminal principal.";
  };
}

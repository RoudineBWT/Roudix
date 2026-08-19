{ lib, config, ... }:
with lib;
{
  options.roudix.terminal = mkOption {
    type = types.enum [ "ghostty" "kitty" "alacritty" "foot" "wezterm" "ptyxis" "konsole" ];
    default = "ghostty";
    description = "Terminal émulateur par défaut installé et configuré comme terminal principal.";
  };

  config = {
    # "Ouvrir un terminal ici" dans Nautilus lance roudix.terminal au lieu
    # de gnome-terminal. Toutes les valeurs de l'enum ci-dessus sont
    # supportées par l'extension (ghostty, kitty, alacritty, foot,
    # wezterm, ptyxis, konsole).
    # Ignoré sur KDE : Dolphin n'utilise pas Nautilus/cette extension.
    programs.nautilus-open-any-terminal = mkIf (config.roudix.desktop.type != "kde") {
      enable   = true;
      terminal = config.roudix.terminal;
    };
  };
}

{ config, lib, pkgs, roudixWelcome, ... }:

with lib;

let
  cfg = config.roudix.welcome;
in
{
  options.roudix.welcome.enable = mkOption {
    type = types.bool;
    default = true;
    description = ''
      Installe roudix-welcome et le lance automatiquement au démarrage de
      la session graphique. L'utilisateur peut désactiver l'autostart lui-
      même via l'interrupteur "Afficher au démarrage" dans l'app — ce
      switch écrit un simple fichier marqueur (~/.local/state/roudix-welcome/disabled)
      lu par le ConditionPathExists du service ci-dessous, sans jamais
      toucher à l'enable/disable systemd géré par Home Manager. Ainsi le
      choix de l'utilisateur survit aux rebuilds (nh os switch/boot).
    '';
  };

  config = mkIf cfg.enable {
    home.packages = [ roudixWelcome ];

    systemd.user.services.roudix-welcome = {
      Unit = {
        Description = "Roudix Welcome — écran de bienvenue au démarrage de session";
        After = [ "graphical-session.target" ];
        PartOf = [ "graphical-session.target" ];
        # Bascule utilisateur, pas géré par systemctl enable/disable : voir
        # la description de l'option ci-dessus.
        ConditionPathExists = "!%h/.local/state/roudix-welcome/disabled";
      };

      Service = {
        Type = "simple";
        ExecStart = "${roudixWelcome}/bin/roudix-welcome";
      };

      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}

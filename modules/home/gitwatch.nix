{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.roudix.gitwatch;
in
{
  options.roudix.gitwatch = {
    enable = mkEnableOption "auto-commit/push automatique via gitwatch";

    repoPath = mkOption {
      type = types.str;
      default = "${config.home.homeDirectory}/Roudix";
      description = "Chemin du repo à surveiller";
    };

    branch = mkOption {
      type = types.str;
      default = "testing";
      description = "Branche cible pour le push automatique";
    };

    remote = mkOption {
      type = types.str;
      default = "origin";
      description = "Remote git à utiliser";
    };

    debounce = mkOption {
      type = types.int;
      default = 30;
      description = "Délai en secondes avant commit/push après la dernière modif";
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ pkgs.gitwatch ];

    systemd.user.services.roudix-gitwatch = {
      Unit = {
        Description = "Auto-commit/push automatique sur ${cfg.branch}";
        After = [ "network-online.target" "ssh-agent.service" ];
        Wants = [ "ssh-agent.service" ];
      };

      Service = {
        ExecStart = "${pkgs.gitwatch}/bin/gitwatch -r ${cfg.remote} -b ${cfg.branch} -s ${toString cfg.debounce} ${cfg.repoPath}";
        Restart = "on-failure";
        RestartSec = 5;
      };

      Install.WantedBy = [ "default.target" ];
    };
  };
}

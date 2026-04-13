{ config, lib, pkgs, ... }:

let
  isHyprland = config.roudix.desktop.type == "hyprland";
in

lib.mkIf isHyprland {

  services.displayManager.ly = {
    enable = true;

    settings = {
      # Pointe vers le répertoire système où uwsm installe hyprland-uwsm.desktop
      # (programs.uwsm génère /run/current-system/sw/share/wayland-sessions/hyprland-uwsm.desktop)
      waylandsessions = "/run/current-system/sw/share/wayland-sessions";

      # Désactiver les sessions X11 / TTY inutiles
      xinitrcpath  = "";
      xsessions    = "";

      # Optionnel : cacher l'animation de fond pour un look épuré
      animate      = false;
    };
  };

  # S'assurer que le .desktop UWSM est bien présent dans le bon répertoire
  # (normalement géré par programs.uwsm, mais on le rend explicite)
  environment.sessionVariables = {
    XDG_SESSION_TYPE = "wayland";
  };
}

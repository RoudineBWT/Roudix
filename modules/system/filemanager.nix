{ lib, pkgs, config, ... }:
with lib;
let
  # `command` = binaire réellement lancé (utilisé par le bind niri MOD+E).
  # Les noms d'attributs ci-dessous matchent déjà les vrais binaires.
  fileManagerDefs = {
    "nautilus"   = { package = pkgs.nautilus;             command = "nautilus";   extras = [ pkgs.gvfs ]; };
    "dolphin"    = { package = pkgs.kdePackages.dolphin;   command = "dolphin";    extras = []; };
    "nemo"       = { package = pkgs.nemo;                  command = "nemo";       extras = [ pkgs.gvfs ]; };
    "thunar"     = { package = pkgs.thunar;           command = "thunar";     extras = [ pkgs.gvfs pkgs.thunar-volman ]; };
    "pcmanfm-qt" = { package = pkgs.libsForQt5.pcmanfm-qt; command = "pcmanfm-qt"; extras = []; };
  };
in
{
  options.roudix.fileManager = mkOption {
    type = types.enum (attrNames fileManagerDefs);
    default = "nautilus";
    description = ''
      Gestionnaire de fichiers par défaut : installé, et lié au bind niri
      MOD+E ainsi qu'à l'intégration "ouvrir un terminal ici" (nautilus
      uniquement, via nautilus-open-any-terminal).
    '';
  };

  config = mkIf (elem config.roudix.desktop.type [ "niri" "hyprland" "mangowc" ]) {
    environment.systemPackages =
      [ fileManagerDefs.${config.roudix.fileManager}.package ]
      ++ fileManagerDefs.${config.roudix.fileManager}.extras;

    # Nautilus a besoin de son extension pour respecter roudix.terminal.
    # Les autres file managers ont leur propre mécanisme natif (ou aucun
    # équivalent packagé actuellement).
    programs.nautilus-open-any-terminal =
      mkIf (config.roudix.fileManager == "nautilus") {
        enable   = true;
        terminal = config.roudix.terminal;
      };
  };
}

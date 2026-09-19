{ lib, pkgs, config, ... }:
with lib;
let
  # `command` = the binary actually launched (used by the niri MOD+E bind).
  # The attribute names below already match the real binaries.
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
      Default file manager: installed, and wired to the niri MOD+E bind
      as well as the "open a terminal here" integration (nautilus only,
      via nautilus-open-any-terminal).
    '';
  };

  config = mkIf (elem config.roudix.desktop.type [ "niri" "hyprland" "mangowc" "umbriel" ]) {
    environment.systemPackages =
      [ fileManagerDefs.${config.roudix.fileManager}.package ]
      ++ fileManagerDefs.${config.roudix.fileManager}.extras;

    # Nautilus needs its extension to respect roudix.terminal. Other
    # file managers have their own native mechanism (or no packaged
    # equivalent currently).
    programs.nautilus-open-any-terminal =
      mkIf (config.roudix.fileManager == "nautilus") {
        enable   = true;
        terminal = config.roudix.terminal;
      };
  };
}

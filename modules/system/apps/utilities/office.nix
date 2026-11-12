{ config, lib, pkgs, ... }:
let
  cfg = config.roudix;

  # language -> spell-check + hyphenation dictionaries (hunspell / hyphen)
  dictionaries = with pkgs; {
    en = [ hunspellDicts.en_US-large hunspellDicts.en_GB-large hyphenDicts.en_US hyphenDicts.en_GB ];
    fr = [ hunspellDicts.fr-moderne hyphenDicts.fr_FR ];
    es = [ hunspellDicts.es_ES hyphenDicts.es_ES ];
    de = [ hunspellDicts.de_DE hyphenDicts.de_DE ];
    it = [ hunspellDicts.it_IT hyphenDicts.it_IT ];
    pt = [ hunspellDicts.pt_PT hunspellDicts.pt_BR hyphenDicts.pt_PT hyphenDicts.pt_BR ];
  };
in
{
  # Read on the home-manager side (modules/home/apps/utilities/office.nix) via
  # osConfig — same pattern as roudix.passwordManager / roudix.torrentClient.
  options.roudix.office = lib.mkOption {
    type = lib.types.enum [ "none" "libreoffice" ];
    default = "none";
    description = ''
      "none"        : No office suite installed.
      "libreoffice" : LibreOffice (`pkgs.libreoffice`) — Writer, Calc, Impress.
    '';
  };

  options.roudix.officeDictionaries = lib.mkOption {
    type = lib.types.listOf (lib.types.enum (builtins.attrNames dictionaries));
    default = [ ];
    example = [ "fr" "en" ];
    description = ''
      Spell-check and hyphenation dictionaries for LibreOffice (and any
      hunspell-aware app), installed system-wide and exposed through DICPATH.
      Without them LibreOffice has no dictionary on NixOS.
      Available: ${lib.concatStringsSep ", " (builtins.attrNames dictionaries)}.
    '';
  };

  config = lib.mkIf (cfg.officeDictionaries != [ ]) {
    environment.pathsToLink = [ "/share/hunspell" "/share/myspell" "/share/hyphen" ];
    environment.variables.DICPATH =
      "/run/current-system/sw/share/hunspell:/run/current-system/sw/share/hyphen";
    environment.systemPackages =
      [ pkgs.hunspell pkgs.hyphen ]
      ++ lib.concatMap (l: dictionaries.${l}) (lib.unique cfg.officeDictionaries);
  };
}

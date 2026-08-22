{ config, lib, pkgs, inputs, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";

  resolveUmbrielDotfiles = shell:
    let
      candidates = {
        noctalia  = "${dotfiles}/umbriel";
      };
      desired  = candidates.${shell} or candidates.noctalia;
      fallback = candidates.noctalia;
    in
{
  imports = [ inputs.umbriel.homeModules.default ];

  programs.umbriel = {
    enable = true;
    validateConfig = true;   # umbriel valide le TOML au build (via `umbriel validate`)


    xdg.configFile."umbriel" = {
      source    = umbrielDir;
      recursive = true;
    };

    # Le fichier ci-contre (config.toml) est la traduction de tes 9 fichiers
    # niri .kdl. Il est chargé tel quel — remplace LEGION-OUTPUT/HKC-OUTPUT
    # dedans par les vrais noms de connecteur avant le premier build
    # (`umbriel outputs` une fois en session pour les récupérer).
    #settings = ./config.toml;
  };
}

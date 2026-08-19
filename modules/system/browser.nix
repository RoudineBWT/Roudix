{ config, lib, pkgs, inputs, brave-previews, ... }:

let
  cfg = config.roudix;

  # `command` = binaire réellement lancé (utilisé par les keybinds niri).
  # Ajuste-le ici si un de tes paquets custom (brave-origin-*) expose un
  # binaire différent du nom de l'attribut.
  browserDefs = {
    "brave"    = { package = pkgs.brave;                                     command = "brave";                 extras = []; };
    "brave-beta"    = { package = pkgs.brave-beta;                           command = "brave-beta";            extras = []; };
    "brave-nightly" = { package = pkgs.brave-nightly;                        command = "brave-nightly";         extras = []; };
    "brave-origin" = { package = pkgs.brave-origin;                command = "brave-origin";                    extras = []; };
    "brave-origin-beta" = { package = pkgs.brave-origin-beta;                command = "brave-origin-beta";     extras = []; };
    "brave-origin-nightly" = { package = pkgs.brave-origin-nightly;          command = "brave-origin-nightly";  extras = []; };
    "helium"   = { package = inputs.helium.packages.${pkgs.system}.helium-appimage;  command = "helium";        extras = []; };
    "vivaldi"  = { package = pkgs.vivaldi;                                   command = "vivaldi";               extras = [ pkgs.vivaldi-ffmpeg-codecs ]; };
    "chromium" = { package = pkgs.chromium;                                  command = "chromium";              extras = []; };
    "firefox"  = { package = pkgs.firefox;                                   command = "firefox";               extras = []; };
    "librewolf"= { package = pkgs.librewolf;                                 command = "librewolf";             extras = []; };
    "google-chrome"       = { package = pkgs.google-chrome;                  command = "google-chrome-stable";  extras = []; };
    "microsoft-edge"      = { package = pkgs.microsoft-edge;                 command = "microsoft-edge";        extras = []; };
    "ungoogled-chromium"  = { package = pkgs.ungoogled-chromium;             command = "chromium";              extras = []; };
  };

  # Collect packages for all selected browsers
  selectedBrowserPkgs = lib.concatMap
    (name:
      let b = browserDefs.${name}; in
      lib.optional (b.package != null) b.package ++ b.extras
    )
    cfg.browsers;

in {
  options.roudix = {

    browsers = lib.mkOption {
      type    = lib.types.listOf (lib.types.enum (lib.attrNames browserDefs));
      default = [ "brave" ];
      description = ''
        List of browsers to install.
        Example: [ "brave" "vivaldi" ]
        Use [] to skip all.
      '';
    };

    zen = {
      enable = lib.mkOption {
        type    = lib.types.bool;
        default = false;
        description = "Install Zen Browser (from zen-browser flake input).";
      };

      mods = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [];
        description = ''
          Mod IDs to install from the native Zen theme store
          (https://zen-browser.app/mods). Ignored if `zen.sine.enable = true`.
        '';
      };

      sine = {
        enable = lib.mkOption {
          type    = lib.types.bool;
          default = false;
          description = ''
            Enable the Sine mod loader (bootloader injected at build time,
            no read-only store conflict). Disables the native `zen.mods`
            option on this profile — upstream limitation, the two mod
            systems don't coexist on the same profile.
          '';
        };

        mods = lib.mkOption {
          type = lib.types.listOf lib.types.str;
          default = [];
          description = ''
            Mod IDs to install via the Sine store (falls back to the
            Zen theme store automatically if not found on Sine).
            Use this for mods only available on Sine.
          '';
        };
      };
    };

    browser = {
      default = lib.mkOption {
        type = lib.types.nullOr (lib.types.enum (lib.attrNames browserDefs));
        default = if cfg.browsers != [ ] then lib.head cfg.browsers else null;
        description = ''
          Navigateur lié au raccourci niri MOD+B. Défaut : le premier
          élément de `roudix.browsers`. Mets `null` (ou une liste vide de
          `browsers`) pour désactiver le bind niri.
        '';
      };

      command = lib.mkOption {
        type     = lib.types.nullOr lib.types.str;
        readOnly = true;
        default  = if cfg.browser.default != null
                   then browserDefs.${cfg.browser.default}.command
                   else null;
        description = ''
          Binaire résolu à partir de `roudix.browser.default`.
          Lecture seule, consommée par le module niri pour générer le bind.
        '';
      };

      commands = lib.mkOption {
        type     = lib.types.listOf (lib.types.attrsOf lib.types.str);
        readOnly = true;
        default  = map (n: { name = n; command = browserDefs.${n}.command; }) cfg.browsers;
        description = ''
          Liste ordonnée `{ name; command; }` pour chaque navigateur de
          `roudix.browsers`. Le module niri s'en sert pour générer un bind
          par navigateur (le premier correspond à `roudix.browser.default`).
        '';
      };
    };

  };

  config = {
    environment.systemPackages = selectedBrowserPkgs;

    assertions = [
      {
        assertion = !(cfg.zen.sine.enable && cfg.zen.mods != []);
        message = ''
          roudix.zen: `mods` (Zen store) and `sine.enable` can't be used
          together on the same profile. Use `zen.sine.mods` instead when
          `sine.enable = true` (it falls back to the Zen theme store).
        '';
      }
    ];
  };
}

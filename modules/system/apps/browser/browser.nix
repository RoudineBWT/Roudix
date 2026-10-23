{ config, lib, pkgs, inputs, brave-previews, ... }:

let
  cfg = config.roudix;

  # `command` = the binary actually launched (used by the niri keybinds).
  # Adjust it here if a custom package (brave-origin-*) exposes a binary
  # under a different name than the attribute.
  browserDefs = {
    "brave"    = { package = pkgs.brave;                                     command = "brave";                 extras = []; };
    "brave-beta"    = { package = pkgs.brave-beta;                           command = "brave-beta";            extras = []; };
    "brave-nightly" = { package = pkgs.brave-nightly;                        command = "brave-nightly";         extras = []; };
    "brave-origin" = { package = pkgs.brave-origin;                command = "brave-origin";                    extras = []; };
    "brave-origin-beta" = { package = pkgs.brave-origin-beta;                command = "brave-origin-beta";     extras = []; };
    "brave-origin-nightly" = { package = pkgs.brave-origin-nightly;          command = "brave-origin-nightly";  extras = []; };
    "helium"   = { package = inputs.helium.packages.${pkgs.stdenv.hostPlatform.system}.helium-appimage;  command = "helium";        extras = []; };
    "vivaldi"  = { package = pkgs.vivaldi;                                   command = "vivaldi";               extras = [ pkgs.vivaldi-ffmpeg-codecs ]; };
    "chromium" = { package = pkgs.chromium;                                  command = "chromium";              extras = []; };
    "firefox"  = { package = pkgs.firefox;                                   command = "firefox";               extras = []; };
    "librewolf"= { package = pkgs.librewolf;                                 command = "librewolf";             extras = []; };
    "google-chrome"       = { package = pkgs.google-chrome;                  command = "google-chrome";  extras = []; };
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

      variant = lib.mkOption {
        type = lib.types.enum [ "beta" "twilight" ];
        default = "twilight";
        description = ''
          Zen release channel to install (drives which
          `inputs.zen-browser.homeModules.<variant>` gets imported in
          `modules/home/apps/browser/browser.nix`):
            "beta"     — Zen's regular (Firefox-based) release channel,
                         slower-moving, most stable
            "twilight" — nightly builds of Zen Beta, mirrored by the
                         flake maintainer
        '';
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

    zen.tweaks = {
      enable = lib.mkOption {
        type    = lib.types.bool;
        default = false;
        description = ''
          Apply Roudix's Zen Browser tweaks: a set of prefs written to the
          profile's user.js (programs.zen-browser.profiles.default.settings)
          AND a policies.json (programs.zen-browser.policies, built from
          modules/home/apps/browser/zen-policies.json). Only used when
          `roudix.zen.enable = true`.

          Prefs live in modules/home/apps/browser/zen-prefs.nix. Prefs that
          were `locked` in the original snippet are additionally enforced
          through the `Preferences` policy (user.js alone can't lock a pref).
          Anything can still be overridden from modules/home/local.nix with
          `programs.zen-browser.profiles.default.settings.<pref> = …;`
          (our values are set with lib.mkDefault).
        '';
      };

      performance = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = ''
          Hardware video decoding, WebRender / GPU process, JIT thresholds,
          bigger memory caches (media cache up to 1 GB / 3 GB combined),
          disk cache off, network connection tuning.
        '';
      };

      privacy = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = ''
          Removes Mozilla extras (sponsored tiles, Pocket, VPN promo, ML /
          AI chat, Normandy, UITour…), telemetry, and applies hardening
          (strict tracking protection, HTTPS-only, no prefetch/predictor,
          query-string stripping, no form autofill, CRLite).
          Note: `browser.newtabpage.enabled = false` is part of this.
        '';
      };

      disableSafeBrowsing = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = ''
          Turns Google Safe Browsing (malware / phishing / downloads
          checks) off and blanks its provider URLs. This removes a
          protection layer — the uBlock Origin lists in the policies
          (urlhaus, curben-phishing, ublock-badware) partly make up for it.
          Set to false to keep Safe Browsing.
        '';
      };

      ui = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = "Physics-based smooth scrolling, faster mouse wheel, CSS masonry.";
      };

      policies = lib.mkOption {
        type    = lib.types.bool;
        default = true;
        description = ''
          Also install the policies.json (tracking protection, DoH,
          uBlock Origin + filter lists, no Pocket/studies/feedback, locked
          Firefox Home & messaging…) plus the `Preferences` policy for
          locked prefs. false = user.js only.
        '';
      };

      profile = lib.mkOption {
        type    = lib.types.nullOr lib.types.str;
        default = null;
        example = ".zen/abcd1234.Default (release)";
        description = ''
          Zen profile that receives the tweaks' user.js, as a path relative to
          the home directory (Zen keeps its profiles in ~/.zen or ~/.config/zen,
          see the profiles.ini there). null (default) = the profile Roudix
          manages itself (`programs.zen-browser.profiles.default`).
          Set from roudix-switcher, which lists the profiles it finds.
          The policies.json is not per profile: it covers the whole install.
        '';
      };
    };

    # ── Firefox tweaks ───────────────────────────────────────────────────
    # Same categories as zen.tweaks, written as a user.js in ONE existing
    # Firefox profile (~/.mozilla/firefox or ~/.config/mozilla/firefox).
    firefox.tweaks = {
      enable = lib.mkOption {
        type    = lib.types.bool;
        default = false;
        description = ''
          Apply Roudix's tweaks (the same prefs as `roudix.zen.tweaks`, minus
          the Zen-only ones) to the Firefox profile in `profile`. Nothing is
          written while `profile` is null. No policies.json: Firefox's is
          install-wide, not per profile.
        '';
      };

      profile = lib.mkOption {
        type    = lib.types.nullOr lib.types.str;
        default = null;
        example = ".mozilla/firefox/abcd1234.default-release";
        description = ''
          Firefox profile that receives the user.js, as a path relative to the
          home directory (see the profiles.ini in ~/.mozilla/firefox or
          ~/.config/mozilla/firefox). Set from roudix-switcher.
        '';
      };

      performance         = lib.mkOption { type = lib.types.bool; default = true; description = "Same as `roudix.zen.tweaks.performance`."; };
      privacy             = lib.mkOption { type = lib.types.bool; default = true; description = "Same as `roudix.zen.tweaks.privacy`."; };
      disableSafeBrowsing = lib.mkOption { type = lib.types.bool; default = true; description = "Same as `roudix.zen.tweaks.disableSafeBrowsing` (removes a protection layer)."; };
      ui                  = lib.mkOption { type = lib.types.bool; default = true; description = "Same as `roudix.zen.tweaks.ui` (smooth scrolling, masonry)."; };
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

# roudix.store.packages — list of nixpkgs attribute names installed for the
# user (home.packages). Written by roudix-store into a managed block of
# modules/home/local.nix; you can also edit it by hand. Your own
# `home.packages = [...]` in local.nix keeps working next to it.
#
# roudix.store.flakePackages — "<flake>#<attr>" references (e.g. "roudix-caches#faugus"), taken
# from the flake inputs' packages.<system>.<attr> and installed for the user. The list of
# flakes the store offers is roudix.store.flakeSources (modules/system/packaging/store.nix).
#
# roudix.store.flatpaksUser / flatpaksUserBeta — Flatpak app ids installed in the
# *user* installation (~/.local/share/flatpak) from flathub / flathub-beta, through
# nix-flatpak's Home Manager module (imported in flake.nix). The system-wide
# lists (roudix.store.flatpaks / flatpaksBeta) are in modules/system/packaging/store.nix.
{ config, lib, pkgs, inputs, osConfig ? null, ... }:
let
  cfg = config.roudix.store;
  resolve = name:
    let r = builtins.tryEval (lib.attrByPath (lib.splitString "." name) null pkgs);
    in if r.success && r.value != null
       then r.value
       else lib.warn "roudix-store: '${name}' not found in nixpkgs, skipped" null;
  system = pkgs.stdenv.hostPlatform.system;
  resolveFlake = ref:
    let
      parts = lib.splitString "#" ref;
      r = builtins.tryEval (lib.attrByPath [ (lib.elemAt parts 0) "packages" system (lib.elemAt parts 1) ] null inputs);
    in if lib.length parts == 2 && r.success && r.value != null
       then r.value
       else lib.warn "roudix-store: '${ref}' not found in the flake inputs, skipped" null;
  userFlatpaks = cfg.flatpaksUser != [ ] || cfg.flatpaksUserBeta != [ ];
  systemFlatpakOn = lib.attrByPath [ "roudix" "flatpak" "enable" ] true osConfig;
in
{
  options.roudix.store = {
    packages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "vlc" "telegram-desktop" ];
      description = "nixpkgs attribute names installed for the user (managed by roudix-store).";
    };
    flakePackages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "roudix-caches#faugus" ];
      description = "\"<flake>#<attr>\" references from the flake inputs installed for the user (managed by roudix-store).";
    };
    flatpaksUser = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "org.mozilla.firefox" ];
      description = "Flathub application ids installed in the user Flatpak installation (managed by roudix-store).";
    };
    flatpaksUserBeta = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "org.mozilla.firefox" ];
      description = "flathub-beta application ids installed in the user Flatpak installation (managed by roudix-store).";
    };
  };

  config = lib.mkMerge [
    {
      home.packages =
        lib.filter (p: p != null) (map resolve cfg.packages)
        ++ lib.filter (p: p != null) (map resolveFlake cfg.flakePackages);
    }

    (lib.mkIf userFlatpaks {
      services.flatpak = {
        enable = true;
        # a user installation has its own remotes, separate from the system ones
        remotes = lib.mkDefault [
          { name = "flathub"; location = "https://dl.flathub.org/repo/flathub.flatpakrepo"; }
          { name = "flathub-beta"; location = "https://flathub.org/beta-repo/flathub-beta.flatpakrepo"; }
        ];
        packages =
          map (id: { appId = id; origin = "flathub"; }) cfg.flatpaksUser
          ++ map (id: { appId = id; origin = "flathub-beta"; }) cfg.flatpaksUserBeta;
      };
    })

    (lib.mkIf (userFlatpaks && !systemFlatpakOn) {
      warnings = [ "roudix-store: roudix.store.flatpaksUser / flatpaksUserBeta is set but roudix.flatpak.enable is false (system Flatpak is needed for user installs too)." ];
    })
  ];
}

# Written by roudix-store into a managed block of hosts/<host>/local.nix
# (already gitignored); you can also edit these lists by hand.
#
#   roudix.store.systemPackages : nixpkgs attribute names installed system-wide
#                                 (e.g. "htop", "kdePackages.kate")
#   roudix.store.flatpaks       : Flathub app ids handed to nix-flatpak, system-wide
#                                 (e.g. "org.mozilla.firefox"); needs roudix.flatpak.enable
#   roudix.store.flatpaksBeta   : same, from the flathub-beta remote
#   roudix.store.systemFlakePackages : "<flake>#<attr>" references installed system-wide, taken
#                                 from the flake inputs' `packages.<system>.<attr>`
#                                 (e.g. "roudix-caches#faugus", "brave-previews#brave-nightly")
#   roudix.store.flakeSources   : which flake inputs the store offers, and how (see below). The
#                                 resulting catalog is written to /etc/roudix-store/flake-catalog.json,
#                                 which roudix-store reads: it never has to evaluate a flake itself.
#
# The per-user Flatpak lists (roudix.store.flatpaksUser / flatpaksUserBeta) live in
# modules/home/apps/store.nix (nix-flatpak's Home Manager module).
#
# A nixpkgs name that no longer exists in the locked nixpkgs is skipped with a
# warning instead of breaking the whole rebuild.
{ config, lib, pkgs, inputs, ... }:
let
  cfg = config.roudix.store;
  system = pkgs.stdenv.hostPlatform.system;
  resolve = name:
    let r = builtins.tryEval (lib.attrByPath (lib.splitString "." name) null pkgs);
    in if r.success && r.value != null
       then r.value
       else lib.warn "roudix-store: '${name}' not found in nixpkgs, skipped" null;

  # "<flake>#<attr>" -> inputs.<flake>.packages.<system>.<attr>
  resolveFlake = ref:
    let
      parts = lib.splitString "#" ref;
      r = builtins.tryEval (lib.attrByPath [ (lib.elemAt parts 0) "packages" system (lib.elemAt parts 1) ] null inputs);
    in if lib.length parts == 2 && r.success && r.value != null
       then r.value
       else lib.warn "roudix-store: '${ref}' not found in the flake inputs, skipped" null;

  # ── catalog of the flake packages offered by the store ────────────────
  flakeSet = flake: lib.attrByPath [ flake "packages" system ] { } inputs;
  isPkg = p: let r = builtins.tryEval (lib.isDerivation p); in r.success && r.value;
  offeredAttrs = flake: spec:
    lib.filter
      (attr:
        isPkg (flakeSet flake).${attr}
        && !(lib.elem attr spec.exclude)
        && (spec.only == [ ] || lib.elem attr spec.only)
        && (attr != "default" || spec.names ? default))
      (lib.attrNames (flakeSet flake));
  entryFor = flake: spec: attr:
    let
      p = (flakeSet flake).${attr};
      value = {
        inherit attr;
        pname = lib.getName p;
        version = p.version or "";
        description = p.meta.description or "";
        homepage = let h = p.meta.homepage or ""; in if builtins.isList h then (if h == [ ] then "" else builtins.head h) else h;
        mainProgram = p.meta.mainProgram or "";
        # store path, to tell "installed" from "same name in nixpkgs"; context dropped so the
        # catalog never makes the system build depend on these packages
        out = builtins.unsafeDiscardStringContext p.outPath;
        alias = spec.aliases.${attr} or "";
        name = spec.names.${attr} or "";
      };
      r = builtins.tryEval (builtins.deepSeq value value);  # a broken package never breaks the rebuild
    in if r.success then r.value else null;
  flakeCatalog = {
    version = 1;
    inherit system;
    flakes = lib.mapAttrs
      (flake: spec: {
        label = if spec.label != "" then spec.label else flake;
        packages = lib.filter (e: e != null) (map (entryFor flake spec) (offeredAttrs flake spec));
      })
      cfg.flakeSources;
  };
in
{
  options.roudix.store = {
    systemPackages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "htop" "kdePackages.kate" ];
      description = "nixpkgs attribute names installed system-wide (managed by roudix-store).";
    };
    systemFlakePackages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "roudix-caches#faugus" ];
      description = "\"<flake>#<attr>\" references from the flake inputs installed system-wide (managed by roudix-store).";
    };
    flakeSources = lib.mkOption {
      description = ''
        Flake inputs whose `packages.<system>` the store offers next to nixpkgs. An app that also
        exists in nixpkgs (same attribute, or listed in `aliases`) is not duplicated: it gets one
        more entry in its Source chooser.
      '';
      default = { };
      type = lib.types.attrsOf (lib.types.submodule {
        options = {
          label = lib.mkOption { type = lib.types.str; default = ""; description = "Name shown in the Source chooser (defaults to the input name)."; };
          only = lib.mkOption { type = lib.types.listOf lib.types.str; default = [ ]; description = "Offer only these attributes (empty = every derivation)."; };
          exclude = lib.mkOption { type = lib.types.listOf lib.types.str; default = [ ]; description = "Attributes never offered (libraries, tools, internals)."; };
          aliases = lib.mkOption { type = lib.types.attrsOf lib.types.str; default = { }; description = "flake attribute -> nixpkgs attribute it is a variant of."; };
          names = lib.mkOption { type = lib.types.attrsOf lib.types.str; default = { }; description = "flake attribute -> display name (needed to offer `default`)."; };
        };
      });
    };
    flatpaks = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "org.mozilla.firefox" ];
      description = "Flathub application ids installed system-wide through nix-flatpak (managed by roudix-store).";
    };
    flatpaksBeta = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "org.mozilla.firefox" ];
      description = "flathub-beta application ids installed system-wide through nix-flatpak (managed by roudix-store).";
    };
  };

  config = lib.mkMerge [
    {
      environment.systemPackages =
        lib.filter (p: p != null) (map resolve cfg.systemPackages)
        ++ lib.filter (p: p != null) (map resolveFlake cfg.systemFlakePackages);

      # the flakes Roudix proposes in the store (add yours with roudix.store.flakeSources.<input>)
      # field by field at default priority: overriding `exclude` of one flake keeps its label and aliases
      roudix.store.flakeSources = lib.mapAttrs (_: spec: lib.mapAttrs (_: lib.mkDefault) spec) {
        roudix-caches = {
          label = "Roudix-caches";
          exclude = [ "scxctl" "prismlauncher-wrapped-custom" ];  # scxctl backs roudix-scheduler; the wrapper backs the custom launcher
          aliases = { heroic-custom = "heroic"; prismlauncher-custom = "prismlauncher"; faugus = "faugus-launcher"; };
        };
        brave-previews = {
          label = "Brave Previews";
          aliases = { brave-stable = "brave"; };
        };
        zen-browser = {
          label = "Zen Browser";
          only = [ "beta" "twilight" "twilight-official" ];
          names = { beta = "Zen Browser (beta)"; twilight = "Zen Browser (twilight)"; twilight-official = "Zen Browser (twilight official)"; };
        };
        helium = {
          label = "Helium";
          names = { helium-tarball = "Helium"; helium-appimage = "Helium (AppImage)"; };
        };
        betterbird-nix = { label = "Betterbird"; };
        millennium = { label = "Millennium"; };
        nix-gaming-edge = {
          label = "nix-gaming-edge";
          # toolchain pieces, not apps (and the heaviest to evaluate); `hytale` is hytale-launcher again
          exclude = [ "mesa-git" "mesa32-git" "libdrm-git" "libdrm32-git" "wayland-protocols-git" "proton-cachyos" "protonv3" "hytale" ];
        };
        sonora = { label = "Sonora"; names = { default = "Sonora"; }; };
      };

      environment.etc."roudix-store/flake-catalog.json".text = builtins.toJSON flakeCatalog;
    }

    (lib.mkIf config.roudix.flatpak.enable {
      services.flatpak.packages =
        map (id: { appId = id; origin = "flathub"; }) cfg.flatpaks
        ++ map (id: { appId = id; origin = "flathub-beta"; }) cfg.flatpaksBeta;
    })

    (lib.mkIf ((cfg.flatpaks != [ ] || cfg.flatpaksBeta != [ ]) && !config.roudix.flatpak.enable) {
      warnings = [ "roudix-store: roudix.store.flatpaks / flatpaksBeta is set but roudix.flatpak.enable is false, so no Flatpak will be installed." ];
    })
  ];
}

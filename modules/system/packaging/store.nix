# Written by roudix-store into a managed block of hosts/<host>/local.nix
# (already gitignored); you can also edit these lists by hand.
#
#   roudix.store.systemPackages : nixpkgs attribute names installed system-wide
#                                 (e.g. "htop", "kdePackages.kate")
#   roudix.store.flatpaks       : Flathub app ids handed to nix-flatpak
#                                 (e.g. "org.mozilla.firefox"); needs roudix.flatpak.enable
#
# A nixpkgs name that no longer exists in the locked nixpkgs is skipped with a
# warning instead of breaking the whole rebuild.
{ config, lib, pkgs, ... }:
let
  cfg = config.roudix.store;
  resolve = name:
    let r = builtins.tryEval (lib.attrByPath (lib.splitString "." name) null pkgs);
    in if r.success && r.value != null
       then r.value
       else lib.warn "roudix-store: '${name}' not found in nixpkgs, skipped" null;
in
{
  options.roudix.store = {
    systemPackages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "htop" "kdePackages.kate" ];
      description = "nixpkgs attribute names installed system-wide (managed by roudix-store).";
    };
    flatpaks = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "org.mozilla.firefox" ];
      description = "Flathub application ids installed through nix-flatpak (managed by roudix-store).";
    };
  };

  config = lib.mkMerge [
    { environment.systemPackages = lib.filter (p: p != null) (map resolve cfg.systemPackages); }

    (lib.mkIf config.roudix.flatpak.enable {
      services.flatpak.packages = map (id: { appId = id; origin = "flathub"; }) cfg.flatpaks;
    })

    (lib.mkIf (cfg.flatpaks != [ ] && !config.roudix.flatpak.enable) {
      warnings = [ "roudix-store: roudix.store.flatpaks is set but roudix.flatpak.enable is false, so no Flatpak will be installed." ];
    })
  ];
}

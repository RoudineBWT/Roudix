# roudix.store.systemPackages — list of nixpkgs attribute names (e.g. "htop",
# "kdePackages.kate") installed system-wide. Written by roudix-store into a
# managed block of hosts/<host>/local.nix; you can also edit it by hand.
#
# A name that no longer exists in the locked nixpkgs is skipped with a
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
  options.roudix.store.systemPackages = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
    example = [ "htop" "kdePackages.kate" ];
    description = "nixpkgs attribute names installed system-wide (managed by roudix-store).";
  };

  config.environment.systemPackages =
    lib.filter (p: p != null) (map resolve cfg.systemPackages);
}

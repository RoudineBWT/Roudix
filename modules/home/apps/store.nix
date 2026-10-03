# roudix.store.packages — list of nixpkgs attribute names installed for the
# user (home.packages). Written by roudix-store into a managed block of
# modules/home/local.nix; you can also edit it by hand. Your own
# `home.packages = [...]` in local.nix keeps working next to it.
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
  options.roudix.store.packages = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
    example = [ "vlc" "telegram-desktop" ];
    description = "nixpkgs attribute names installed for the user (managed by roudix-store).";
  };

  config.home.packages = lib.filter (p: p != null) (map resolve cfg.packages);
}

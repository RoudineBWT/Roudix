{ pkgs, osConfig, lib, ... }:
let
  passwordManagerType = osConfig.roudix.passwordManager or "none";

  passwordManagerPackage = {
    bitwarden  = pkgs.bitwarden-desktop;
    keepassxc  = pkgs.keepassxc;
    protonpass = pkgs.proton-pass;
    none       = null;
  }.${passwordManagerType};
in
{
  # Option declared in modules/system/apps/utilities/password-manager.nix
  home.packages = lib.optional (passwordManagerPackage != null) passwordManagerPackage;
}

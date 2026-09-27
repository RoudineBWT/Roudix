{ pkgs, inputs, osConfig, lib, ... }:
let
  mailClientType = osConfig.roudix.mailClient or "none";

  # Betterbird isn't in nixpkgs — same pattern as fluxerPackage
  # (common-apps.nix), pulled straight from its own flake input's
  # prebuilt package.
  betterbirdPackage = inputs.betterbird-nix.packages.${pkgs.stdenv.hostPlatform.system}.betterbird;

  mailClientPackage = {
    thunderbird = pkgs.thunderbird;
    betterbird  = betterbirdPackage;
    geary       = pkgs.geary;
    none        = null;
  }.${mailClientType};
in
{
  # Option declared in modules/system/apps/communication/mail-client.nix
  home.packages = lib.optional (mailClientPackage != null) mailClientPackage;
}

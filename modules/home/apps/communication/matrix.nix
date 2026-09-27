{ pkgs, osConfig, lib, ... }:
let
  matrixClient = osConfig.roudix.matrixClient or "element";

  matrixPackage = {
    element = pkgs.element-desktop.override {
      commandLineArgs = if osConfig.roudix.desktop.type == "kde"
        then "--password-store=kwallet6"
        else "--password-store=gnome-libsecret";
    };
    cinny  = pkgs.cinny-desktop;
    none   = null;
  }.${matrixClient};
in
{
  # Matrix client (optional) — option declared in
  # modules/system/apps/communication/matrix.nix
  home.packages = lib.optional (matrixPackage != null) matrixPackage;
}

{ pkgs, osConfig, lib, ... }:
let
  officeType = osConfig.roudix.office or "none";

  officePackage = {
    libreoffice = pkgs.libreoffice;
    none        = null;
  }.${officeType};
in
{
  # Option declared in modules/system/apps/utilities/office.nix
  home.packages = lib.optional (officePackage != null) officePackage;
}

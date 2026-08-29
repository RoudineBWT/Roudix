## _include-dms.nix — même mécanisme que _include-noctalia.nix, mais
## pour les 5 fichiers que DMS regénère lui-même en live sous
## ~/.config/niri/dms/ (alttab, wpblur, colors, cursor, layout).
{ config, pkgs, lib, ... }:
let
  niriPkg = config.programs.niri.package;
  withDms = config.programs.niri.finalConfig + ''

    include "dms/alttab.kdl"
    include "dms/wpblur.kdl"
    include "dms/colors.kdl"
    include "dms/cursor.kdl"
    include "dms/layout.kdl"
  '';
in
{
  xdg.configFile.niri-config = lib.mkForce {
    target = "niri/config.kdl";
    force = true;
    source = pkgs.runCommand "config.kdl" {
      config = withDms;
      passAsFile = [ "config" ];
      buildInputs = [ niriPkg ];
    } ''
      niri validate -c $configPath
      cp $configPath $out
    '';
  };
}

## _include-dms.nix — same mechanism as _include-noctalia.nix, but for the
## 5 files DMS regenerates live under ~/.config/niri/dms/ (alttab, wpblur,
## colors, cursor, layout).
{ config, pkgs, lib, ... }:
let
  niriPkg = config.programs.niri.package;
  baseConfig = config.programs.niri.finalConfigFile;
  extra = ''

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
      inherit extra;
      passAsFile = [ "extra" ];
      buildInputs = [ niriPkg ];
    } ''
      cat ${baseConfig} $extraPath > config.kdl
      niri validate -c config.kdl
      cp config.kdl $out
    '';
  };
}

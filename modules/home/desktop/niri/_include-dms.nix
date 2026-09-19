## _include-dms.nix — same mechanism as _include-noctalia.nix, but for the
## 5 files DMS regenerates live under ~/.config/niri/dms/ (alttab, wpblur,
## colors, cursor, layout).
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

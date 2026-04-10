{ pkgs, ... }:
{
  environment.systemPackages = [
    (pkgs.runCommand "roudix-logo" {} ''
      mkdir -p $out/share/icons/hicolor/scalable/apps
      cp ${./logo/roudix-logo.svg} $out/share/icons/hicolor/scalable/apps/roudix-logo.svg
    '')
  ];

  environment.pathsToLink = [ "/share/icons" ];

  system.activationScripts.roudix-logo = ''
    mkdir -p /usr/share/icons/hicolor/scalable/apps
    cp ${./logo/roudix-logo.svg} /usr/share/icons/hicolor/scalable/apps/roudix-logo.svg
  '';
}

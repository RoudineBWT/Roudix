{ pkgs, ... }:
{
  environment.systemPackages = [
    (pkgs.runCommand "roudix-logo" {} ''
      mkdir -p $out/share/icons/hicolor/256x256/apps
      cp ${./logo/roudix-logo.png} $out/share/icons/hicolor/256x256/apps/roudix-logo.png
    '')
  ];

  environment.pathsToLink = [ "/share/icons" ];
}

## _include-noctalia.nix — ajoute `include optional=true "noctalia.kdl"`
## à la fin du config.kdl généré par niri-flake (programs.niri.settings),
## pour que le thème régénéré en live par Noctalia (matugen) s'applique
## par-dessus. Technique reprise de github.com/Ly-sec/nixos
## (desktops/niri/home/noctalia-include.nix) : `finalConfig` est la
## sortie KDL rendue par niri-flake depuis `.settings` (readonly), on la
## concatène avec le texte d'include puis on revalide avec `niri validate`
## avant d'écraser `xdg.configFile.niri-config`.
{ config, pkgs, lib, ... }:
let
  niriPkg = config.programs.niri.package;
  withNoctalia = config.programs.niri.finalConfig + ''

    include optional=true "noctalia.kdl"
  '';
in
{
  xdg.configFile.niri-config = lib.mkForce {
    target = "niri/config.kdl";
    force = true;
    source = pkgs.runCommand "config.kdl" {
      config = withNoctalia;
      passAsFile = [ "config" ];
      buildInputs = [ niriPkg ];
    } ''
      niri validate -c $configPath
      cp $configPath $out
    '';
  };
}

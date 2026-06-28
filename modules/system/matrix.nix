{ config, lib, ... }:
{
  options.roudix.matrixClient = lib.mkOption {
    type    = lib.types.enum [ "element" "cinny" "none" ];
    default = "element";
    description = "Client Matrix à installer. 'none' pour n'en installer aucun.";
  };
}

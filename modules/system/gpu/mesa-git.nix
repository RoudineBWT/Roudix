{ config, lib, pkgs, inputs, ... }:

{
  options.roudix.mesa = {
    useGit = lib.mkEnableOption "mesa-git (bleeding-edge) au lieu de mesa stable";
  };
config = lib.mkIf config.roudix.mesa.useGit {
  chaotic.mesa-git.enable = true;
};
}

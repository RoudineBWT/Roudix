{ pkgs, inputs, lib, osConfig, options, ... }:
let
  dp = import ../../desktop-pkgs.nix {
    inherit pkgs inputs;
    latest = osConfig.roudix.desktop.latest;
  };
  # The flake home modules may not expose `package`: if not, stay on the
  # flake version instead of failing evaluation.
  has = path: lib.hasAttrByPath path options;
in
{
  # Imported only once here to avoid double declaration conflicts
  # when both niri.nix and hyprland.nix are loaded by home manager.
  # noctalia.homeModules.default removed: home-manager now provides
  # programs.noctalia nativement (modules/programs/noctalia.nix) — importer
  # having both caused an "option already declared" conflict.
  imports = [
    inputs.caelestia-shell.homeManagerModules.default
    inputs.dms.homeModules.dank-material-shell
  ];

  # Default: nixpkgs. roudix.desktop.latest.{dms,caelestia} = true keeps the
  # flake modules' own default (latest) package.
  config = lib.mkMerge [
    (lib.mkIf (dp.useNixpkgs "dms" && has [ "programs" "dank-material-shell" "package" ]) {
      programs.dank-material-shell.package = pkgs.dms-shell;
    })
    (lib.mkIf (dp.useNixpkgs "caelestia" && has [ "programs" "caelestia" "package" ]) {
      programs.caelestia.package = pkgs.caelestia-shell;
    })
    (lib.mkIf (dp.useNixpkgs "caelestia" && has [ "programs" "caelestia" "cli" "package" ]) {
      programs.caelestia.cli.package = pkgs.caelestia-cli;
    })
  ];
}

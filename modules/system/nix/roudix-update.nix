# modules/system/nix/roudix-update.nix
# `roudix-update` (shell alias: `update`) — manual counterpart of
# roudix-autoupdate. Same repo, same branch, same fast-forward-only rules,
# plus Flatpaks and an opt-in `--inputs` to bump flake inputs locally.
# The script itself lives in roudix-update.sh (pure bash, shellchecked at
# build time by writeShellApplication).
{ config, lib, pkgs, ... }:

let
  cfg = config.roudix.autoupdate;

  roudix-update = pkgs.writeShellApplication {
    name = "roudix-update";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.git
      pkgs.gnused
      pkgs.libnotify
      pkgs.nh
      pkgs.util-linux # flock
      config.nix.package
    ];
    text = ''
      CONFIG_PATH=${lib.escapeShellArg cfg.configPath}
      BRANCH=${lib.escapeShellArg cfg.branch}
      MIN_FREE_GB=${toString cfg.minFreeSpaceGB}
      FLATPAK_ENABLED=${if config.roudix.flatpak.enable then "1" else "0"}
      BUMP_INPUTS_DEFAULT=${if config.roudix.update.bumpInputs then "1" else "0"}

      ${builtins.readFile ./roudix-update.sh}
    '';
  };
in
{
  options.roudix.update.bumpInputs = lib.mkOption {
    type = lib.types.bool;
    default = false;
    description = ''
      Make a plain `update` also bump the flake inputs locally (as if
      `--inputs` was always passed; `update --no-inputs` skips it once).
      Leave it off on machines that follow the CI-validated flake.lock from
      git; meant for the maintainer's own machine tracking dev.
    '';
  };

  config.environment.systemPackages = [ roudix-update ];
}

# Decides, per component, whether the package comes from nixpkgs (default)
# or from the component's own flake input ("latest").
#
#   dp = import ../../desktop-pkgs.nix {
#     inherit pkgs inputs;
#     latest = config.roudix.desktop.latest;      # osConfig.… in home-manager
#   };
#   dp.useNixpkgs "dms"    -> true unless roudix.desktop.latest.dms = true
#   dp.niri                -> the package to use
#
# Only the selected branch is evaluated (Nix is lazy), so a wrong nixpkgs
# attribute name only breaks the people who actually use that branch.
# Every nixpkgs attribute name lives in this file: fix them here.
#
# Keys of `latest`: noctalia, dms, caelestia.
# niri, MangoWC and Umbriel are always taken from their flake (their NixOS /
# home-manager modules come from the flake too and must match the package);
# Hyprland has no flake input in Roudix (always nixpkgs): no toggle.
{ pkgs, inputs, latest ? { } }:
let
  sys = pkgs.stdenv.hostPlatform.system;
  wantsLatest = name: latest.${name} or false;
  useNixpkgs = name: !(wantsLatest name);
  pick = name: fromNixpkgs: fromFlake:
    if wantsLatest name then fromFlake else fromNixpkgs;
in
{
  inherit wantsLatest useNixpkgs;

  # niri-unstable comes from the niri-flake overlay, always applied
  # (see modules/system/desktop/niri.nix).
  niri = pkgs.niri-unstable;

  noctalia = pick "noctalia" pkgs.noctalia
    inputs.noctalia.packages.${sys}.default;

  # Always from the flake input: the home-manager module (inputs.mango.hmModules)
  # generates config keywords (exec_once, disable_while_typing, ov_tab_mode…)
  # that the older nixpkgs mango rejects when it validates the config at build.
  # Module and package must come from the same source.
  mango = inputs.mango.packages.${sys}.mango;

  # The umbriel overlay (inputs.umbriel.overlays.default) provides pkgs.umbriel
  # and is always applied (see modules/system/desktop/umbriel.nix).
  umbriel = pkgs.umbriel;

  # No `umbrielPortal` here anymore: xdg-desktop-portal-umbriel is an input of
  # the umbriel flake itself, and its NixOS module sets
  # programs.umbriel.portalPackage by default (see modules/system/desktop/umbriel.nix).
}

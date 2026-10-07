# Decides, per component, whether the package comes from nixpkgs (default)
# or from the component's own flake input ("latest").
#
#   dp = import ../../desktop-pkgs.nix {
#     inherit pkgs inputs;
#     latest = config.roudix.desktop.latest;      # osConfig.… in home-manager
#   };
#   dp.useNixpkgs "niri"   -> true unless roudix.desktop.latest.niri = true
#   dp.niri                -> the package to use
#
# Only the selected branch is evaluated (Nix is lazy), so a wrong nixpkgs
# attribute name only breaks the people who actually use that branch.
# Every nixpkgs attribute name lives in this file: fix them here.
#
# Keys of `latest`: niri, mangowc, umbriel, noctalia, dms, caelestia.
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

  # niri-unstable comes from the niri-flake overlay, which is only applied
  # when roudix.desktop.latest.niri = true (see modules/system/desktop/niri.nix).
  niri = pick "niri" pkgs.niri pkgs.niri-unstable;

  noctalia = pick "noctalia" pkgs.noctalia
    inputs.noctalia.packages.${sys}.default;

  mango = pick "mangowc" pkgs.mango
    inputs.mango.packages.${sys}.mango;

  # Flake side: the umbriel overlay (inputs.umbriel.overlays.default) provides
  # pkgs.umbriel and is only applied when roudix.desktop.latest.umbriel = true.
  umbriel = pkgs.umbriel;

  # No `umbrielPortal` here anymore: xdg-desktop-portal-umbriel is an input of
  # the umbriel flake itself, and its NixOS module sets
  # programs.umbriel.portalPackage by default (see modules/system/desktop/umbriel.nix).
}

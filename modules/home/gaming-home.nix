{ pkgs, inputs, osConfig, ... }:
let
  pkgs-stable = import inputs.nixpkgs-stable { system = pkgs.stdenv.hostPlatform; config.allowUnfree = true; };
  isKde = osConfig.roudix.desktop.type == "kde";
  isGaming = osConfig.roudix.gaming.enable;
  glfPkgs = inputs.glf-os + "/pkgs";
  roudixPkgs = inputs.roudix-caches + "/pkgs";
in
{

  # ── Gaming packages (user) ───────────────────────────────────────────────
  home.packages = with pkgs; (if isGaming then [
      (callPackage "${roudixPkgs}/heroic" {})
      (callPackage "${glfPkgs}/lutris" {})
      (callPackage "${glfPkgs}/faugus-launcher" {})
      prismlauncher
      vintagestory
      winetricks
      wineWow64Packages.staging
      mangohud
      (if isKde then protonup-qt else protonplus)
    ] else []);
}

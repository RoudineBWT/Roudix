{ pkgs, inputs, osConfig, ... }:
let
  pkgs-stable = import inputs.nixpkgs-stable { system = pkgs.stdenv.hostPlatform; config.allowUnfree = true; };
  isKde = osConfig.roudix.desktop.type == "kde";
  isGaming = osConfig.roudix.gaming.enable;
in
{
  # ── Gaming packages (user) ───────────────────────────────────────────────
  home.packages = with pkgs; (if isGaming then [
      heroic
      lutris
      prismlauncher
      vintagestory
      winetricks
      wineWow64Packages.staging
      mangohud
      (if isKde then protonup-qt else protonplus)
    ] else []);
}

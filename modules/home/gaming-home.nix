{ pkgs, inputs, lib, osConfig, ... }:
let
  pkgs-stable = import inputs.nixpkgs-stable { system = pkgs.stdenv.hostPlatform; config.allowUnfree = true; };
  isKde = osConfig.roudix.desktop.type == "kde";
  isGaming = osConfig.roudix.gaming.enable;
  roudixPkgs = inputs.roudix-caches + "/pkgs";
  steamCompatTools = with pkgs; [
     proton-ge-bin
     proton-cachyos-x86_64-v3
   ];
in
{

  xdg.dataFile = lib.mkIf isGaming (lib.genAttrs' steamCompatTools (
      tool:
      lib.nameValuePair "Steam/compatibilitytools.d/${lib.getName tool}" {
        source = tool.steamcompattool;
      }
  );

  # ── Gaming packages (user) ───────────────────────────────────────────────
  home.packages = with pkgs; (if isGaming then [
      (callPackage "${roudixPkgs}/heroic" {})
      (callPackage "${roudixPkgs}/lutris" {})
      (callPackage "${roudixPkgs}/faugus" {})
      prismlauncher
      vintagestory
      winetricks
      wineWow64Packages.staging
      mangohud
      hytale
      (if isKde then protonup-qt else protonplus)
    ] else []);
}

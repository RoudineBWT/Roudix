{ pkgs, inputs, lib, osConfig, ... }:
let
  isKde = osConfig.roudix.desktop.type == "kde";
  isGaming = osConfig.roudix.gaming.enable;
  apps = osConfig.roudix.gaming.apps;
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
      ));

  # ── Gaming packages (user) ───────────────────────────────────────────────
  # The base (wine/protontricks-like/proton frontend) always stays as
  # long as roudix.gaming.enable is set; each launcher/tool can be
  # individually disabled via roudix.gaming.apps.<name>.enable.
  home.packages = with pkgs; (if isGaming then
    [
      winetricks
      wineWow64Packages.staging
      (if isKde then protonup-qt else protonplus)
    ]
    ++ lib.optional apps.heroic.enable (callPackage "${roudixPkgs}/heroic" {})
    ++ lib.optional apps.faugus.enable (callPackage "${roudixPkgs}/faugus" {})
    ++ lib.optional apps.prismlauncher.enable (callPackage "${roudixPkgs}/prismlauncher/wrapped.nix" {
        prismlauncher-unwrapped = callPackage "${roudixPkgs}/prismlauncher" {};
      })
    ++ lib.optional apps.modrinth.enable (callPackage "${roudixPkgs}/modrinth/wrapped.nix" {
        modrinth-app-unwrapped = callPackage "${roudixPkgs}/modrinth" {};
      })
    ++ lib.optional apps.lutris.enable lutris
    ++ lib.optional apps.vintagestory.enable vintagestory
    ++ lib.optional apps.mangohud.enable mangohud
  else []);
}

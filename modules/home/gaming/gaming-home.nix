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
  # The base (wine/protontricks-like/proton frontend) only comes with
  # roudix.gaming.enable. Each launcher/tool is controlled by
  # roudix.gaming.apps.<name>.enable on its own (default: follows
  # roudix.gaming.enable), so a host can have e.g. Heroic alone without the
  # full gaming setup (see hosts/nixie).
  home.packages = with pkgs; (
    lib.optionals isGaming [
      winetricks
      wineWow64Packages.staging
      (if isKde then protonup-qt else protonplus)
    ]
    ++ lib.optional apps.heroic.enable (callPackage "${roudixPkgs}/heroic" {})
    ++ lib.optional apps.faugus.enable (callPackage "${roudixPkgs}/faugus" {})
    ++ lib.optional apps.prismlauncher.enable (callPackage "${roudixPkgs}/prismlauncher/wrapped.nix" {
        prismlauncher-unwrapped = callPackage "${roudixPkgs}/prismlauncher" {};
      })
    ++ lib.optional apps.modrinth.enable modrinth-app
    ++ lib.optional apps.lutris.enable lutris
    ++ lib.optional apps.vintagestory.enable vintagestory
    ++ lib.optional apps.mangohud.enable mangohud
  );
}

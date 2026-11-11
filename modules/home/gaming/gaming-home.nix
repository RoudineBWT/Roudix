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

  # Hybrid-graphics laptop: Valve's steam.desktop carries PrefersNonDefaultGPU=true,
  # which GNOME / KDE honour once switcheroo-control runs (enabled with
  # roudix.laptop.enable). That would start the Steam *client* on the dedicated
  # GPU (battery drain, and reported to misbehave with AMD dGPUs). User-level
  # entry overriding it: the client stays on the integrated GPU, games go to the
  # dedicated one through game-performance / roudix-dgpu. Same entry otherwise,
  # actions included.
  xdg.desktopEntries.steam = lib.mkIf (isGaming && osConfig.roudix.laptop.enable) {
    name = "Steam";
    comment = "Application for managing and playing games on Steam";
    exec = "steam %U";
    icon = "steam";
    terminal = false;
    type = "Application";
    categories = [ "Network" "FileTransfer" "Game" ];
    mimeType = [ "x-scheme-handler/steam" "x-scheme-handler/steamlink" ];
    settings = {
      PrefersNonDefaultGPU = "false";
      X-KDE-RunOnDiscreteGpu = "false";
      StartupWMClass = "steam";
    };
    actions = {
      Store = { name = "Store"; exec = "steam steam://store"; };
      Community = { name = "Community"; exec = "steam steam://url/CommunityHome/"; };
      Library = { name = "Library"; exec = "steam steam://open/games"; };
      Servers = { name = "Servers"; exec = "steam steam://open/servers"; };
      Screenshots = { name = "Screenshots"; exec = "steam steam://open/screenshots"; };
      News = { name = "News"; exec = "steam steam://open/news"; };
      Settings = { name = "Settings"; exec = "steam steam://open/settings"; };
      BigPicture = { name = "Big Picture"; exec = "steam steam://open/bigpicture"; };
      Friends = { name = "Friends"; exec = "steam steam://open/friends"; };
    };
  };

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
    ++ lib.optional apps.heroic.enable heroic
    ++ lib.optional apps.faugus.enable (callPackage "${roudixPkgs}/faugus" {})
    ++ lib.optional apps.prismlauncher.enable prismlauncher
    ++ lib.optional apps.modrinth.enable modrinth-app
    ++ lib.optional apps.lutris.enable lutris
    ++ lib.optional apps.vintagestory.enable vintagestory
    ++ lib.optional apps.mangohud.enable mangohud
  );
}

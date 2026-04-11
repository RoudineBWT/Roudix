{ lib, osConfig, inputs, ... }:
let
  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
{
  imports = [
    inputs.plasma-manager.homeModules.plasma-manager
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "kde") {
    programs.plasma = {
      enable = true;

      workspace = {
        # ── Thème sombre ──────────────────────────────────────────────────
        lookAndFeel = "org.kde.breezedark.desktop";
        colorScheme = "BreezeDark";
        iconTheme   = "Papirus-Dark";

        # Wallpaper par défaut Roudix Dark
        # Override dans home/local.nix :
        #   programs.plasma.workspace.wallpaper = lib.mkForce "/chemin/wallpaper.jpg";
        wallpaper = wallpaperDark;
      };

      # ── Écran de verrouillage ────────────────────────────────────────────
      # Override dans home/local.nix :
      #   programs.plasma.kscreenlocker.appearance.wallpaper = lib.mkForce "/chemin/wallpaper.jpg";
      kscreenlocker.appearance.wallpaper = wallpaperDark;

      # ── Barre des tâches ────────────────────────────────────────────────
      # Override dans home/local.nix :
      #   programs.plasma.panels = lib.mkForce [ ... ];
      panels = [
        {
          location = "bottom";
          widgets = [
            "org.kde.plasma.kickoff"
            "org.kde.plasma.icontasks"
            "org.kde.plasma.marginsseperator"
            "org.kde.plasma.systemtray"
            "org.kde.plasma.digitalclock"
            "org.kde.plasma.showdesktop"
          ];
        }
      ];
    };
  };
}

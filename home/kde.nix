{ lib, osConfig, inputs, ... }:
lib.mkIf (osConfig.roudix.desktop.type == "kde") {
  imports = [
    inputs.plasma-manager.homeManagerModules.plasma-manager
  ];

  programs.plasma = {
    enable = true;

    # ── Thème sombre ──────────────────────────────────────────────────────
    colorschemes = "BreezeDark";
    workspace = {
      lookAndFeel = "org.kde.breezedark.desktop";
      iconTheme   = "breeze-dark";

      # Wallpaper par défaut Roudix Dark
      # Override dans home/local.nix :
      #   programs.plasma.workspace.wallpaper = lib.mkForce "/chemin/wallpaper.jpg";
      wallpaper = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
    };

    # ── Barre des tâches ──────────────────────────────────────────────────
    # Override dans home/local.nix :
    #   programs.plasma.panels = lib.mkForce [ ... ];
    panels = [
      {
        location = "bottom";
        widgets = [
          {
            kickoff = {
              icon = "/run/current-system/sw/share/icons/hicolor/scalable/apps/roudix-logo.svg";
            };
          }
          "org.kde.plasma.icontasks"
          "org.kde.plasma.marginsseperator"
          "org.kde.plasma.systemtray"
          "org.kde.plasma.digitalclock"
          "org.kde.plasma.showdesktop"
        ];
      }
    ];
  };
}

{ lib, pkgs, osConfig, inputs, ... }:
let
  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
{
  imports = [
    inputs.plasma-manager.homeModules.plasma-manager
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "kde") {
    programs.plasma = {
      enable = true;

      input = {
          keyboard = {
            numlockOnStartup = "on";
          };
        };

      workspace = {
        # ── Thème sombre ──────────────────────────────────────────────────
        lookAndFeel = "org.kde.breezedark.desktop";
        colorScheme = "BreezeDark";
        # iconTheme retiré d'ici volontairement : plasma-manager transforme
        # sinon kdeglobals en symlink read-only vers le store Nix, ce qui
        # empêche ensuite papirusSync/telaSync (hooks noctalia) de patcher
        # la clé [Icons] Theme= avec sed. La valeur par défaut est posée
        # plus bas via home.activation + kwriteconfig6, sur un fichier
        # kdeglobals resté normal/mutable.
        cursorTheme = "capitaine-cursors-white";


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
          floating = true;
          widgets = [
            {
              kickoff.icon = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";
            }
            "org.kde.plasma.icontasks"
            "org.kde.plasma.marginsseparator"
            "org.kde.plasma.systemtray"
            "org.kde.plasma.digitalclock"
            "org.kde.plasma.showdesktop"
          ];
        }
      ];
    };

    # ── Thème d'icônes KDE, hors plasma-manager ────────────────────────────
    # Écrit avec kwriteconfig6 (mutateur natif KDE) au lieu de laisser
    # plasma-manager gérer kdeglobals : le fichier reste un fichier texte
    # normal, éditable ensuite par papirusSync/telaSync sans conflit avec
    # le symlink immuable que produirait la voie déclarative.
    home.activation.setKdeIconTheme = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${pkgs.kdePackages.kconfig}/bin/kwriteconfig6 \
        --file kdeglobals --group Icons --key Theme "Papirus-Dark"
    '';
  };
}

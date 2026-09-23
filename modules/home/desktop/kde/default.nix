{ lib, pkgs, osConfig, inputs, ... }:
let
  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixDark/contents/images/3840x2160.png";
in
{
  imports = [
    inputs.plasma-manager.homeModules.plasma-manager
    ../../theming/mangohud.nix
    ../../theming/papirus-folders.nix
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
        # ── Dark theme ──────────────────────────────────────────────────
        lookAndFeel = "org.kde.breezedark.desktop";
        colorScheme = "BreezeDark";
        # iconTheme deliberately left out here: otherwise plasma-manager
        # turns kdeglobals into a read-only symlink to the Nix store,
        # which then stops papirusSync/telaSync (noctalia hooks) from
        # patching the [Icons] Theme= key with sed. The default value is
        # set further below via home.activation + kwriteconfig6, on a
        # kdeglobals file that stays normal/mutable.
        cursorTheme = "capitaine-cursors-white";


        # Default Roudix Dark wallpaper
        # Override in home/local.nix:
        #   programs.plasma.workspace.wallpaper = lib.mkForce "/path/wallpaper.jpg";
        wallpaper = wallpaperDark;
      };

      # ── Lock screen ────────────────────────────────────────────
      # Override in home/local.nix:
      #   programs.plasma.kscreenlocker.appearance.wallpaper = lib.mkForce "/path/wallpaper.jpg";
      kscreenlocker.appearance.wallpaper = wallpaperDark;

      # ── Taskbar ────────────────────────────────────────────────
      # Override in home/local.nix:
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

    # ── KDE icon theme, outside plasma-manager ────────────────────────────
    # Written with kwriteconfig6 (native KDE mutator) instead of letting
    # plasma-manager manage kdeglobals: the file stays a normal text file,
    # later editable by papirusSync/telaSync without conflicting with the
    # immutable symlink the declarative path would produce.
    home.activation.setKdeIconTheme = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${pkgs.kdePackages.kconfig}/bin/kwriteconfig6 \
        --file kdeglobals --group Icons --key Theme "Papirus-Dark"
    '';
  };
}

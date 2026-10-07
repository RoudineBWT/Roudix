{ lib, pkgs, osConfig, inputs, ... }:
let
  wallpaperDark = "/run/current-system/sw/share/wallpapers/RoudixKitsune/contents/images/2560x1440.png";

  kwriteconfig6 = "${pkgs.kdePackages.kconfig}/bin/kwriteconfig6";

  terminalDesktopId = {
    ghostty   = "com.mitchellh.ghostty.desktop";
    kitty     = "kitty.desktop";
    alacritty = "Alacritty.desktop";
    foot      = "foot.desktop";
    wezterm   = "org.wezfurlong.wezterm.desktop";
    ptyxis    = "org.gnome.Ptyxis.desktop";
    konsole   = "org.kde.konsole.desktop";
  }.${osConfig.roudix.terminal or "ghostty"};
in
{
  imports = [
    inputs.plasma-manager.homeModules.plasma-manager
    ../../theming/mangohud.nix
    ../../theming/papirus-folders.nix
  ];

  # ── How Roudix ships its KDE look without overriding the user ─────────────
  # plasma-manager has three behaviours, and only one of them is safe here:
  #
  #  1. Settings that end up in a config file (workspace.colorScheme,
  #     lookAndFeel, cursorTheme, iconTheme, input.*, kscreenlocker...) are
  #     re-written on EVERY home-manager activation, i.e. every rebuild.
  #     -> not used for anything the user may want to change.
  #  2. Panels and wallpaper are "desktop scripts": they run at login, but
  #     only when their generated content changed since the last run. So
  #     they are applied once, then left alone (until Roudix itself changes
  #     the panel/wallpaper definition — see the note next to `panels`).
  #  3. `startup.startupScript` runs at login; with the marker file below it
  #     runs exactly once per user, ever.
  #
  # Theme defaults therefore go through (3); lock-screen wallpaper and NumLock
  # are plain KConfig defaults in /etc/xdg (modules/system/desktop/kde.nix),
  # which sit *under* ~/.config and never override it.
  config = lib.mkIf (osConfig.roudix.desktop.type == "kde") {
    programs.plasma = {
      enable = true;

      # ── First-login theme (dark) ──────────────────────────────────────────
      # Run once, guarded by a marker file, then never again: whatever the
      # user picks afterwards in System Settings is theirs. To re-apply the
      # Roudix look on purpose: rm ~/.local/state/roudix/kde-theme-seeded
      startup.startupScript."roudix_theme_defaults" = {
        priority = 1;
        text = ''
          marker="$HOME/.local/state/roudix/kde-theme-seeded"
          if [ ! -f "$marker" ]; then
            plasma-apply-lookandfeel -a org.kde.breezedark.desktop
            plasma-apply-colorscheme BreezeDark
            plasma-apply-cursortheme capitaine-cursors-white
            # Icons via kwriteconfig6 rather than plasma-manager: keeps
            # kdeglobals a normal, writable file (papirusSync / telaSync
            # patch its [Icons] Theme= key with sed).
            ${kwriteconfig6} --file kdeglobals --group Icons --key Theme "Papirus-Dark"
            mkdir -p "$(dirname "$marker")" && touch "$marker"
          fi
        '';
      };

      workspace = {
        # Default Roudix Dark wallpaper (applied at first login by a desktop
        # script, not re-applied afterwards).
        # Override in home/local.nix:
        #   programs.plasma.workspace.wallpaper = lib.mkForce "/path/wallpaper.jpg";
        wallpaper = wallpaperDark;
      };

      # ── Taskbar ────────────────────────────────────────────────
      # Applied at first login, then left alone. Caveat: if a future Roudix
      # update changes this definition, plasma-manager re-runs ALL desktop
      # scripts once (panel + wallpaper), which resets the user's panel.
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
            {
              iconTasks.launchers = [
                "preferred://filemanager"
                "preferred://browser"
                "applications:${terminalDesktopId}"
                "applications:io.roudix.store.desktop"
                "applications:systemsettings.desktop"
              ];
            }
            "org.kde.plasma.marginsseparator"
            "org.kde.plasma.systemtray"
            "org.kde.plasma.digitalclock"
            "org.kde.plasma.showdesktop"
          ];
        }
      ];
    };
  };
}

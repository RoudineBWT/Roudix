{ config, lib, pkgs, ... }:
let
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
  isBareCompositor = builtins.elem config.roudix.desktop.type [ "niri" "hyprland" "mangowc" "umbriel" ];

  # ── KDE counterparts of the GNOME pieces (bare compositors only) ───────────
  # keyring / portal / polkit are switched in niri.nix, hyprland.nix,
  # mangowc.nix and umbriel.nix; the home-manager side swaps the small app
  # bundle (modules/home/desktop/_integration-apps.nix) and the default file
  # manager follows (modules/system/apps/utilities/filemanager.nix).
  # What is installed here is the system-wide part those apps need.
  #
  # Kept on purpose: adw-gtk3 + nwg-look (GTK apps stay themed), qt6ct/qt5ct
  # (Noctalia/DMS Qt theming), gvfs (GTK apps' trash/mounts).
  kdeCounterparts = lib.mkIf (isKdeIntegration && isBareCompositor) {
    # KDE Partition Manager + kpmcore D-Bus helper/polkit action
    # (replaces gnome-disk-utility).
    programs.partition-manager.enable = true;

    environment.systemPackages = with pkgs.kdePackages; [
      breeze              # Qt style, so Dolphin/Kate don't fall back to Fusion
      kio-extras          # trash:/, smb://, MTP, thumbnails in Dolphin/Gwenview
      kdegraphics-thumbnailers
      ffmpegthumbs
    ] ++ [
      # Dolphin's "Open With" (via KService/sycoca) needs *some* freedesktop
      # menu file. plasma-workspace ships one but drags in half of Plasma;
      # lxmenu-data is data-only (no Qt/Plasma deps) and provides
      # /etc/xdg/menus/lxde-applications.menu, hence the prefix below.
      pkgs.lxmenu-data
    ];

    environment.sessionVariables.XDG_MENU_PREFIX = "lxde-";

    # xdg-desktop-portal-kde (file picker, ...) is a Qt app started by
    # systemd/D-Bus activation, NOT by the compositor, so it never sees the
    # QT_QPA_PLATFORMTHEME that niri/umbriel/mango set in their own
    # `environment` block. It then falls back to plain Fusion = light
    # dialog. (hyprland only works because its autostart runs
    # `dbus-update-activation-environment --systemd --all`.) Setting it in
    # the user manager makes every compositor behave the same, and the
    # dialog follows the qt6ct colors Noctalia/DMS generate.
    # (systemd.user.extraConfig is deprecated: systemd.user.settings.Manager.)
    systemd.user.settings.Manager.DefaultEnvironment =
      "\"QT_QPA_PLATFORMTHEME=qt6ct\" \"QT_QPA_PLATFORMTHEME_QT6=qt6ct\" \"QT_PLUGIN_PATH=${pkgs.qt6Packages.qt6ct}/${pkgs.qt6.qtbase.qtPluginPrefix}\"";
  };
in
{
  # dconf is what GSettings-backed apps (GTK3/4, and Chromium-family
  # browsers like Helium/Brave/Chromium) read their theme/icon/cursor
  # choice from. Previously only enabled inside modules/system/desktop/
  # gnome.nix, so niri/hyprland/mangowc/umbriel got no GTK theming at all
  # for those apps (no dconf database → GSettings falls back to
  # upstream/Adwaita defaults regardless of what modules/home/theming/gtk-theme.nix
  # writes to ~/.config/gtk-3.0/settings.ini). mkDefault so gnome.nix's own
  # (identical) assignment, or a user override in home/local.nix or
  # hosts/*/local.nix, still wins without a "defined twice" conflict.
  config = lib.mkMerge [
    { programs.dconf.enable = lib.mkDefault true; }
    kdeCounterparts
  ];

  options.roudix.desktopIntegration = lib.mkOption {
    type = lib.types.enum [ "gnome" "kde" ];
    default = "gnome";
    description = ''
      Keyring + xdg-desktop-portal stack used by "bare" compositors (niri,
      hyprland, mangowc, umbriel) that have no full DE providing their own
      stack natively. Has no effect when roudix.desktop.type is "gnome" or
      "kde": those DEs always keep their own native integration.

      "gnome"  → gnome-keyring + xdg-desktop-portal-gtk/-gnome (default).
      "kde"    → KWallet + xdg-desktop-portal-kde + polkit-kde-agent, and
                 the GNOME apps are swapped for their KDE counterparts:
                   gnome-text-editor  → Kate
                   loupe              → Gwenview
                   gnome-disk-utility → KDE Partition Manager
                   Nautilus (default) → Dolphin
                 adw-gtk3, nwg-look, qt6ct and gvfs are kept so GTK apps
                 stay themed. Useful if you mostly use Qt/KDE apps on a
                 compositor that's neither GNOME nor KDE.

      ⚠ On compositors using greetd (the default, via noctalia-greeter),
      KWallet auto-unlock at login has a known nixpkgs limitation (the
      "greetd" PAM service doesn't substack "login" — nixpkgs#357201).
      Verify after a rebuild; if the wallet stays locked, see the
      comments in modules/system/desktop/*.nix for the workaround.
    '';
  };
}

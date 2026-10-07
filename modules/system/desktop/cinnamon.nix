{ config, lib, pkgs, roudixBranding, ... }:
let
  isCinnamon = config.roudix.desktop.type == "cinnamon";

  wallpaper = "file:///run/current-system/sw/share/backgrounds/b-kitsune.png";

  # Same browser -> .desktop id table as gnome.nix (kept in sync by hand;
  # an unknown id is silently ignored by Cinnamon's menu, so a wrong guess
  # only means "not pinned").
  browserDesktopIds = {
    "brave"                = [ "brave-browser.desktop" ];
    "brave-beta"           = [ "brave-browser-beta.desktop" ];
    "brave-nightly"        = [ "brave-browser-nightly.desktop" ];
    "brave-origin"         = [ "brave-origin.desktop" ];
    "brave-origin-beta"    = [ "brave-origin-beta.desktop" ];
    "brave-origin-nightly" = [ "brave-origin-nightly.desktop" ];
    "helium"               = [ "helium.desktop" "helium-browser.desktop" ];
    "vivaldi"              = [ "vivaldi-stable.desktop" ];
    "chromium"             = [ "chromium-browser.desktop" ];
    "ungoogled-chromium"   = [ "chromium-browser.desktop" ];
    "firefox"              = [ "firefox.desktop" ];
    "librewolf"            = [ "librewolf.desktop" ];
    "google-chrome"        = [ "google-chrome.desktop" ];
    "microsoft-edge"       = [ "microsoft-edge.desktop" ];
  };

  favoriteApps =
    lib.concatMap (b: browserDesktopIds.${b} or [ ]) config.roudix.browsers
    ++ [
      "nemo.desktop"
      "io.roudix.store.desktop"
    ];

  # ── Roudix look & feel, as dconf DEFAULTS ─────────────────────────────
  # Same mechanism as gnome.nix: written to the *system* dconf database, so
  # it only applies to keys the user never touched. A rebuild never reverts
  # a choice made in Cinnamon Settings.
  cinnamonDefaults = {
    "org/cinnamon" = {
      # Favorites of the Cinnamon menu (the browser(s) chosen in Roudix, Nemo,
      # Roudix Store). The panel's window-list pinning is a per-applet JSON
      # file under ~/.config/cinnamon/spices, not a dconf key — left to the user.
      favorite-apps = favoriteApps;
    };
    "org/cinnamon/desktop/background" = {
      picture-uri     = wallpaper;
      picture-options = "zoom";
    };
    "org/cinnamon/desktop/interface" = {
      gtk-theme    = "Mint-Y-Dark-Aqua";
      icon-theme   = "Papirus-Dark";
      cursor-theme = "capitaine-cursors-white";
      cursor-size  = lib.gvariant.mkInt32 24;
    };
    "org/cinnamon/theme".name = "Mint-Y-Dark-Aqua";
    "org/cinnamon/desktop/wm/preferences".theme = "Mint-Y-Dark-Aqua";
    # libadwaita / GTK4 apps follow this one.
    "org/gnome/desktop/interface".color-scheme = "prefer-dark";
    # Terminal chosen in Roudix (gnome-terminal is excluded below).
    "org/cinnamon/desktop/default-applications/terminal" = {
      exec     = config.roudix.terminal;
      exec-arg = "-e";
    };
  };

  # Same "Roudix" application-menu category as kde.nix: Roudix apps carry
  # Categories=...;X-Roudix; and this merged menu groups them in one folder.
  roudixMenu = {
    text = ''
      <!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
        "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
      <Menu>
        <Name>Applications</Name>
        <Menu>
          <Name>System</Name>
          <Exclude><Category>X-Roudix</Category></Exclude>
        </Menu>
        <Menu>
          <Name>Settingsmenu</Name>
          <Exclude><Category>X-Roudix</Category></Exclude>
        </Menu>
        <Menu>
          <Name>Roudix</Name>
          <Directory>roudix.directory</Directory>
          <Include><Category>X-Roudix</Category></Include>
        </Menu>
      </Menu>
    '';
  };
in
lib.mkIf isCinnamon {
  # ── X11 session + LightDM ────────────────────────────────────────────────
  # Cinnamon is an X11 desktop (its Wayland session is still experimental).
  # That is the point of choosing it on older hardware: GNOME 49 is
  # Wayland-only. The nixpkgs module only configures the slick greeter, it
  # does not turn LightDM on.
  services.xserver.enable = true;
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.displayManager.lightdm.background =
    "${roudixBranding}/share/backgrounds/b-kitsune.png";
  services.displayManager.defaultSession = "cinnamon";
  services.xserver.desktopManager.cinnamon.enable = true;

  # X11 keyboard layout (greeter + session); other DEs get theirs through
  # their own compositor/greeter settings, see keyboard.nix.
  services.xserver.xkb = {
    layout  = config.roudix.keyboardLayout;
    variant = config.roudix.keyboardVariant;
  };

  # ── Keyring ───────────────────────────────────────────────────────────────
  # The nixpkgs Cinnamon module already enables gnome-keyring; unlock it at
  # the LightDM login.
  security.pam.services.lightdm.enableGnomeKeyring = true;

  # ── Look & feel (dconf defaults) ──────────────────────────────────────────
  programs.dconf.enable = true;
  programs.dconf.profiles.user.databases = [
    { settings = cinnamonDefaults; }
  ];

  # ── Menu: "Roudix" category ──────────────────────────────────────────────
  # Dropped in both merge dirs, as in kde.nix, because the directory name
  # depends on XDG_MENU_PREFIX.
  environment.etc."xdg/menus/applications-merged/roudix.menu"          = roudixMenu;
  environment.etc."xdg/menus/cinnamon-applications-merged/roudix.menu" = roudixMenu;

  # Roudix provides its own terminal; warpinator opens LAN ports nobody
  # asked for on a hands-off family machine.
  environment.cinnamon.excludePackages = with pkgs; [
    gnome-terminal
    warpinator
  ];

  environment.systemPackages = with pkgs; [
    (writeTextDir "share/desktop-directories/roudix.directory" ''
      [Desktop Entry]
      Type=Directory
      Name=Roudix
      Icon=roudix-logo
    '')
    (lib.hiPrio roudixBranding)
    papirus-icon-theme
    capitaine-cursors
  ];
}

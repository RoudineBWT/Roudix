{ config, lib, pkgs, roudixBranding, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaperDark = "${roudixBranding}/share/wallpapers/RoudixKitsune/contents/images/2560x1440.png";

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
lib.mkIf isKde {
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Plasma Login Manager ──────────────────────────────────────────────────
  services.displayManager.plasma-login-manager = {
    enable = true;
  };

  # ── Plasma Login Manager wallpaper ────────────────────────────────────────
  # The KCM reads the wallpaper from /var/lib/plasmalogin/wallpapers/
  # and references it via /etc/plasmalogin.conf with a file:// prefix
  environment.etc."plasmalogin.conf".text = ''
    [Greeter][Wallpaper][org.kde.image][General]
    Image=file:///var/lib/plasmalogin/wallpapers/RoudixKitsune
  '';

  system.activationScripts.plasmaLoginWallpaper = {
    deps = [ "users" "groups" ];
    text = ''
      install -d -o plasmalogin -g plasmalogin /var/lib/plasmalogin/wallpapers/RoudixKitsune/contents/images
      cp ${wallpaperDark} /var/lib/plasmalogin/wallpapers/RoudixKitsune/contents/images/2560x1440.png
      cp ${roudixBranding}/share/wallpapers/RoudixKitsune/metadata.json /var/lib/plasmalogin/wallpapers/RoudixKitsune/metadata.json
      chown -R plasmalogin:plasmalogin /var/lib/plasmalogin/wallpapers/
    '';
  };

  # ── Config defaults under ~/.config ───────────────────────────────────────
  # KConfig reads /etc/xdg/<file> as a fallback below ~/.config/<file>: these
  # are defaults for anything the user never set. Once they change the
  # setting in System Settings it is stored in their own file and wins; a
  # rebuild never touches it (unlike plasma-manager's `input.*` /
  # `kscreenlocker.*`, which are re-written on every activation).
  #
  # NumLock: 0 = on, 1 = off, 2 = leave unchanged.
  environment.etc."xdg/kcminputrc".text = ''
    [Keyboard]
    NumLock=0
  '';

  environment.etc."xdg/kscreenlockerrc".text = ''
    [Greeter]
    WallpaperPlugin=org.kde.image

    [Greeter][Wallpaper][org.kde.image][General]
    Image=${wallpaperDark}
  '';

  # ── "Roudix" category in the application menu (Kickoff) ───────────────
  # Roudix apps carry Categories=...;X-Roudix; in their .desktop files. This
  # merged menu turns that tag into a "Roudix" submenu and removes those apps
  # from System/Settings so they aren't listed twice. Dropped in both merge
  # dirs because the file name depends on XDG_MENU_PREFIX (plasma- or none).
  environment.pathsToLink = [ "/share/desktop-directories" ];
  environment.etc."xdg/menus/applications-merged/roudix.menu" = roudixMenu;
  environment.etc."xdg/menus/plasma-applications-merged/roudix.menu" = roudixMenu;


  # ── Hardware ──────────────────────────────────────────────────────────────
  hardware.bluetooth.enable = true;

  # ── Portals ───────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  # ── KDE Connect ───────────────────────────────────────────────────────────
  programs.kdeconnect.enable = true;
  documentation.nixos.enable = false;

  # ── Polkit agent ──────────────────────────────────────────────────────────
  # PLM (Plasma Login Manager) doesn't always trigger the autostart that
  # normally launches polkit-kde-authentication-agent-1 (unlike SDDM).
  # Forced via a systemd user service tied to the graphical session.
  systemd.user.services.polkit-kde-agent = {
    description = "PolicyKit KDE Authentication Agent";
    wantedBy = [ "graphical-session.target" ];
    partOf = [ "graphical-session.target" ];
    serviceConfig = {
      ExecStart = "${pkgs.kdePackages.polkit-kde-agent-1}/libexec/polkit-kde-authentication-agent-1";
      Restart = "on-failure";
    };
  };

  # ── Excluded packages ─────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ───────────────────────────────────────────────────────
  # lib.hiPrio on roudix-branding so start-here-kde overrides Papirus
  environment.systemPackages = with pkgs; [
    (writeTextDir "share/desktop-directories/roudix.directory" ''
      [Desktop Entry]
      Type=Directory
      Name=Roudix
      Icon=roudix-logo
    '')
    (lib.hiPrio roudixBranding)
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    papirus-icon-theme
    capitaine-cursors
    vlc
    digikam
  ];
}

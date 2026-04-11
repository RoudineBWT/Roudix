{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";
in
lib.mkIf isKde {
  services.displayManager.plasma-login-manager.enable = true;
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  environment.etc."plasmalogin.conf".text = ''
    [Greeter]
    WallpaperPlugin=org.kde.image

    [Greeter.WallpaperPlugin.org.kde.image]
    Image=/run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg
  '';

  environment.etc."backgrounds/roudix/roudix-dark.svg".source =
    ../../assets/wallpapers/roudix-dark.svg;

  hardware.bluetooth.enable = true;

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  systemd.services."getty@tty1".enable  = false;
  systemd.services."autovt@tty1".enable = false;

  systemd.user.services.plasma-taskbar-icon-fix = {
    description = "Fix plasma taskbar icon path";
    before   = [ "plasma-plasmashell.service" ];
    wantedBy = [ "plasma-core.target" ];
    serviceConfig = {
      Type      = "simple";
      ExecStart = "${pkgs.writeShellScriptBin "plasma-taskbar-icon-fix" ''
        #!${pkgs.bash}
        if [ -f ''${HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc ]; then
          ${pkgs.gnused}/bin/sed -i 's/file:\/\/\/nix\/store\/[^\/]*\/share\/applications\//applications:/gi' ''${HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc
        fi
      ''}/bin/plasma-taskbar-icon-fix";
    };
    restartIfChanged = false;
  };

  # Icône du menu KDE
  systemd.user.services.plasma-menu-icon = {
    description = "Set Roudix KDE menu icon";
    after    = [ "plasma-plasmashell.service" ];
    wantedBy = [ "plasma-core.target" ];
    serviceConfig = {
      Type      = "oneshot";
      ExecStart = "${pkgs.writeShellScriptBin "plasma-menu-icon" ''
        #!${pkgs.bash}
        ${pkgs.kdePackages.plasma-workspace}/bin/kwriteconfig6 \
          --file plasma-org.kde.plasma.desktop-appletsrc \
          --group "Containments" --group "1" \
          --group "Applets" --group "2" \
          --group "Configuration" --group "General" \
          --key "icon" "start-here-kde"
      ''}/bin/plasma-menu-icon";
    };
    restartIfChanged = false;
  };

  programs.kdeconnect.enable = true;
  documentation.nixos.enable = false;

  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  environment.systemPackages = with pkgs; [
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    vlc
    digikam
    (pkgs.runCommand "roudix-backgrounds" {} ''
        mkdir -p $out/share/wallpapers/roudix
        cp ${./../../assets/wallpapers/roudix-dark.svg} $out/share/backgrounds/roudix/roudix-dark.svg
      '')
  ];
}

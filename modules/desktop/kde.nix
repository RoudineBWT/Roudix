{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";
in
lib.mkIf isKde {
  services.displayManager.plasma-login-manager.enable = true;
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  hardware.bluetooth.enable = true;

  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "*";
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
  ];
}

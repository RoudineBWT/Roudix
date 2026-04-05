{ config, lib, pkgs, inputs, ... }:
{
  # ── Desktop environment option ───────────────────────────────────────────
  options.roudix.desktop.type = lib.mkOption {
    description = "Desktop environment selection. Use 'roudix-switch <de>' to change.";
    type = lib.types.enum [ "niri" "gnome" "kde" ];
    default = "niri";
  };

  # ── Activate the selected desktop ────────────────────────────────────────
  config = {
    # Niri
    programs.niri.enable = lib.mkIf (config.roudix.desktop.type == "niri") true;

    programs.uwsm = lib.mkIf (config.roudix.desktop.type == "niri") {
      enable = true;
      waylandCompositors.niri = {
        prettyName = "Niri";
        comment     = "Niri scrollable tiling compositor";
        binPath     = "/run/current-system/sw/bin/niri";
      };
    };

    systemd.user.services.polkit-gnome = lib.mkIf (config.roudix.desktop.type == "niri") {
      description = "GNOME Polkit authentication agent";
      wantedBy = [ "graphical-session.target" ];
      after = [ "graphical-session.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart = "on-failure";
      };
    };

    # GNOME
    services.desktopManager.gnome.enable = lib.mkIf (config.roudix.desktop.type == "gnome") true;

    nixpkgs.overlays = lib.mkIf (config.roudix.desktop.type == "gnome") [
      (final: prev: {
        gnome = inputs.nixpkgsStaging.legacyPackages.${prev.system}.gnome;
      })
    ];

    environment.gnome.excludePackages = lib.mkIf (config.roudix.desktop.type == "gnome") (with pkgs; [
      tali iagno hitori atomix yelp geary xterm totem
      epiphany gnome-tour gnome-software gnome-contacts
      gnome-user-docs gnome-font-viewer gnome-music
    ]);

    # KDE Plasma 6
    services.displayManager.plasma-login-manager.enable = lib.mkIf (config.roudix.desktop.type == "kde") true;
    services.displayManager.defaultSession = lib.mkIf (config.roudix.desktop.type == "kde") "plasma";
    services.desktopManager.plasma6.enable = lib.mkIf (config.roudix.desktop.type == "kde") true;

    hardware.bluetooth.enable = lib.mkIf (config.roudix.desktop.type == "kde") true;

    systemd.services."getty@tty1".enable = lib.mkIf (config.roudix.desktop.type == "kde") false;
    systemd.services."autovt@tty1".enable = lib.mkIf (config.roudix.desktop.type == "kde") false;

    systemd.user.services.plasma-taskbar-icon-fix = lib.mkIf (config.roudix.desktop.type == "kde") {
      description = "Fix plasma taskbar icon path";
      before = [ "plasma-plasmashell.service" ];
      wantedBy = [ "plasma-core.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${pkgs.writeShellScriptBin "plasma-taskbar-icon-fix" ''
          #!${pkgs.bash}
          if [ -f ''${HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc ]; then
            ${pkgs.gnused}/bin/sed -i 's/file:\/\/\/nix\/store\/[^\/]*\/share\/applications\//applications:/gi' ''${HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc
          fi
        ''}/bin/plasma-taskbar-icon-fix";
      };
      restartIfChanged = false;
    };

    programs.kdeconnect.enable = lib.mkIf (config.roudix.desktop.type == "kde") true;
    documentation.nixos.enable = lib.mkIf (config.roudix.desktop.type == "kde") false;

    environment.plasma6.excludePackages = lib.mkIf (config.roudix.desktop.type == "kde") [
      pkgs.kdePackages.discover
    ];

    # Shared portals
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; lib.mkMerge [
        (lib.mkIf (config.roudix.desktop.type == "gnome") [
          xdg-desktop-portal-gnome
          xdg-desktop-portal-gtk
        ])
        (lib.mkIf (config.roudix.desktop.type == "niri") [
          xdg-desktop-portal-gtk
        ])
        (lib.mkIf (config.roudix.desktop.type == "kde") [
          kdePackages.xdg-desktop-portal-kde
        ])
      ];
      xdgOpenUsePortal = lib.mkIf (config.roudix.desktop.type == "kde") true;
      config.common.default = "*";
    };

    # Polkit agent + packages (Niri only)
    environment.systemPackages = lib.mkMerge [
      (lib.mkIf (config.roudix.desktop.type == "niri") (with pkgs; [
        polkit_gnome
      ]))
      (lib.mkIf (config.roudix.desktop.type == "kde") (with pkgs; [
        kdePackages.partitionmanager
        kdePackages.kpmcore
        vlc
        digikam
        kdePackages.kcalc
        kdePackages.qtwebengine
      ]))
    ];
  };
}

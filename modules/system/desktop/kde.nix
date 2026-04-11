{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaper = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";

  # Script de branding : wallpaper desktop + icône menu Kickoff
  brandingScript = pkgs.writeShellScriptBin "roudix-kde-branding" ''
    #!${pkgs.bash}

    PLASMA_CFG="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    # Attendre que plasmashell soit vraiment prêt (max 30s)
    for i in $(seq 1 60); do
      ${pkgs.dbus}/bin/dbus-send --session --dest=org.kde.plasmashell \
        /PlasmaShell org.kde.PlasmaShell.version 2>/dev/null && break
      sleep 0.5
    done

    # Attendre que le fichier de config Plasma existe
    for i in $(seq 1 20); do
      [ -f "$PLASMA_CFG" ] && break
      sleep 0.5
    done
    [ -f "$PLASMA_CFG" ] || exit 1

    # ── Détection dynamique du containment et de l'applet Kickoff ────────────
    KICKOFF_LINE=$(${pkgs.gnugrep}/bin/grep -n "plugin=org.kde.plasma.kickoff" "$PLASMA_CFG" 2>/dev/null | ${pkgs.coreutils}/bin/cut -d: -f1 | ${pkgs.coreutils}/bin/head -1)

    if [ -n "$KICKOFF_LINE" ]; then
      KICKOFF_SECTION=$(${pkgs.gnused}/bin/sed -n "1,''${KICKOFF_LINE}p" "$PLASMA_CFG" | ${pkgs.gnugrep}/bin/grep "^\[Containments\]" | ${pkgs.coreutils}/bin/tail -1)
      CONTAINMENT=$(echo "$KICKOFF_SECTION" | ${pkgs.gnugrep}/bin/grep -oP '\[\K[0-9]+(?=\]\[Applets\])')
      APPLET=$(echo "$KICKOFF_SECTION" | ${pkgs.gnugrep}/bin/grep -oP 'Applets\]\[\K[0-9]+')
    fi

    CONTAINMENT="''${CONTAINMENT:-1}"
    APPLET="''${APPLET:-2}"

    # ── Icône du menu Kickoff (via kwriteconfig6) ─────────────────────────────
    ${pkgs.kdePackages.plasma-workspace}/bin/kwriteconfig6 \
      --file plasma-org.kde.plasma.desktop-appletsrc \
      --group "Containments" --group "$CONTAINMENT" \
      --group "Applets" --group "$APPLET" \
      --group "Configuration" --group "General" \
      --key "icon" "start-here"

    # ── Wallpaper du desktop via l'API JavaScript de plasmashell ─────────────
    # (plus fiable que kwriteconfig6 + refreshCurrentShell)
    ${pkgs.kdePackages.plasma-workspace}/bin/qdbus org.kde.plasmashell /PlasmaShell \
      org.kde.PlasmaShell.evaluateScript "
        var allDesktops = desktops();
        for (var i = 0; i < allDesktops.length; i++) {
          var d = allDesktops[i];
          d.wallpaperPlugin = 'org.kde.image';
          d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
          d.writeConfig('Image', '${wallpaper}');
        }
      " 2>/dev/null || true
  '';

in
lib.mkIf isKde {
  services.displayManager.plasma-login-manager.enable = true;
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Hardware ───────────────────────────────────────────────────────────────
  hardware.bluetooth.enable = true;

  # ── Portals ────────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  # ── Disable getty/autovt on tty1 (handled by display manager) ─────────────
  systemd.services."getty@tty1".enable  = false;
  systemd.services."autovt@tty1".enable = false;

  # ── Fix plasma taskbar icon path ───────────────────────────────────────────
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

  # ── Roudix branding : wallpaper desktop + icône menu ──────────────────────
  # Les assets (wallpapers + icônes) sont fournis par pkgs/roudix-branding
  # via branding.nix — pas besoin de runCommand ici
  systemd.user.services.roudix-kde-branding = {
    description = "Apply Roudix KDE branding (wallpaper + menu icon)";
    after    = [ "plasma-plasmashell.service" ];
    wantedBy = [ "plasma-core.target" ];
    serviceConfig = {
      Type            = "oneshot";
      ExecStart       = "${brandingScript}/bin/roudix-kde-branding";
      RemainAfterExit = true;
    };
    restartIfChanged = false;
  };

  # ── KDE Connect ───────────────────────────────────────────────────────────
  programs.kdeconnect.enable = true;
  documentation.nixos.enable = false;

  # ── Excluded packages ──────────────────────────────────────────────────────
  environment.plasma6.excludePackages = with pkgs; [
    kdePackages.discover
  ];

  # ── System packages ────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    kdePackages.partitionmanager
    kdePackages.kpmcore
    kdePackages.kcalc
    kdePackages.qtwebengine
    vlc
    digikam
  ];
}

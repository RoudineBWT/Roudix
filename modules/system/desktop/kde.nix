{ config, lib, pkgs, ... }:
let
  isKde = config.roudix.desktop.type == "kde";

  wallpaper = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.svg";

  brandingScript = pkgs.writeShellScriptBin "roudix-kde-branding" ''
    #!${pkgs.bash}

    PLASMA_CFG="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    # Attendre que plasmashell soit prêt sur DBus
    for i in $(seq 1 60); do
      ${pkgs.dbus}/bin/dbus-send --session --dest=org.kde.plasmashell \
        --type=method_call /PlasmaShell \
        org.kde.PlasmaShell.evaluateScript string:"" 2>/dev/null && break
      sleep 0.5
    done

    # Laisser le temps à plasmashell de vraiment finir l'init
    sleep 3

    # Attendre que le fichier de config Plasma existe
    for i in $(seq 1 20); do
      [ -f "$PLASMA_CFG" ] && break
      sleep 0.5
    done
    [ -f "$PLASMA_CFG" ] || exit 1

    # ── Fix taskbar icon path ─────────────────────────────────────────────────
    ${pkgs.gnused}/bin/sed -i \
      's/file:\/\/\/nix\/store\/[^\/]*\/share\/applications\//applications:/gi' \
      "$PLASMA_CFG"

    # ── Icône du menu Kickoff via kwriteconfig6 ───────────────────────────────
    KICKOFF_LINE=$(${pkgs.gnugrep}/bin/grep -n "plugin=org.kde.plasma.kickoff" "$PLASMA_CFG" 2>/dev/null \
      | ${pkgs.coreutils}/bin/cut -d: -f1 \
      | ${pkgs.coreutils}/bin/head -1)

    if [ -n "$KICKOFF_LINE" ]; then
      SECTION=$(${pkgs.gnused}/bin/sed -n "1,''${KICKOFF_LINE}p" "$PLASMA_CFG" \
        | ${pkgs.gnugrep}/bin/grep "^\[Containments\]\[[0-9]*\]\[Applets\]\[[0-9]*\]" \
        | ${pkgs.coreutils}/bin/tail -1)
      CONTAINMENT=$(echo "$SECTION" | ${pkgs.gnugrep}/bin/grep -oP '\[Containments\]\[\K[0-9]+')
      APPLET=$(echo "$SECTION" | ${pkgs.gnugrep}/bin/grep -oP '\[Applets\]\[\K[0-9]+')
    fi

    CONTAINMENT="''${CONTAINMENT:-2}"
    APPLET="''${APPLET:-3}"

    ${pkgs.kdePackages.plasma-workspace}/bin/kwriteconfig6 \
      --file plasma-org.kde.plasma.desktop-appletsrc \
      --group "Containments" --group "$CONTAINMENT" \
      --group "Applets" --group "$APPLET" \
      --group "Configuration" --group "General" \
      --key "icon" "roudix-logo"

    # ── Wallpaper via dbus evaluateScript ─────────────────────────────────────
    ${pkgs.dbus}/bin/dbus-send --session --dest=org.kde.plasmashell \
      --type=method_call /PlasmaShell \
      org.kde.PlasmaShell.evaluateScript \
      string:"
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
  # ── Display Manager ────────────────────────────────────────────────────────
  services.displayManager.sddm = {
    enable         = true;
    wayland.enable = true;
  };
  services.displayManager.defaultSession = "plasma";
  services.desktopManager.plasma6.enable = true;

  # ── Thème sombre par défaut ────────────────────────────────────────────────
  environment.etc."xdg/kdeglobals".text = ''
    [KDE]
    ColorScheme=BreezeDark
    widgetStyle=Breeze

    [General]
    ColorScheme=BreezeDark

    [Icons]
    Theme=breeze-dark
  '';

  # ── Icône Kickoff par défaut (avant premier login) ─────────────────────────
  # Les IDs 2/3 correspondent à une fresh install Plasma standard
  # Le service branding corrige dynamiquement si les IDs diffèrent
  environment.etc."xdg/plasma-org.kde.plasma.desktop-appletsrc".text = ''
    [Containments][2][Applets][3][Configuration][General]
    icon=roudix-logo
  '';

  # ── Hardware ───────────────────────────────────────────────────────────────
  hardware.bluetooth.enable = true;

  # ── Portals ────────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [ kdePackages.xdg-desktop-portal-kde ];
    xdgOpenUsePortal = true;
    config.common.default = "kde";
  };

  # ── Roudix branding : taskbar fix + wallpaper + icône menu ────────────────
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

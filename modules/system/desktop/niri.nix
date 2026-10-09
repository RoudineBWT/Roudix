{ config, lib, pkgs, inputs, username, ... }:
let
  isNiri     = config.roudix.desktop.type == "niri";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
  dp = import ../../desktop-pkgs.nix {
    inherit pkgs inputs;
    latest = config.roudix.desktop.latest;
  };
in
{
  config = lib.mkIf isNiri {
    # niri-unstable (latest main commit) through the niri-flake overlay.
    nixpkgs.overlays = [ inputs.niri.overlays.niri ];
    programs.niri.package = dp.niri;
    programs.niri.enable = true;

    # ── DMS greeter (when shell != noctalia) ───────────────────────────────
    programs.dms-greeter = lib.mkIf (!isNoctalia) {
      enable = true;
      compositor.name = "niri";
      configHome = "/home/${username}";
    };

    # ── DMS (shell) ─────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
    };

    # ── Noctalia greeter (when shell == noctalia) ──────────────────────────
    services.displayManager.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "--session niri";
      settings = {
        keyboard = {
          layout  = config.roudix.keyboardLayout;
          variant = config.roudix.keyboardVariant;
        };
      };
    };

    # ── Portals ───────────────────────────────────────────────────────────
    # Driven by roudix.desktopIntegration (gnome by default, kde as an
    # option for mostly-Qt/KDE setups on a non-KDE compositor).
    #
    # The niri-flake module adds xdg-desktop-portal-gnome and ships
    # niri-portals.conf (default = gnome;gtk, FileChooser/Access/
    # Notification = gtk) through configPackages. config.niri below
    # replaces that file entirely; mkForce keeps it that way even if
    # another module also defines xdg.portal.config.niri.
    # xdg-desktop-portal-gnome stays installed on purpose: niri implements
    # the Mutter ScreenCast/Screenshot D-Bus API, not KWin's, so those
    # interfaces must keep going through the gnome portal.
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs;
        if isKdeIntegration
        then [ kdePackages.xdg-desktop-portal-kde xdg-desktop-portal-gtk ]
        else [ xdg-desktop-portal-gtk xdg-desktop-portal-gnome ];
      config.niri =
        if isKdeIntegration
        then lib.mkForce {
          default = [ "kde" ];
          "org.freedesktop.impl.portal.ScreenCast"    = [ "gnome" ];
          "org.freedesktop.impl.portal.RemoteDesktop" = [ "gnome" ];
          "org.freedesktop.impl.portal.Screenshot"    = [ "gnome" ];
          # gtk portal only for Settings: dark/light follows dconf
          # (color-scheme) instead of the KDE portal's kdeglobals (= light).
          "org.freedesktop.impl.portal.Settings"      = [ "gtk" ];
        }
        else {
          default = [ "gnome" "gtk" ];
          "org.freedesktop.impl.portal.ScreenCast"    = [ "gnome" ];
          "org.freedesktop.impl.portal.RemoteDesktop" = [ "gnome" ];
        };
    };

    # ── Polkit ────────────────────────────────────────────────────────────
    systemd.user.services.polkit-agent = {
      description =
        if isKdeIntegration
        then "KDE Polkit authentication agent"
        else "GNOME Polkit authentication agent";
      wantedBy = [ "graphical-session.target" ];
      after    = [ "graphical-session.target" ];
      partOf   = [ "graphical-session.target" ];
      serviceConfig = {
        Type       = "simple";
        ExecStart  =
          if isKdeIntegration
          then "${pkgs.kdePackages.polkit-kde-agent-1}/libexec/polkit-kde-authentication-agent-1"
          else "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart    = "on-failure";
        RestartSec = "1s";
      };
    };

    # ── Keyring ───────────────────────────────────────────────────────────
    # ⚠ kde branch not tested in a real session. Known caveat: the
    # "greetd" PAM service doesn't substack "login" (nixpkgs#357201),
    # which has already broken kwallet auto-unlock for other greetd users
    # — see discourse.nixos.org "Auto-Unlock kwallet with greetd
    # login-manager". If the wallet stays locked after login, greetd's PAM
    # text will likely need "login" substacked by hand (as gdm.nix/
    # lightdm.nix already do for this case).
    # niri-flake's NixOS module hard-sets gnome-keyring.enable = true, so
    # the kde branch (false) needs mkForce to win over it.
    services.gnome.gnome-keyring.enable = lib.mkForce (!isKdeIntegration);
    security.pam.services.greetd.enableGnomeKeyring = !isKdeIntegration;
    security.pam.services.greetd.kwallet.enable = isKdeIntegration;

    environment.systemPackages = with pkgs;
      lib.optional (!isKdeIntegration) polkit_gnome
      ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
  };
}

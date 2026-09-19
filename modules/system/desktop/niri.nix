{ config, lib, pkgs, inputs, username, ... }:
let
  isNiri     = config.roudix.desktop.type == "niri";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
in
{
  config = lib.mkIf isNiri {
    # niri-unstable (latest main commit):
    nixpkgs.overlays = [ inputs.niri.overlays.niri ];
    programs.niri.package = pkgs.niri-unstable;
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
    programs.noctalia-greeter = lib.mkIf isNoctalia {
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
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs;
        if isKdeIntegration
        then [ kdePackages.xdg-desktop-portal-kde ]
        else [ xdg-desktop-portal-gtk xdg-desktop-portal-gnome ];
      config.niri =
        if isKdeIntegration
        then {
          default = [ "kde" ];
          "org.freedesktop.impl.portal.ScreenCast"    = [ "kde" ];
          "org.freedesktop.impl.portal.RemoteDesktop" = [ "kde" ];
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
    services.gnome.gnome-keyring.enable = !isKdeIntegration;
    security.pam.services.greetd.enableGnomeKeyring = !isKdeIntegration;
    security.pam.services.greetd.kwallet.enable = isKdeIntegration;

    environment.systemPackages = with pkgs;
      lib.optional (!isKdeIntegration) polkit_gnome
      ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
  };
}

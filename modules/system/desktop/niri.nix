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
    # Pour niri-unstable (dernier commit de main), décommenter ces 2 lignes :
    nixpkgs.overlays = [ inputs.niri.overlays.niri ];
    programs.niri.package = pkgs.niri-unstable;
    programs.niri.enable = true;

    # ── Greeter DMS (si shell != noctalia) ───────────────────────────────
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

    # ── Greeter Noctalia (si shell == noctalia) ──────────────────────────
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
    # Pilotés par roudix.desktopIntegration (gnome par défaut, kde en option
    # pour les setups surtout Qt/KDE sur un compositeur non-KDE).
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
    # ⚠ Branche kde pas testée en session réelle. Point de vigilance connu :
    # le service PAM "greetd" ne substack pas "login" (nixpkgs#357201), ce
    # qui a déjà cassé l'auto-unlock kwallet pour d'autres utilisateurs de
    # greetd — cf. discourse.nixos.org "Auto-Unlock kwallet with greetd
    # login-manager". Si le wallet reste verrouillé après un login, il
    # faudra probablement substack "login" à la main dans le texte PAM de
    # greetd (comme le font déjà gdm.nix/lightdm.nix pour ce cas).
    services.gnome.gnome-keyring.enable = !isKdeIntegration;
    security.pam.services.greetd.enableGnomeKeyring = !isKdeIntegration;
    security.pam.services.greetd.kwallet.enable = isKdeIntegration;

    environment.systemPackages = with pkgs;
      lib.optional (!isKdeIntegration) polkit_gnome
      ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
  };
}

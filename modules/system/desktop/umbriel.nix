{ config, lib, pkgs, inputs, username, ... }:
let
  isUmbriel  = config.roudix.desktop.type == "umbriel";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
in
{
  imports = [ inputs.umbriel.nixosModules.default ];

  config = lib.mkIf isUmbriel {
    # ── Compositeur ────────────────────────────────────────────────────
    # inputs.umbriel = { url = "github:noctalia-dev/umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    # inputs.umbriel-portal = { url = "github:noctalia-dev/xdg-desktop-portal-umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    nixpkgs.overlays = [
      inputs.umbriel.overlays.default
    ];

    programs.umbriel.enable = true;
    # programs.umbriel.package est déjà réglé par défaut par le module sur
    # inputs.umbriel.packages.${system}.default
    #
    # Le README d'Umbriel documente une option dédiée pour le portail :
    # elle configure xdg.portal ET installe la conf nécessaire au
    # ScreenCast/Screenshot toute seule (au lieu de le faire à la main
    # via xdg.portal.config.umbriel plus bas).
    programs.umbriel.portalPackage =
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default;

    # ── Greeter DMS (si shell != noctalia) ───────────────────────────────
    programs.dms-greeter = lib.mkIf (!isNoctalia) {
      enable = true;
      compositor.name = "umbriel";
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
      greeter-args = "start-umbriel";
      settings = {
        keyboard = {
          layout  = "us";
          variant = "intl";
        };
      };
    };

    # ── Portails ──────────────────────────────────────────────────────────
    # Le backend umbriel + sa conf (ScreenCast/Screenshot) sont maintenant
    # câblés par programs.umbriel.portalPackage ci-dessus. Ici on ne garde
    # que les portails de secours pour les file pickers GTK/GNOME.
    # ⚠ Pas testé en profondeur — à vérifier une fois en session que
    # portalPackage suffit bien et qu'il n'entre pas en conflit avec gtk/
    # gnome pour le default portal. Doc: https://github.com/noctalia-dev/xdg-desktop-portal-umbriel
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];
    };

    # ── Polkit ────────────────────────────────────────────────────────────
    systemd.user.services.polkit-gnome = {
      description = "GNOME Polkit authentication agent";
      wantedBy = [ "graphical-session.target" ];
      after    = [ "graphical-session.target" ];
      partOf   = [ "graphical-session.target" ];
      serviceConfig = {
        Type       = "simple";
        ExecStart  = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart    = "on-failure";
        RestartSec = "1s";
      };
    };

    # ── Keyring ───────────────────────────────────────────────────────────
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.greetd.enableGnomeKeyring = true;

    environment.systemPackages = with pkgs; [ polkit_gnome ];
  };
}

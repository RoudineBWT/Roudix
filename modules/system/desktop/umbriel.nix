{ config, lib, pkgs, inputs, username, ... }:
let
  isUmbriel  = config.roudix.desktop.type == "umbriel";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
in
{
  config = lib.mkIf isUmbriel {
    # ── Compositeur ────────────────────────────────────────────────────
    # inputs.umbriel = { url = "github:noctalia-dev/umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    # inputs.umbriel-portal = { url = "github:noctalia-dev/xdg-desktop-portal-umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    nixpkgs.overlays = [
      inputs.umbriel.overlays.default
      inputs.xdg-desktop-portal-umbriel.overlays.default
    ];

    imports = [ inputs.umbriel.nixosModules.default ];
    programs.umbriel.enable = true;
    # programs.umbriel.package est déjà réglé par défaut par le module sur
    # inputs.umbriel.packages.${system}.default

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
    # ⚠ xdg-desktop-portal-umbriel n'a pas de module NixOS officiel (juste
    # un package + overlay) : ajout manuel via extraPortals. Pas testé en
    # profondeur — à vérifier que le ScreenCast/Screenshot fonctionne
    # correctement une fois en session. Doc: https://github.com/noctalia-dev/xdg-desktop-portal-umbriel
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        xdg-desktop-portal-umbriel
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];
      config.umbriel = {
        default = [ "umbriel" "gtk" ];
        "org.freedesktop.impl.portal.ScreenCast" = [ "umbriel" ];
        "org.freedesktop.impl.portal.Screenshot" = [ "umbriel" ];
      };
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

{ config, lib, pkgs, inputs, username, ... }:
let
  isUmbriel = config.roudix.desktop.type == "umbriel";
  shellType = config.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
in
{
  config = lib.mkIf isUmbriel {
    # ── Umbriel compositor ──────────────────────────────────────────────
    # Umbriel s'active via le package (pas de module NixOS spécifique)
    # L'activation se fait via le greeter ou directement

    # ── Greeter ──────────────────────────────────────────────────────────
    # Noctalia greeter pour Umbriel (si shell = noctalia)
    programs.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "--session umbriel";  # ← Démarre Umbriel au lieu de Niri
      settings = {
        keyboard = {
          layout  = "us";
          variant = "intl";
        };
      };
    };

    # ── Portals ───────────────────────────────────────────────────────────
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];
      config.umbriel = {
        default = [ "umbriel" "gtk" "gnome" ];
        "org.freedesktop.impl.portal.ScreenCast" = [ "umbriel" ];
        "org.freedesktop.impl.portal.RemoteDesktop" = [ "umbriel" ];
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

    # ── Packages (fusionné) ──────────────────────────────────────────────
    environment.systemPackages = with pkgs; [
      # Umbriel et son portail
      inputs.umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
      # Polkit
      polkit_gnome
    ];
  };
}

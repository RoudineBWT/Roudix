{ inputs, pkgs, ... }:

{
  imports = [
    inputs.umbriel.nixosModules.default
  ];

  programs.umbriel.enable = true;

  # ─── Portals ───────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
      xdg-desktop-portal-gtk
      xdg-desktop-portal-gnome
    ];  # ← Il manquait ce ";"
    config.umbriel = {
      default = [ "umbriel" "gtk" "gnome" ];
      "org.freedesktop.impl.portal.ScreenCast" = [ "umbriel" ];
      "org.freedesktop.impl.portal.RemoteDesktop" = [ "umbriel" ];
    };
  };

  # ─── Keyring ───────────────────────────────────────────────────────────
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
}

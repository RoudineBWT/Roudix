{ pkgs, inputs, lib, ... }:
{
  # ── GNOME 50 from staging-next ───────────────────────────────────────────
  # Remove this overlay once GNOME 50 lands in nixpkgs-unstable
  nixpkgs.overlays = [
    (final: prev: {
      gnome = inputs.nixpkgsStaging.legacyPackages.${prev.system}.gnome;
    })
  ];

  # ── GNOME desktop ────────────────────────────────────────────────────────
  services.desktopManager.gnome.enable = true;

  # ── Packages to exclude from GNOME default install ───────────────────────
  environment.gnome.excludePackages = with pkgs; [
    tali
    iagno
    hitori
    atomix
    yelp
    geary
    xterm
    totem
    epiphany
    gnome-tour
    gnome-software
    gnome-contacts
    gnome-user-docs
    gnome-font-viewer
    gnome-music
  ];

  # ── Portals ─────────────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = [
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk
    ];
    config.common.default = "*";
  };
}

# umbriel.nix (système)
{ inputs, ... }:

{
  imports = [
    inputs.umbriel.nixosModules.default
  ];

  programs.umbriel.enable = true;

  # Portals
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs; [
        inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
        xdg-desktop-portal-gtk
        xdg-desktop-portal-gnome
      ];

  # Vos autres services système (comme gnome-keyring)
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
}

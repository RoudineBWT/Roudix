{
  description = "Roudix ISO — Live installer with roudix-installer (GTK4 + disko)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";
    roudix-installer.url = "path:./roudix-installer";
  };

  outputs = { self, nixpkgs, disko, roudix-installer }:
    let
      system = "x86_64-linux";
    in
    {
      nixosConfigurations.roudix-iso = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = {
          roudixBranding = nixpkgs.legacyPackages.${system}.callPackage ./pkgs/roudix-branding {};
          inherit roudix-installer disko;
        };
        modules = [
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-gnome.nix"
          "${nixpkgs}/nixos/modules/installer/cd-dvd/channel.nix"
          ./iso-configuration.nix
        ];
      };

      packages.x86_64-linux.iso =
        self.nixosConfigurations.roudix-iso.config.system.build.isoImage;
    };
}

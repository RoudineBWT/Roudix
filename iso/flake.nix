{
  description = "Roudix ISO — Live installer with Calamares";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: {
    nixosConfigurations.roudix-iso = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares.nix"
        ./iso-configuration.nix
      ];
    };

    packages.x86_64-linux.iso =
      self.nixosConfigurations.roudix-iso.config.system.build.isoImage;
  };
}

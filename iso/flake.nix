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
          # ./roudix-cfg est la copie du repo principal embarquée par le
          # rsync du workflow — pkgs/roudix-branding vit à la racine du
          # repo, pas sous iso/, d'où le chemin qui pointe dans roudix-cfg.
          roudixBranding = nixpkgs.legacyPackages.${system}.callPackage ./roudix-cfg/pkgs/roudix-branding {};
          # gnome.nix (importé ci-dessous) attend un arg "inputs" dans sa
          # signature même s'il ne s'en sert pas dans son corps — dummy
          # vide, on n'a pas besoin des inputs du flake principal ici.
          inputs = {};
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

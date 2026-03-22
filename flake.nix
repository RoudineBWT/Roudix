{
  description = "NixOS unstable — Niri + Noctalia + CachyOS kernel";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nixpkgs-stable = {
      url = "github:NixOS/nixpkgs/nixos-25.11";
    };

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    noctalia = {
      url = "github:noctalia-dev/noctalia-shell";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix-cachyos-kernel = {
      url = "github:xddxdd/nix-cachyos-kernel/release";
    };

    zen-browser = {
     url = "github:0xc000022070/zen-browser-flake";
     inputs.nixpkgs.follows = "nixpkgs";
    };

    glf-os = {
      url = "git+https://framagit.org/gaming-linux-fr/glf-os/glf-os";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    spicetify-nix = {
      url = "github:Gerg-L/spicetify-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ { self, nixpkgs, home-manager, nix-cachyos-kernel, zen-browser, noctalia, glf-os, spicetify-nix, ... }:
  let
    username = "roudine"; # ← Change your username here
  in
  {
    nixosConfigurations.roudix = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs = { inherit inputs username; };
      modules = [
        ./configuration.nix
        ./niri.nix
        home-manager.nixosModules.home-manager
        {
          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.extraSpecialArgs = { inherit inputs username; };
          home-manager.users.${username} = import ./home.nix;
        }
      ];
    };
  };
}

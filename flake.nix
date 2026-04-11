{
  description = "NixOS unstable — Niri + Noctalia + CachyOS Kernel";

  # ── Binary caches ───────────────────────────────────────
  nixConfig = {
    extra-substituters = [
      "https://attic.xuyh0120.win/lantian"
      "https://cache.garnix.io"
      "https://noctalia.cachix.org"
    ];
    extra-trusted-public-keys = [
      "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc="
      "cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
    ];
  };


  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-25.11";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    noctalia = {
      url = "github:noctalia-dev/noctalia-shell";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.noctalia-qs.follows = "noctalia-qs";
    };

    noctalia-qs = {
      url = "github:noctalia-dev/noctalia-qs";
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

    millennium = {
      url = "github:SteamClientHomebrew/Millennium?dir=packages/nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    helium = {
      url = "github:AlvaroParker/helium-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix-flatpak = {
      url = "github:gmodena/nix-flatpak";
    };

    plasma-manager = {
      url = "github:nix-community/plasma-manager";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };
  };

  outputs = inputs @ { self, nixpkgs, home-manager, nix-cachyos-kernel, zen-browser, noctalia, noctalia-qs, glf-os, spicetify-nix, millennium, helium, nix-flatpak, plasma-manager, ... }:
  let
  # ← username is defined in hosts/roudix/username.nix (gitignored)
  # Create it with: echo '"yourusername"' > hosts/roudix/username.nix
    username = import ./hosts/roudix/username.nix;
    roudixSwitcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-switcher {};
    roudixBranding  = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-branding {};
    specialArgs = { inherit inputs username roudixSwitcher roudixBranding; dotfiles = self + /dotfiles; };
  in
  {
    # ── Main desktop configuration ───────────────────────────────────────
    # Use 'roudix-switch <de>' to change desktop environment
    nixosConfigurations.roudix = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs = specialArgs;
      modules = [
        nix-flatpak.nixosModules.nix-flatpak
        ./hosts/roudix/configuration.nix
        ./version.nix
        ./branding.nix
        home-manager.nixosModules.home-manager
        {
          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.backupFileExtension = "bak";
          home-manager.extraSpecialArgs = specialArgs;
          home-manager.users.${username} = { ... }: {
            imports = [
              ./home/common.nix
              ./home/niri.nix
              ./home/hyprland.nix
              ./home/kde.nix
              ./home/local.nix
            ];
          };
        }
      ];
    };
  };
}

{
  description = "Roudix";

  # ── Binary caches ───────────────────────────────────────
  nixConfig = {
    extra-substituters = [
      "https://attic.xuyh0120.win/lantian"
      "https://noctalia.cachix.org"
      "https://prismlauncher.cachix.org"
      "https://nix-community.cachix.org"
      "https://roudix.cachix.org"
      "https://nix-cache.tokidoki.dev/tokidoki"
      "https://nyx-cache.chaotic.cx/"
      "https://niri-epireyn.cachix.org"
      "https://hyprland.cachix.org"
    ];
    extra-trusted-public-keys = [
      "niri-epireyn.cachix.org-1:tlVyFN7CtsDT+ZcLPS+ekFWeT1X6X4OqvWqbBMyIzFA="
      "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "prismlauncher.cachix.org-1:9/n/FGyABA2jLUVfY+DEp4hKds/rwO+SCOtbOkDzd+c="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCUSeBw="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
      "tokidoki:MD4VWt3kK8Fmz3jkiGoNRJIW31/QAm7l1Dcgz2Xa4hk="
      "nyx-cache.chaotic.cx:dJxTrgMC3V3cFfyIiBQDQorG6k1LsqurH/srpMSq7qk="
      "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
    ];
  };


  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-26.05";

    chaotic.url = "github:chaotic-cx/nyx/nyxpkgs-unstable";

    niri = {
      url = "github:epireyn/niri-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    hyprland = {
      url = "github:hyprwm/hyprnix";
      # Pas de nixpkgs.follows ici : le cachix hyprland.cachix.org cache des
      # builds faites avec LEUR nixpkgs épinglé. Si on force notre
      # nixos-unstable, les hash de dérivation divergent → cache miss →
      # recompilation locale de Hyprland + deps (mesa, ffmpeg...).
    };

    hyprland-modules = {
      url = "github:hyprwm/Hyprland";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    hyprland-plugins = {
      url = "github:hyprwm/hyprland-plugins";
      # Verrouille exactement la même révision Hyprland que ci-dessus, pour
      # éviter le mismatch d'ABI qu'on aurait avec pkgs.hyprlandPlugins.
      inputs.hyprland.follows = "hyprland";
    };

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    noctalia = {
      url = "github:noctalia-dev/noctalia/cachix";
    };

    noctalia-greeter = {
      url = "github:noctalia-dev/noctalia-greeter";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    umbriel = {
      # github: ne supporte pas l'attribut submodules — umbriel a vendored
      # SceneFX en submodule git (cf. "Removed input umbriel/scenefx" dans le
      # lock), il faut le fetcher git générique pour que ça checkout.
      url = "git+https://github.com/noctalia-dev/umbriel";
    };

    xdg-desktop-portal-umbriel = {
      url = "github:noctalia-dev/xdg-desktop-portal-umbriel";
    };

    caelestia-shell = {
         url = "github:caelestia-dots/shell";
         inputs.nixpkgs.follows = "nixpkgs";
       };

    dms ={
        url = "github:AvengeMedia/DankMaterialShell";
        inputs.nixpkgs.follows = "nixpkgs";
  };

  dank-greeter = {
    url = "github:AvengeMedia/dank-greeter";
    inputs.nixpkgs.follows = "nixpkgs";
  };

    nix-cachyos-kernel = {
      url = "github:xddxdd/nix-cachyos-kernel/release";
    };

    zen-browser = {
      url = "github:0xc000022070/zen-browser-flake";
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
      url = "github:x13-me/helium-nix/rolling";
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

    brave-previews ={
    url = "github:roudinebwt/brave-preview";
    inputs.nixpkgs.follows = "nixpkgs";
    };

    roudix-caches = {
      url = "github:RoudineBWT/Roudix-caches";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nix-gaming-edge = {
       url = "github:powerofthe69/nix-gaming-edge";
       inputs.nixpkgs.follows = "nixpkgs";
    };
    mango = {
        url = "github:DreamMaoMao/mango";
        inputs.nixpkgs.follows = "nixpkgs";
      };
  };

  outputs = inputs @ {
    self,
    nixpkgs,
    chaotic,
    niri,
    hyprland,
    hyprland-modules,
    hyprland-plugins,
    home-manager,
    nix-cachyos-kernel,
    zen-browser,
    noctalia,
    noctalia-greeter,
    caelestia-shell,
    dms,
    dank-greeter,
    spicetify-nix,
    millennium,
    helium,
    nix-flatpak,
    plasma-manager,
    brave-previews,
    roudix-caches,
    nix-gaming-edge,
    mango,
    umbriel,
    xdg-desktop-portal-umbriel,
    ... }:
  let
  # ← username is defined in hosts/roudix/username.nix (gitignored)
  # Create it with: echo '"yourusername"' > hosts/roudix/username.nix
    username = import ./hosts/roudix/username.nix;
    roudixSwitcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-switcher {};
    roudixBranding  = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-branding {};
    roudix-kernel-switcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-kernel-switcher {};
    roudix-scheduler-switcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-scheduler-switcher {
      scxctl = roudix-caches.packages.x86_64-linux.scxctl;
    };
    specialArgs = { inherit inputs username roudixSwitcher roudixBranding roudix-kernel-switcher roudix-scheduler-switcher ; dotfiles = self + /dotfiles; };
  in
  {
    # ── Main desktop configuration ───────────────────────────────────────
    # Use 'roudix-switch <de>' to change desktop environment
    nixosConfigurations.roudix = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs = specialArgs;
      modules = [
        niri.nixosModules.niri
        inputs.hyprland-modules.nixosModules.default
        inputs.dms.nixosModules.dank-material-shell
        inputs.noctalia-greeter.nixosModules.default
        inputs.dank-greeter.nixosModules.default
        nix-flatpak.nixosModules.nix-flatpak
        inputs.mango.nixosModules.mango
        chaotic.nixosModules.default
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
              ./home/umbriel.nix
              ./home/hyprland.nix
              ./home/mangowc.nix
              ./home/kde.nix
              ./home/gnome.nix
              ./home/local.nix
              ./home/shell-modules.nix
            ];
          };
        }
      ];
    };
  };
}

{
  description = "Roudix";

  # ── Binary caches ───────────────────────────────────────
  nixConfig = {
    extra-substituters = [
      "https://cache.lantian.pub/lantian"
      "https://noctalia.cachix.org"
      "https://prismlauncher.cachix.org"
      "https://nix-community.cachix.org"
      "https://roudix.cachix.org"
      "https://nix-cache.tokidoki.dev/tokidoki"
      "https://nyx-cache.chaotic.cx/"
      "https://niri-epireyn.cachix.org"
      "https://hyprland.cachix.org"
      "https://umbriel.cachix.org"
    ];
    extra-trusted-public-keys = [
      "niri-epireyn.cachix.org-1:tlVyFN7CtsDT+ZcLPS+ekFWeT1X6X4OqvWqbBMyIzFA="
      "lantian:WVGO7vsRMSEN+h7Lp7kv6SAmrkEXgUGbbXm7jMDjBuQ="
      "noctalia.cachix.org-1:pCOR47nnMEo5thcxNDtzWpOxNFQsBRglJzxWPp3dkU4="
      "prismlauncher.cachix.org-1:9/n/FGyABA2jLUVfY+DEp4hKds/rwO+SCOtbOkDzd+c="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "roudix.cachix.org-1:h5EnhsXw4Mr6pLUpZIalE8SlfH1kKXgvPFvl+yrTAaQ="
      "tokidoki:MD4VWt3kK8Fmz3jkiGoNRJIW31/QAm7l1Dcgz2Xa4hk="
      "nyx-cache.chaotic.cx:dJxTrgMC3V3cFfyIiBQDQorG6k1LsqurH/srpMSq7qk="
      "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
      "umbriel.cachix.org-1:JfNq/2yg2S6D6z4Z2dVSZrZlDPQTKtexB6GAVLD98nw="
    ];
  };


  inputs = {
    # AppStream catalog (icons, categories, screenshots) for nixpkgs — used by roudix-store
    nixos-appstream-data = {
      url = "github:vlinkz/nixos-appstream-data";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # Fresher nixpkgs, used ONLY for the nixpkgs-sourced kernels (zen,
    # nixpkgs-*, xanmod-*) when hardware.myKernelSource is set to "master"
    # or "staging-next" (see modules/system/boot/kernel.nix). The rest of the
    # system keeps following `nixpkgs` above — no `follows` here on purpose.
    nixpkgs-master.url = "github:NixOS/nixpkgs/master";
    nixpkgs-staging-next.url = "github:NixOS/nixpkgs/staging-next";

    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-26.05";

    chaotic.url = "github:chaotic-cx/nyx/nyxpkgs-unstable";

    niri = {
      url = "github:epireyn/niri-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    noctalia = {
      url = "github:noctalia-dev/noctalia/cachix";
      #inputs.nixpkgs.follows = "nixpkgs";
    };

    noctalia-greeter = {
      url = "github:noctalia-dev/noctalia-greeter";
      inputs.nixpkgs.follows = "nixpkgs";
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

    # xddxdd CachyOS kernels (AMD/Intel/VM hosts). `release` = last build
    # present in the binary cache. No `nixpkgs.follows` on purpose: the
    # `pinned` overlay must use the nixpkgs revision the kernels were built
    # with, otherwise cache misses / patch-vs-kernel version mismatches.
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

    # Only pkgs/decky-loader is used from this (see gamescope-session.nix),
    # never its overlay/modules, which redefine gamescope/steam/mesa. Safe to
    # follow our nixpkgs: Jovian's own flake pins nixos-unstable too, same
    # channel as ours, so this is not the bun-style fixed-output-derivation
    # mismatch millennium has above. `nix flake update jovian` bumps it, no
    # sha to hand-maintain like GLF-OS' fetchTarball does.
    jovian = {
      url = "github:Jovian-Experiments/Jovian-NixOS";
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
       url = "github:powerofthe69/nix-gaming-edge/nightly";
       inputs.nixpkgs.follows = "nixpkgs";
    };
    betterbird-nix = {
      url = "github:TheAnachronism/betterbird-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    mango = {
        url = "github:mangowm/mango";
        inputs.nixpkgs.follows = "nixpkgs";
      };

      umbriel = {
        url = "github:noctalia-dev/umbriel/cachix";
      };

    # Sonora — native (Rust/GPUI) music client: Spotify, YouTube Music, Apple
    # Music, Deezer, Subsonic... One of the roudix.musicPlayer choices. No
    # `nixpkgs.follows` on purpose: its default package is a prebuilt release
    # binary, and its source build pins its own Rust toolchain.
    sonora ={
      url = "github:sonorahq/sonora";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ {
    self,
    nixpkgs,
    chaotic,
    niri,
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
    ... }:
  let
    roudixSwitcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-switcher {};
    roudixBranding  = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-branding {};
    roudix-kernel-switcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-kernel-switcher {};
    roudix-hw-sync = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-hw-sync {};
    roudix-firewall = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-firewall {};
    roudix-disk = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-disk {};
    roudix-scheduler-switcher = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-scheduler-switcher {
      scxctl = roudix-caches.packages.x86_64-linux.scxctl;
    };
    roudixWelcome = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-welcome {};
    roudixConfig = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-config {};
    roudixStore = nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/roudix-store {
      nixos-appstream-data = inputs.nixos-appstream-data.packages.x86_64-linux.appstream-data;
    };

    # username is NOT here anymore: it's per-host, read from
    # hosts/<hostName>/username.nix (gitignored). Base args shared by
    # every host — each mkHost call adds its own `username`.
    baseSpecialArgs = { inherit inputs roudixSwitcher roudixBranding roudix-kernel-switcher roudix-hw-sync roudix-firewall roudix-disk roudix-scheduler-switcher roudixWelcome roudixConfig roudixStore; dotfiles = self + /dotfiles; };

    # ── Host builder ──────────────────────────────────────────────────────
    # One host = one directory under ./hosts/<hostName>/ containing:
    #   configuration.nix          (tracked — networking.hostName + option
    #                                overrides for this machine)
    #   local.nix                  (gitignored — personal tweaks, optional)
    #   username.nix                (gitignored — create with:
    #                                echo '"yourusername"' > hosts/<hostName>/username.nix)
    #   hardware-configuration.nix  (gitignored — from nixos-generate-config)
    # `nixosConfigurations.<hostName>` is what roudix.autoupdate.flakeAttr
    # must match on that machine (see modules/system/nix/autoupdate.nix).
    mkHost = hostName:
      let
        username = import (./hosts + "/${hostName}/username.nix");
        specialArgs = baseSpecialArgs // { inherit username; };
      in
      nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        inherit specialArgs;
        modules = [
          niri.nixosModules.niri
          inputs.dms.nixosModules.dank-material-shell
          inputs.noctalia-greeter.nixosModules.default
          inputs.dank-greeter.nixosModules.default
          nix-flatpak.nixosModules.nix-flatpak
          inputs.mango.nixosModules.mango
          chaotic.nixosModules.default
          (./hosts + "/${hostName}/configuration.nix")
          ./version.nix
          ./branding.nix
          home-manager.nixosModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.backupFileExtension = "bak";
            home-manager.extraSpecialArgs = specialArgs;
            # per-user Flatpaks (roudix.store.flatpaksUser / flatpaksUserBeta)
            home-manager.sharedModules = [ nix-flatpak.homeManagerModules.nix-flatpak ];
            home-manager.users.${username} = { lib, ... }: {
              imports = [
                ./modules/home/common.nix
                ./modules/home/desktop
              ] ++ lib.optional (builtins.pathExists ./modules/home/local.nix) ./modules/home/local.nix;
            };
          }
        ];
      };
  in
  {
    # ── Every directory under ./hosts/ becomes a nixosConfigurations
    # attribute automatically — add a host by creating hosts/<name>/, no
    # edit to this file needed. (Use 'roudix-switch <de>' to change desktop
    # environment on the machine you're on.)
    nixosConfigurations =
      let
        hostDirs = builtins.readDir ./hosts;
        hostNames = builtins.attrNames (nixpkgs.lib.filterAttrs (_: type: type == "directory") hostDirs);
      in
      nixpkgs.lib.genAttrs hostNames mkHost;

    # `nix develop` — the tools behind `just ci` (and the installer's gettext
    # workflow), pinned by this flake, so contributors install nothing by hand.
    devShells.x86_64-linux.default =
      let pkgs = nixpkgs.legacyPackages.x86_64-linux;
      in pkgs.mkShell {
        packages = with pkgs; [
          just          # task runner: `just` lists the tasks
          git
          python3
          ruff          # `just py`
          statix        # `just lint`
          deadnix       # `just lint`
          shellcheck    # installer + scripts
          gettext       # xgettext / msgmerge / msgfmt: `just i18n-*`
        ];
        shellHook = ''
          echo "Roudix dev shell — type 'just' to list the tasks"
        '';
      };
  };
}

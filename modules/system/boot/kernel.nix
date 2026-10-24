{ config, pkgs, lib, inputs, ... }:
{
  options.hardware.myKernel = lib.mkOption {
    type = lib.types.enum [
      # Zen + XanMod + LTS/latest/testing (nixpkgs, not CachyOS)
      "zen"
      "nixpkgs-lts"
      "nixpkgs-latest"
      "nixpkgs-testing"
      "xanmod-lts"
      "xanmod-latest"
      # Latest
      "cachyos-latest"
      "cachyos-latest-v2"
      "cachyos-latest-v3"
      "cachyos-latest-v4"
      "cachyos-latest-zen4"
      "cachyos-latest-lto"
      "cachyos-latest-lto-v2"
      "cachyos-latest-lto-v3"
      "cachyos-latest-lto-v4"
      "cachyos-latest-lto-zen4"
      # LTS
      "cachyos-lts"
      "cachyos-lts-v2"
      "cachyos-lts-v3"
      "cachyos-lts-v4"
      "cachyos-lts-zen4"
      "cachyos-lts-lto"
      "cachyos-lts-lto-v2"
      "cachyos-lts-lto-v3"
      "cachyos-lts-lto-v4"
      "cachyos-lts-lto-zen4"
      # Variants
      "cachyos-bmq"
      "cachyos-bmq-lto"
      "cachyos-bore"
      "cachyos-bore-lto"
      "cachyos-deckify"
      "cachyos-deckify-lto"
      "cachyos-eevdf"
      "cachyos-eevdf-lto"
      "cachyos-hardened"
      "cachyos-hardened-lto"
      "cachyos-rc"
      "cachyos-rc-lto"
      "cachyos-rt-bore"
      "cachyos-rt-bore-lto"
      "cachyos-server"
      "cachyos-server-lto"
    ];
    default = "cachyos-latest-v3";
    description = "CachyOS kernel variant (xddxdd/nix-cachyos-kernel) — used when hardware.myGpu != \"nvidia\". \"zen\" maps to pkgs.linuxPackages_zen, \"nixpkgs-lts\" to pkgs.linuxPackages (nixpkgs default LTS), \"nixpkgs-latest\" to pkgs.linuxPackages_latest, \"nixpkgs-testing\" to pkgs.linuxPackages_testing (linux_testing — RC/mainline candidate kernel), \"xanmod-lts\" to pkgs.linuxPackages_xanmod (XanMod LTS branch) and \"xanmod-latest\" to pkgs.linuxPackages_xanmod_latest (XanMod main branch) — all outside the xddxdd overlay. These nixpkgs-sourced kernels can be taken from a fresher nixpkgs, see hardware.myKernelSource.";
  };

  # Chaotic-Nyx's variant set is much smaller (no x86_64-v2/v3/v4/zen4,
  # no separate LTO per family like xddxdd). Only used on nvidia hosts.
  options.hardware.myKernelChaotic = lib.mkOption {
    type = lib.types.enum [
      # Zen + XanMod + LTS/latest/testing (nixpkgs): nixpkgs kernel + nvidia
      # module built locally via nvidiaPackages.stable (no Chaotic cache for
      # these)
      "zen"
      "nixpkgs-lts"
      "nixpkgs-latest"
      "nixpkgs-testing"
      "xanmod-lts"
      "xanmod-latest"
      "cachyos"        # Chaotic-Nyx default, LTO+BORE
      "cachyos-lts"
      "cachyos-server"
      "cachyos-hardened"
    ];
    default = "cachyos";
    description = "Chaotic-Nyx kernel variant — used only when hardware.myGpu == \"nvidia\", to benefit from the precompiled nvidia_cachyos cache. \"zen\", \"nixpkgs-lts\", \"nixpkgs-latest\", \"nixpkgs-testing\", \"xanmod-lts\" and \"xanmod-latest\" fall outside this cache: nixpkgs kernel (linuxPackages_zen / linuxPackages / linuxPackages_latest / linuxPackages_testing / linuxPackages_xanmod / linuxPackages_xanmod_latest) + nvidia module recompiled locally (see nvidia.nix)";
  };

  options.hardware.myKernelSource = lib.mkOption {
    type = lib.types.enum [ "nixpkgs" "master" "staging-next" ];
    default = "nixpkgs";
    description = ''
      Which nixpkgs the nixpkgs-sourced kernels come from: "zen",
      "nixpkgs-lts", "nixpkgs-latest", "nixpkgs-testing", "xanmod-lts" and
      "xanmod-latest" (hardware.myKernel, or hardware.myKernelChaotic on
      nvidia hosts). Only the kernel (and the out-of-tree modules built
      against it, e.g. the nvidia module) uses this nixpkgs — the rest of the
      system stays on the main `nixpkgs` input.

      "nixpkgs"      the main input (nixos-unstable): kernels are cached on
                     cache.nixos.org once a channel has passed, but land a
                     few days after the upstream bump. Default.
      "master"       NixOS/nixpkgs master: gets kernel bumps as soon as they
                     are merged, without the channel delay.
      "staging-next" NixOS/nixpkgs staging-next: same idea, but this branch
                     also carries toolchain/stdenv changes in flight, so the
                     kernel is more likely to be rebuilt locally (long) and
                     to break.

      A kernel taken from "master" / "staging-next" is not guaranteed to be
      in a binary cache yet: expect a local kernel (and nvidia module) build
      when the exact commit hasn't been built by Hydra. Has no effect on the
      cachyos-* kernels (served by Chaotic-Nyx / xddxdd, which bring their own
      nixpkgs) — a warning is emitted in that case.
    '';
  };

  config =
    let
      source = config.hardware.myKernelSource;
      activeVariant =
        if config.hardware.myGpu == "nvidia"
        then config.hardware.myKernelChaotic
        else config.hardware.myKernel;

      # nixpkgs the nixpkgs-sourced kernels are taken from. For anything but
      # the main input, a second, separate instance of nixpkgs is imported
      # with the same `nixpkgs.config` (allowUnfree is needed by the nvidia
      # module built against the kernel). Selecting inside the attrset keeps
      # the unselected inputs unevaluated.
      kernelPkgs =
        if source == "nixpkgs" then pkgs
        else
          import
            ({
              master = inputs.nixpkgs-master;
              staging-next = inputs.nixpkgs-staging-next;
            }.${source})
            {
              system = pkgs.stdenv.hostPlatform.system;
              config = config.nixpkgs.config;
            };

      # Every kernel that comes from nixpkgs (as opposed to the cachyos-*
      # ones). Single source of truth for both the AMD/Intel and the nvidia
      # branches below. Lazy: only the selected entry is evaluated.
      nixpkgsKernels = {
        "zen"             = kernelPkgs.linuxPackages_zen;
        # default LTS
        "nixpkgs-lts"     = kernelPkgs.linuxPackages;
        # latest stable mainline
        "nixpkgs-latest"  = kernelPkgs.linuxPackages_latest;
        # linux_testing — RC/mainline candidate kernel
        "nixpkgs-testing" = kernelPkgs.linuxPackages_testing;
        # XanMod, LTS branch (linux_xanmod)
        "xanmod-lts"      = kernelPkgs.linuxPackages_xanmod;
        # XanMod, main branch (linux_xanmod_latest)
        "xanmod-latest"   = kernelPkgs.linuxPackages_xanmod_latest;
      };
    in
    lib.mkMerge [
    # hardware.myKernelSource only applies to nixpkgs kernels
    {
      warnings = lib.optional (source != "nixpkgs" && lib.hasPrefix "cachyos" activeVariant) ''
        hardware.myKernelSource = "${source}" has no effect with the
        "${activeVariant}" kernel: only zen, nixpkgs-* and xanmod-* kernels
        are taken from it.
      '';
    }

    # Workaround for a nixpkgs regression (kernel build changes of 2026-10-11):
    # nixpkgs now keeps System.map in kernel.dev, so the kernel's depmod.sh no
    # longer skips depmod when an out-of-tree module is installed. Each such
    # package (seen with v4l2loopback) then ships its own
    # lib/modules/<ver>/modules.alias, ... and pkgs.aggregateModules (a
    # buildEnv) aborts with "two given paths contain a conflicting subpath".
    # The aggregator deletes and regenerates every modules.* file in its
    # postBuild, so letting buildEnv ignore the collision is harmless.
    # Affects every kernel (nixos-unstable included), not just master /
    # staging-next. Drop this once nixpkgs fixes it upstream.
    {
      nixpkgs.overlays = [
        (_final: prev: {
          aggregateModules =
            modules:
            (prev.aggregateModules modules).override {
              buildEnv = args: prev.buildEnv (args // { ignoreCollisions = true; });
            };
        })
      ];
    }

    # Common sysctl, independent of the chosen GPU/kernel
    {
      # Sysctl values from 70-cachyos-settings.conf (cachyos-settings package)
      # https://github.com/CachyOS/CachyOS-Settings/blob/master/usr/lib/sysctl.d/70-cachyos-settings.conf
      boot.kernel.sysctl = {
        # Reduces the kernel's tendency to reclaim the VFS cache (dentries/inodes) vs the default (100)
        "vm.vfs_cache_pressure" = 50;

        # Threshold (bytes) above which a process writing to disk starts flushing its own dirty data
        "vm.dirty_bytes" = 268435456; # 256 MiB

        # Consecutive pages read at once from swap (default 3); 0 recommended for SSD/ZRAM swap
        "vm.page-cluster" = 0;

        # Threshold (bytes) above which kernel flusher threads start writing in the background
        "vm.dirty_background_bytes" = 67108864; # 64 MiB

        # Interval (centiseconds) between flusher thread wakeups (default 500)
        "vm.dirty_writeback_centisecs" = 1500;

        # Disables the NMI watchdog: faster boot/shutdown, slightly lower power draw
        "kernel.nmi_watchdog" = 0;

        # Allows non-root users to create user namespaces (unprivileged containers)
        "kernel.unprivileged_userns_clone" = 1;

        # Hides kernel messages on the console
        "kernel.printk" = "3 3 3 3";

        # Restricts access to kernel pointers exposed in /proc
        "kernel.kptr_restrict" = 2;

        # Increases the network receive queue size, avoids packet loss under load
        "net.core.netdev_max_backlog" = 4096;

        # Increases the max number of file handles / inode cache
        "fs.file-max" = 2097152;

        # Max memory maps per process (needed by some Proton/DayZ games, etc.)
        "vm.max_map_count" = 16777216;

        # inotify limits (file watching), needed by IDEs, Steam, sync tools, etc.
        "fs.inotify.max_user_watches" = 524288;
        "fs.inotify.max_user_instances" = 1024;

        # Default TCP keepalive interval (seconds)
        "net.ipv4.tcp_keepalive_time" = 120;
      };
    }

    # AMD / Intel / VM branch: xddxdd kernel (nix-cachyos-kernel), no cache
    # concern from the GPU side (no nvidia module to build).
    #
    # The `pinned` overlay builds against the exact nixpkgs revision the
    # kernels were cached with (binary cache: cache.lantian.pub/lantian, see
    # flake.nix / modules/system/nix/*.nix) and exposes them as
    # pkgs.cachyosKernels.*. We use its `linuxPackages-*` entries (kernel +
    # matching module set, incl. the LTO out-of-tree-module fix) rather than
    # wrapping the bare kernel with linuxKernel.packagesFor ourselves.
    # NOTE: the cache must be active BEFORE the first build with this kernel —
    # apply the cache settings once (nixos-rebuild switch) first.
    (lib.mkIf (config.hardware.myGpu != "nvidia") (
      let
        variant = config.hardware.myKernel;
        cachy = name: pkgs.cachyosKernels."linuxPackages-${name}";

        # hardware.myKernel value -> attribute of nix-cachyos-kernel.
        # Lazy: only the selected entry is evaluated. Upstream spells the
        # CPU-level suffixes "x86_64-vN" where we use "vN".
        # (v2 and a few -lto variants are not in the binary cache upstream.)
        xddxddKernels = {
          # Latest
          "cachyos-latest"          = cachy "cachyos-latest";
          "cachyos-latest-v2"       = cachy "cachyos-latest-x86_64-v2";
          "cachyos-latest-v3"       = cachy "cachyos-latest-x86_64-v3";
          "cachyos-latest-v4"       = cachy "cachyos-latest-x86_64-v4";
          "cachyos-latest-zen4"     = cachy "cachyos-latest-zen4";
          "cachyos-latest-lto"      = cachy "cachyos-latest-lto";
          "cachyos-latest-lto-v2"   = cachy "cachyos-latest-lto-x86_64-v2";
          "cachyos-latest-lto-v3"   = cachy "cachyos-latest-lto-x86_64-v3";
          "cachyos-latest-lto-v4"   = cachy "cachyos-latest-lto-x86_64-v4";
          "cachyos-latest-lto-zen4" = cachy "cachyos-latest-lto-zen4";
          # LTS
          "cachyos-lts"             = cachy "cachyos-lts";
          "cachyos-lts-v2"          = cachy "cachyos-lts-x86_64-v2";
          "cachyos-lts-v3"          = cachy "cachyos-lts-x86_64-v3";
          "cachyos-lts-v4"          = cachy "cachyos-lts-x86_64-v4";
          "cachyos-lts-zen4"        = cachy "cachyos-lts-zen4";
          "cachyos-lts-lto"         = cachy "cachyos-lts-lto";
          "cachyos-lts-lto-v2"      = cachy "cachyos-lts-lto-x86_64-v2";
          "cachyos-lts-lto-v3"      = cachy "cachyos-lts-lto-x86_64-v3";
          "cachyos-lts-lto-v4"      = cachy "cachyos-lts-lto-x86_64-v4";
          "cachyos-lts-lto-zen4"    = cachy "cachyos-lts-lto-zen4";
          # Variants
          "cachyos-bmq"             = cachy "cachyos-bmq";
          "cachyos-bmq-lto"         = cachy "cachyos-bmq-lto";
          "cachyos-bore"            = cachy "cachyos-bore";
          "cachyos-bore-lto"        = cachy "cachyos-bore-lto";
          "cachyos-deckify"         = cachy "cachyos-deckify";
          "cachyos-deckify-lto"     = cachy "cachyos-deckify-lto";
          "cachyos-eevdf"           = cachy "cachyos-eevdf";
          "cachyos-eevdf-lto"       = cachy "cachyos-eevdf-lto";
          "cachyos-hardened"        = cachy "cachyos-hardened";
          "cachyos-hardened-lto"    = cachy "cachyos-hardened-lto";
          "cachyos-rc"              = cachy "cachyos-rc";
          "cachyos-rc-lto"          = cachy "cachyos-rc-lto";
          "cachyos-rt-bore"         = cachy "cachyos-rt-bore";
          "cachyos-rt-bore-lto"     = cachy "cachyos-rt-bore-lto";
          "cachyos-server"          = cachy "cachyos-server";
          "cachyos-server-lto"      = cachy "cachyos-server-lto";
        };
      in
      {
        nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];

        boot.kernelPackages = nixpkgsKernels.${variant} or xddxddKernels.${variant};
      }
    ))

    # Nvidia branch: Chaotic-Nyx kernel, to get the precompiled
    # nvidia_cachyos (chaotic.nixosModules.default is already imported
    # globally in flake.nix, no need to re-import here — its binary cache
    # is therefore active whether or not the GPU is nvidia)
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      # zen / nixpkgs-* / xanmod-* come from nixpkgs (see nixpkgsKernels);
      # the associated nvidia module (nvidiaPackages.stable, built locally)
      # is selected in nvidia.nix. Everything else is a Chaotic-Nyx kernel
      # shipping the precompiled nvidia_cachyos.
      boot.kernelPackages =
        let
          kernels = {
            "cachyos"          = pkgs.linuxPackages_cachyos;
            "cachyos-lts"      = pkgs.linuxPackages_cachyos-lts;
            "cachyos-server"   = pkgs.linuxPackages_cachyos-server;
            "cachyos-hardened" = pkgs.linuxPackages_cachyos-hardened;
          };
          variant = config.hardware.myKernelChaotic;
        in
        nixpkgsKernels.${variant} or kernels.${variant};
    })
  ];
}

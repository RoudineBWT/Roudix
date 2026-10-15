{ config, pkgs, lib, inputs, ... }:
{
  options.hardware.myKernel = lib.mkOption {
    type = lib.types.enum [
      # Zen + LTS/latest/testing (nixpkgs, not CachyOS)
      "zen"
      "nixpkgs-lts"
      "nixpkgs-latest"
      "nixpkgs-testing"
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
    description = "CachyOS kernel variant — used when hardware.myGpu != \"nvidia\". TEMPORARY: xddxdd is disabled, cachyos-* values are served by Chaotic-Nyx (closest family: default/lts/server/hardened). \"zen\" maps to pkgs.linuxPackages_zen, \"nixpkgs-lts\" to pkgs.linuxPackages (nixpkgs default LTS), \"nixpkgs-latest\" to pkgs.linuxPackages_latest, \"nixpkgs-testing\" to pkgs.linuxPackages_testing (linux_testing — RC/mainline candidate kernel) — all outside the xddxdd overlay.";
  };

  # Chaotic-Nyx's variant set is much smaller (no x86_64-v2/v3/v4/zen4,
  # no separate LTO per family like xddxdd).
  options.hardware.myKernelChaotic = lib.mkOption {
    type = lib.types.enum [
      # Zen + LTS/latest/testing (nixpkgs): nixpkgs kernel + nvidia module
      # built locally via nvidiaPackages.stable (no Chaotic cache for these)
      "zen"
      "nixpkgs-lts"
      "nixpkgs-latest"
      "nixpkgs-testing"
      "cachyos"        # Chaotic-Nyx default, LTO+BORE
      "cachyos-lts"
      "cachyos-server"
      "cachyos-hardened"
    ];
    default = "cachyos";
    description = "Chaotic-Nyx kernel variant — used only when hardware.myGpu == \"nvidia\", to benefit from the precompiled nvidia_cachyos cache. \"zen\", \"nixpkgs-lts\", \"nixpkgs-latest\" and \"nixpkgs-testing\" fall outside this cache: nixpkgs kernel (linuxPackages_zen / linuxPackages / linuxPackages_latest / linuxPackages_testing) + nvidia module recompiled locally (see nvidia.nix)";
  };

  config = lib.mkMerge [
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

    # AMD / Intel / VM branch.
    #
    # TEMPORARY: the xddxdd overlay (nix-cachyos-kernel) and its attic cache
    # (attic.xuyh0120.win/lantian) are disabled — cache reported compromised.
    # Until it is trusted again, every "cachyos-*" value of hardware.myKernel
    # is served by Chaotic-Nyx (already imported globally in flake.nix), using
    # the closest family: lts / server / hardened / default. The finer xddxdd
    # variants (x86_64-vN, zen4, LTO, BORE/BMQ/EEVDF, rc, rt, deckify) do not
    # exist on Chaotic-Nyx, so they collapse onto that family and a build
    # warning says so.
    # To restore xddxdd: uncomment the input in flake.nix, the overlay + the
    # "lantian" substituter/key (flake.nix, common.nix, binary-caches.nix),
    # and bring back the `pkgs.cachyosKernels.*` table from git history.
    (lib.mkIf (config.hardware.myGpu != "nvidia") (
      let
        variant = config.hardware.myKernel;
        isCachy = lib.hasPrefix "cachyos" variant;
        chaoticFamily =
          if lib.hasPrefix "cachyos-lts" variant then "cachyos-lts"
          else if lib.hasPrefix "cachyos-server" variant then "cachyos-server"
          else if lib.hasPrefix "cachyos-hardened" variant then "cachyos-hardened"
          else "cachyos";
        chaoticKernels = {
          "cachyos"          = pkgs.linuxPackages_cachyos;
          "cachyos-lts"      = pkgs.linuxPackages_cachyos-lts;
          "cachyos-server"   = pkgs.linuxPackages_cachyos-server;
          "cachyos-hardened" = pkgs.linuxPackages_cachyos-hardened;
        };
      in
      {
        warnings = lib.optional (isCachy && variant != chaoticFamily) ''
          hardware.myKernel = "${variant}": the xddxdd CachyOS kernels are
          temporarily disabled, using Chaotic-Nyx "${chaoticFamily}" instead
          (no x86_64-vN / zen4 / LTO / scheduler-specific variant available).
        '';

        boot.kernelPackages =
          if variant == "zen" then
            # nixpkgs linux-zen
            pkgs.linuxPackages_zen
          else if variant == "nixpkgs-lts" then
            # nixpkgs default LTS
            pkgs.linuxPackages
          else if variant == "nixpkgs-latest" then
            # Latest stable mainline from nixpkgs
            pkgs.linuxPackages_latest
          else if variant == "nixpkgs-testing" then
            # linux_testing — nixpkgs RC/mainline candidate kernel
            pkgs.linuxPackages_testing
          else
            chaoticKernels.${chaoticFamily};
      }
    ))

    # Nvidia branch: Chaotic-Nyx kernel, to get the precompiled
    # nvidia_cachyos (chaotic.nixosModules.default is already imported
    # globally in flake.nix, no need to re-import here — its binary cache
    # is therefore active whether or not the GPU is nvidia)
    (lib.mkIf (config.hardware.myGpu == "nvidia") {
      boot.kernelPackages =
        if config.hardware.myKernelChaotic == "zen" then
          # nixpkgs linux-zen; the associated nvidia module
          # (nvidiaPackages.stable, built locally) is selected in nvidia.nix
          pkgs.linuxPackages_zen
        else if config.hardware.myKernelChaotic == "nixpkgs-lts" then
          # nixpkgs default LTS; nvidia module built locally (nvidia.nix)
          pkgs.linuxPackages
        else if config.hardware.myKernelChaotic == "nixpkgs-latest" then
          # Latest stable mainline from nixpkgs; nvidia module built locally (nvidia.nix)
          pkgs.linuxPackages_latest
        else if config.hardware.myKernelChaotic == "nixpkgs-testing" then
          # linux_testing — RC/mainline candidate kernel; nvidia module built locally (nvidia.nix)
          pkgs.linuxPackages_testing
        else
        let
          kernels = {
            "cachyos"          = pkgs.linuxPackages_cachyos;
            "cachyos-lts"      = pkgs.linuxPackages_cachyos-lts;
            "cachyos-server"   = pkgs.linuxPackages_cachyos-server;
            "cachyos-hardened" = pkgs.linuxPackages_cachyos-hardened;
          };
        in
          kernels.${config.hardware.myKernelChaotic};
    })
  ];
}

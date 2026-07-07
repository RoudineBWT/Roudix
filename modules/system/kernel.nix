{ config, pkgs, lib, inputs, ... }:
{
  options.hardware.myKernel = lib.mkOption {
    type = lib.types.enum [
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
    description = "CachyOS kernel variant to use";
  };

  config = {
    nixpkgs.overlays = [ inputs.nix-cachyos-kernel.overlays.pinned ];

    # Binary cache
    nix.settings.substituters = [ "https://attic.xuyh0120.win/lantian" ];
    nix.settings.trusted-public-keys = [ "lantian:EeAUQ+W+6r7EtwnmYjeVwx5kOGEBpjlBfPlzGlTNvHc=" ];

    # Sysctl repris de 70-cachyos-settings.conf (paquet cachyos-settings)
    # https://github.com/CachyOS/CachyOS-Settings/blob/master/usr/lib/sysctl.d/70-cachyos-settings.conf
    boot.kernel.sysctl = {
      # Réduit la tendance du noyau à libérer le cache VFS (dentries/inodes) par rapport au défaut (100)
      "vm.vfs_cache_pressure" = 50;

      # Seuil (en octets) à partir duquel un process qui écrit sur disque commence lui-même à flusher ses données sales
      "vm.dirty_bytes" = 268435456; # 256 MiB

      # Nombre de pages consécutives lues d'un coup depuis le swap (défaut 3) ; 0 recommandé si swap sur SSD/ZRAM
      "vm.page-cluster" = 0;

      # Seuil (en octets) à partir duquel les kernel flusher threads commencent à écrire en arrière-plan
      "vm.dirty_background_bytes" = 67108864; # 64 MiB

      # Intervalle (en centièmes de seconde) entre deux réveils des flusher threads (défaut 500)
      "vm.dirty_writeback_centisecs" = 1500;

      # Désactive le NMI watchdog : boot/shutdown plus rapide, un peu moins de conso
      "kernel.nmi_watchdog" = 0;

      # Autorise les utilisateurs non-root à créer des user namespaces (conteneurs non privilégiés)
      "kernel.unprivileged_userns_clone" = 1;

      # Masque les messages du noyau sur la console
      "kernel.printk" = "3 3 3 3";

      # Restreint l'accès aux pointeurs noyau exposés dans /proc
      "kernel.kptr_restrict" = 2;

      # Augmente la taille de la file de réception réseau, évite des pertes de paquets sous charge
      "net.core.netdev_max_backlog" = 4096;

      # Augmente le nombre max de file handles / inode cache
      "fs.file-max" = 2097152;

      # Nombre max de memory maps par process (utile pour certains jeux Proton/DayZ, etc.)
      "vm.max_map_count" = 16777216;

      # Limites inotify (surveillance de fichiers), utile pour IDE, Steam, sync tools, etc.
      "fs.inotify.max_user_watches" = 524288;
      "fs.inotify.max_user_instances" = 1024;

      # Intervalle de keepalive TCP par défaut (en secondes)
      "net.ipv4.tcp_keepalive_time" = 120;
    };

    boot.kernelPackages =
      let
        kernels = {
          # Latest
          "cachyos-latest"         = pkgs.cachyosKernels.linux-cachyos-latest;
          "cachyos-latest-v2"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v2;
          "cachyos-latest-v3"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v3;
          "cachyos-latest-v4"      = pkgs.cachyosKernels.linux-cachyos-latest-x86_64-v4;
          "cachyos-latest-zen4"    = pkgs.cachyosKernels.linux-cachyos-latest-zen4;
          "cachyos-latest-lto"     = pkgs.cachyosKernels.linux-cachyos-latest-lto;
          "cachyos-latest-lto-v2"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v2;
          "cachyos-latest-lto-v3"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v3;
          "cachyos-latest-lto-v4"  = pkgs.cachyosKernels.linux-cachyos-latest-lto-x86_64-v4;
          "cachyos-latest-lto-zen4"= pkgs.cachyosKernels.linux-cachyos-latest-lto-zen4;
          # LTS
          "cachyos-lts"            = pkgs.cachyosKernels.linux-cachyos-lts;
          "cachyos-lts-v2"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v2;
          "cachyos-lts-v3"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v3;
          "cachyos-lts-v4"         = pkgs.cachyosKernels.linux-cachyos-lts-x86_64-v4;
          "cachyos-lts-zen4"       = pkgs.cachyosKernels.linux-cachyos-lts-zen4;
          "cachyos-lts-lto"        = pkgs.cachyosKernels.linux-cachyos-lts-lto;
          "cachyos-lts-lto-v2"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v2;
          "cachyos-lts-lto-v3"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v3;
          "cachyos-lts-lto-v4"     = pkgs.cachyosKernels.linux-cachyos-lts-lto-x86_64-v4;
          "cachyos-lts-lto-zen4"   = pkgs.cachyosKernels.linux-cachyos-lts-lto-zen4;
          # Variants
          "cachyos-bmq"            = pkgs.cachyosKernels.linux-cachyos-bmq;
          "cachyos-bmq-lto"        = pkgs.cachyosKernels.linux-cachyos-bmq-lto;
          "cachyos-bore"           = pkgs.cachyosKernels.linux-cachyos-bore;
          "cachyos-bore-lto"       = pkgs.cachyosKernels.linux-cachyos-bore-lto;
          "cachyos-deckify"        = pkgs.cachyosKernels.linux-cachyos-deckify;
          "cachyos-deckify-lto"    = pkgs.cachyosKernels.linux-cachyos-deckify-lto;
          "cachyos-eevdf"          = pkgs.cachyosKernels.linux-cachyos-eevdf;
          "cachyos-eevdf-lto"      = pkgs.cachyosKernels.linux-cachyos-eevdf-lto;
          "cachyos-hardened"       = pkgs.cachyosKernels.linux-cachyos-hardened;
          "cachyos-hardened-lto"   = pkgs.cachyosKernels.linux-cachyos-hardened-lto;
          "cachyos-rc"             = pkgs.cachyosKernels.linux-cachyos-rc;
          "cachyos-rc-lto"         = pkgs.cachyosKernels.linux-cachyos-rc-lto;
          "cachyos-rt-bore"        = pkgs.cachyosKernels.linux-cachyos-rt-bore;
          "cachyos-rt-bore-lto"    = pkgs.cachyosKernels.linux-cachyos-rt-bore-lto;
          "cachyos-server"         = pkgs.cachyosKernels.linux-cachyos-server;
          "cachyos-server-lto"     = pkgs.cachyosKernels.linux-cachyos-server-lto;
        };
      in
        pkgs.linuxKernel.packagesFor kernels.${config.hardware.myKernel};
  };
}

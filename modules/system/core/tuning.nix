{ config, lib, ... }:

# CachyOS-Settings tweaks that Roudix does not have yet.
# Source: https://github.com/CachyOS/CachyOS-Settings
#
# Already covered elsewhere in Roudix (NOT repeated here): vm.* / kernel.* /
# net.* / fs.* sysctls (boot/kernel.nix), ZRAM + zswap off + swappiness 150
# (nix/common.nix), ntsync (nix/common.nix).
#
# Everything is opt-out: roudix.tuning.enable = false turns the whole file
# off, each block below also has its own switch (same "debloatable" idea as
# the rest of Roudix).
let
  cfg = config.roudix.tuning;

  mkToggle = description: lib.mkOption {
    inherit description;
    type = lib.types.bool;
    default = cfg.enable;
    defaultText = lib.literalExpression "config.roudix.tuning.enable";
  };
in
{
  options.roudix.tuning = {
    enable = lib.mkOption {
      description = "Enable the CachyOS-Settings-style system tuning (modules/system/core/tuning.nix)";
      type = lib.types.bool;
      default = true;
    };

    oomd.enable = mkToggle ''
      Make systemd-oomd actually watch system.slice and the user slices.
      NixOS starts the daemon by default but monitors nothing until a slice
      opts in, so out-of-memory situations end in a frozen desktop instead of
      a killed app.
    '';

    ioSchedulers.enable = mkToggle "Per-device I/O scheduler udev rules (HDD bfq, SATA/eMMC SSD mq-deadline, NVMe kyber)";

    shortTimeouts.enable = mkToggle ''
      15 s start / 10 s stop default timeouts and a higher open-files limit
      (faster shutdown when a service hangs). Services that set their own
      TimeoutStartSec/TimeoutStopSec are not affected.
    '';


    journalMaxUse = lib.mkOption {
      description = ''
        Cap for the persistent journal (SystemMaxUse). CachyOS uses 50M, which
        only keeps a few days of logs; 500M keeps enough history to debug a
        family machine remotely. null = keep the systemd default (10% of the
        filesystem, max 4G).
      '';
      type = lib.types.nullOr lib.types.str;
      default = "500M";
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [

    # ── Always on ───────────────────────────────────────────────────────────
    {
      boot.kernel.sysctl = {
        # Full SysRq (REISUB) to recover from a hang. systemd's own default,
        # which NixOS inherits, is 16 (sync only).
        "kernel.sysrq" = lib.mkDefault 1;
      };

      systemd.tmpfiles.rules = [
        # THP: tcmalloc-friendly defrag policy (thp.conf)
        "w! /sys/kernel/mm/transparent_hugepage/defrag - - - - defer+madvise"
        # THP shrinker (kernel >= 6.12): split THPs that are >80% zero pages so
        # THP=always (CachyOS kernels) doesn't inflate memory use (thp-shrinker.conf)
        "w! /sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none - - - - 409"
        # Coredumps are kept 3 days instead of 2 weeks (coredump.conf)
        "e /var/lib/systemd/coredump - - - 3d"
      ];

      # Hardware watchdogs only cost wakeups on a desktop (blacklist.conf).
      # Blacklisting a module that isn't present is harmless.
      boot.blacklistedKernelModules = [ "iTCO_wdt" "sp5100_tco" "wdat_wdt" ];

      services.journald.settings.Journal = lib.mkIf (cfg.journalMaxUse != null) {
        SystemMaxUse = cfg.journalMaxUse;
      };
    }

    # rtkit-daemon spams the journal at debug level (rtkit-daemon.service.d/override.conf).
    # Guarded: without rtkit the unit doesn't exist and we must not create a bogus one.
    (lib.mkIf config.security.rtkit.enable {
      systemd.services.rtkit-daemon.serviceConfig.LogLevelMax = lib.mkDefault "info";
    })

    # ── systemd-oomd (10-oomd-per-slice-defaults.conf) ──────────────────────
    (lib.mkIf cfg.oomd.enable {
      # nixpkgs sets ManagedOOMMemoryPressure=kill at 80% on these slices
      systemd.oomd.enableSystemSlice = true;
      systemd.oomd.enableUserSlices = true;

      # CachyOS also kills on swap exhaustion
      systemd.slices."system".sliceConfig.ManagedOOMSwap = "kill";
      systemd.slices."user".sliceConfig.ManagedOOMSwap = "kill";

      # Never pick the session slice (compositor / shell) as the victim
      # (10-ignore-session-slice.conf)
      systemd.user.slices."session".sliceConfig.ManagedOOMPreference = "omit";

      # oomd needs the cgroup controllers delegated to each user manager
      # (user@.service.d/delegate.conf)
      systemd.services."user@".serviceConfig.Delegate = lib.mkDefault "cpu cpuset io memory pids";
    })

    # ── I/O schedulers (60-ioschedulers.rules) ──────────────────────────────
    # bfq / kyber / mq-deadline are loaded on demand when the rule writes the
    # scheduler name. For NVMe, the kernel default ("none") is also a fine
    # choice: switch "kyber" to "none" below if you prefer it.
    (lib.mkIf cfg.ioSchedulers.enable {
      services.udev.extraRules = ''
        # HDD
        ACTION=="add|change", KERNEL=="sd[a-z]*", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
        # SATA / eMMC SSD
        ACTION=="add|change", KERNEL=="sd[a-z]*|mmcblk[0-9]*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
        # NVMe SSD
        ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="kyber"
      '';
    })

    # ── Timeouts and limits (system.conf.d / user.conf.d) ───────────────────
    (lib.mkIf cfg.shortTimeouts.enable {
      systemd.settings.Manager = {
        DefaultTimeoutStartSec = "15s";
        DefaultTimeoutStopSec = "10s";
        DefaultLimitNOFILE = "2048:2097152";
      };
      systemd.user.settings.Manager = {
        DefaultTimeoutStartSec = "15s";
        DefaultTimeoutStopSec = "10s";
        DefaultLimitNOFILE = "1024:1048576";
      };
    })

  ]);
}

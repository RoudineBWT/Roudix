{ config, lib, pkgs, ... }:

let
  cfg = config.roudix.laptop;

  # Run a command on the dedicated GPU of a hybrid-graphics laptop, the way
  # GNOME's "Launch using Discrete Graphics Card" does: switcherooctl picks the
  # first non-default GPU and sets the matching environment (DRI_PRIME=pci-...
  # for AMD/Intel, the PRIME-offload variables for NVIDIA). With a single GPU it
  # just runs the command. No `--` before the command: switcherooctl's own
  # option parsing is not documented to accept it.
  dgpu = pkgs.writeShellScriptBin "roudix-dgpu" ''
    if [ $# -eq 0 ]; then
      echo "usage: roudix-dgpu COMMAND [ARGS...]  (ROUDIX_NO_DGPU=1 disables it)" >&2
      exit 2
    fi
    if [ -n "''${ROUDIX_NO_DGPU:-}" ]; then exec "$@"; fi
    # `list` fails when switcheroo-control isn't reachable: run the command
    # as is rather than failing the game.
    if ${pkgs.switcheroo-control}/bin/switcherooctl list >/dev/null 2>&1; then
      exec ${pkgs.switcheroo-control}/bin/switcherooctl launch "$@"
    fi
    exec "$@"
  '';
in
{
  options.roudix.laptop = {
    dgpuLauncher = lib.mkOption {
      type = lib.types.package;
      default = dgpu;
      internal = true;
      readOnly = true;
      description = "roudix-dgpu wrapper (used by game-performance).";
    };

    enable = lib.mkEnableOption "Laptop power management";

    backend = lib.mkOption {
      type = lib.types.enum [ "tlp" "tuned" ];
      default = "tlp";
      description = ''
        Which tool manages power on this laptop. Never both: TLP and tuned
        (and power-profiles-daemon) tune the same knobs and conflict.

        "tlp": best battery life. Automatic AC/battery profiles, USB / PCIe /
        SATA / Wi-Fi power saving, battery charge thresholds. Disables tuned,
        so game-performance and the desktop's power-mode selector have
        nothing behind them.

        "tuned": the desktop's tuned + tuned-ppd stack stays active. Keeps
        game-performance and the GNOME / KDE power-mode selector working,
        which suits a gaming laptop that is mostly plugged in. No charge
        thresholds, and less aggressive battery tuning than TLP.
      '';
    };

    thinkpad = lib.mkEnableOption ''
      ThinkPad-specific tuning: loads thinkpad_acpi and lets TLP drive the
      battery charge-threshold sysfs it exposes. No tp-smapi — it's
      unmaintained and unnecessary on any ThinkPad new enough to have
      thinkpad_acpi's native charge_start/stop_threshold (all models with
      an embedded controller from roughly 2011 onward, L380 included)
    '';

    batteryChargeThresholds = {
      start = lib.mkOption {
        type = lib.types.int;
        default = 40;
        description = "Charge start threshold (%). Only applied when roudix.laptop.thinkpad is true.";
      };
      stop = lib.mkOption {
        type = lib.types.int;
        default = 80;
        description = "Charge stop threshold (%). Only applied when roudix.laptop.thinkpad is true.";
      };
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [
    # ── Both backends ──────────────────────────────────────────────────────
    {
      # Hybrid-graphics laptops (AMD dGPU, or an Intel iGPU next to one):
      # lets GNOME / KDE offer "Launch using dedicated GPU" and gives
      # `switcherooctl launch <app>`. Harmless on a single-GPU laptop. NVIDIA
      # Optimus keeps its own `nvidia-offload` (nvidia.nix).
      services.switcherooControl.enable = lib.mkDefault true;

      # Intel laptops: thermald keeps the CPU under its thermal limits without
      # hard throttling. Intel-only, mkDefault so it can be turned off.
      services.thermald.enable = lib.mkDefault (config.hardware.myCpu == "intel");

      boot.kernelModules = lib.optional cfg.thinkpad "thinkpad_acpi";

      environment.systemPackages = [ pkgs.powertop dgpu ];
    }

    # ── TLP ────────────────────────────────────────────────────────────────
    (lib.mkIf (cfg.backend == "tlp") {
      # power-profiles-daemon fights TLP over the same knobs (same class of
      # D-Bus conflict already hit with tuned on the desktop profile) — keep
      # exactly one power manager active.
      services.power-profiles-daemon.enable = false;

      # common.nix sets services.tuned.enable = true unconditionally (plain
      # assignment, not mkDefault) for the ppd-emulation game-performance
      # depends on — a plain `false` here at the same priority would be a
      # conflicting-definition eval error, not a silent override. mkForce
      # wins regardless of how the other side set it.
      # NOTE: this also kills tuned-adm, so roudix-gaming/game-performance
      # won't do anything with this backend. On a gaming laptop set
      # roudix.laptop.backend = "tuned" instead.
      services.tuned.enable = lib.mkForce false;

      services.tlp = {
        enable = true;
        settings = {
          # No CPU_SCALING_GOVERNOR_* on purpose. The right governor depends on
          # the scaling driver: "powersave" is fine with intel_pstate /
          # amd-pstate in active mode, but on acpi-cpufreq (older AMD/Intel) it
          # pins the minimum frequency, and on intel_cpufreq (Intel Core 5th
          # gen. and older, kernel >= 5.7) TLP's own FAQ lists it as a cause of
          # sluggishness. Left unset, TLP keeps the kernel default for each
          # driver. The EPP policies below do the AC/battery split on CPUs
          # that support them (they are ignored elsewhere).
          CPU_ENERGY_PERF_POLICY_ON_AC = "performance";
          CPU_ENERGY_PERF_POLICY_ON_BAT = "power";
          USB_AUTOSUSPEND = 1;
          RUNTIME_PM_ON_AC = "on";
          RUNTIME_PM_ON_BAT = "auto";
          # No HDA codec power saving on AC (crackle after idle); same idea as
          # CachyOS's audio-pm-ctl, which pipewire.nix only applies on desktops.
          SOUND_POWER_SAVE_ON_AC = 0;
          # Battery: no turbo boost, the platform's low-power profile and the
          # scheduler's power-saving mode (silently ignored where unsupported).
          CPU_BOOST_ON_BAT = 0;
          PLATFORM_PROFILE_ON_BAT = "low-power";
          SCHED_POWERSAVE_ON_BAT = 1;
        } // lib.optionalAttrs cfg.thinkpad {
          START_CHARGE_THRESH_BAT0 = cfg.batteryChargeThresholds.start;
          STOP_CHARGE_THRESH_BAT0 = cfg.batteryChargeThresholds.stop;
        };
      };
    })

    # ── tuned (+ tuned-ppd, set up in nix/common.nix) ──────────────────────
    (lib.mkIf (cfg.backend == "tuned") {
      warnings = lib.optional cfg.thinkpad
        "roudix.laptop.thinkpad: battery charge thresholds are applied by TLP only, so they are ignored with roudix.laptop.backend = \"tuned\". thinkpad_acpi is still loaded.";
    })
  ]);
}

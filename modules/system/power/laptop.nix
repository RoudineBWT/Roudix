{ config, lib, pkgs, ... }:

let
  cfg = config.roudix.laptop;
in
{
  options.roudix.laptop = {
    enable = lib.mkEnableOption "Laptop power management (TLP)";

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

  config = lib.mkIf cfg.enable {
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
    # won't do anything on a machine with roudix.laptop.enable — fine for
    # a general-use family laptop, but set roudix.gaming.enable = false
    # too if it isn't meant to be a gaming box, to avoid a script that
    # silently no-ops.
    services.tuned.enable = lib.mkForce false;

    services.tlp = {
      enable = true;
      settings = {
        CPU_SCALING_GOVERNOR_ON_AC = "performance";
        CPU_SCALING_GOVERNOR_ON_BAT = "powersave";
        CPU_ENERGY_PERF_POLICY_ON_AC = "performance";
        CPU_ENERGY_PERF_POLICY_ON_BAT = "power";
        USB_AUTOSUSPEND = 1;
        RUNTIME_PM_ON_AC = "on";
        RUNTIME_PM_ON_BAT = "auto";
      } // lib.optionalAttrs cfg.thinkpad {
        START_CHARGE_THRESH_BAT0 = cfg.batteryChargeThresholds.start;
        STOP_CHARGE_THRESH_BAT0 = cfg.batteryChargeThresholds.stop;
      };
    };

    boot.kernelModules = lib.optional cfg.thinkpad "thinkpad_acpi";

    environment.systemPackages = [ pkgs.powertop ];
  };
}

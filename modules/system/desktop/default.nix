{ config, lib, pkgs, inputs, options, ... }:
let
  cfg = config.roudix.desktop;
  dp = import ../../desktop-pkgs.nix {
    inherit pkgs inputs;
    latest = cfg.latest;
  };
  # Does the flake module declare this option? Used to degrade gracefully
  # (stay on the flake version + a warning) instead of failing evaluation.
  has = path: lib.hasAttrByPath path options;
  usesShell = builtins.elem cfg.type [ "niri" "hyprland" "mangowc" "umbriel" ];
  # dms-greeter is shared by the dms and caelestia shells
  dmsGreeterKey = if cfg.shell == "caelestia" then "caelestia" else "dms";

  mkLatest = what: lib.mkOption {
    type = lib.types.bool;
    default = false;
    description = ''
      false (default): ${what} from nixpkgs.
      true: the latest version, built from the project's own flake.

      Roudix configurations are written for the flake (latest) versions
      first. On the nixpkgs versions, a configuration error saying that an
      option, a setting or a config key "does not exist" is normal: it was
      added after the version nixpkgs ships. Wait for nixpkgs to catch up,
      or set this to true.
    '';
  };
in
{
  imports = [
    ./niri.nix
    ./gnome.nix
    ./kde.nix
    ./cinnamon.nix
    ./hyprland.nix
    ./mangowc.nix
    ./umbriel.nix
    # DE-agnostic desktop-session settings (dconf, XKB layout, icon-theme
    # option consumed by modules/home/theming/gtk-theme.nix)
    ./desktop-integration.nix
    ./icon-theme.nix
    ./keyboard.nix
  ];

  # ── Desktop environment option ───────────────────────────────────────────
  options.roudix.desktop.type = lib.mkOption {
    description = "Desktop environment selection. Use 'roudix-switch <de>' to change.";
    type = lib.types.enum [ "niri" "gnome" "kde" "cinnamon" "hyprland" "mangowc" "umbriel" ];
    default = "niri";
  };
  # ── Desktop shell option ─────────────────────────────────────────────────
  options.roudix.desktop.shell = lib.mkOption {
    description = "Shell/bar stack for Wayland compositors (niri, hyprland,mangowc). Set in local.nix.";
    type = lib.types.enum [ "noctalia" "dms" "caelestia" ];
    default = "noctalia";
  };

  # ── nixpkgs (default) or latest (flake) version, per component ───────────
  # Set in local.nix or from roudix-switcher / the installer. The greeters
  # follow their shell: noctalia -> noctalia-greeter, dms/caelestia ->
  # dms-greeter. niri/MangoWC/Umbriel: always flake. Hyprland: always nixpkgs.
  options.roudix.desktop.latest = let
    # niri, MangoWC and Umbriel are always built from their flake now. The
    # options stay (hidden, no effect) so an existing local.nix that still
    # sets them keeps evaluating.
    deprecated = lib.mkOption {
      type = lib.types.bool;
      default = true;
      internal = true;
      visible = false;
      description = "Deprecated: no effect (always the flake version).";
    };
  in {
    niri      = deprecated;
    mangowc   = deprecated;
    umbriel   = deprecated;
    noctalia  = mkLatest "Noctalia (and its greeter)";
    dms       = mkLatest "DankMaterialShell (and its greeter)";
    caelestia = mkLatest "Caelestia (and the DMS greeter it uses)";
  };

  config = lib.mkMerge [
    # Greeters: package from nixpkgs unless the shell asked for the latest.
    (lib.mkIf (dp.useNixpkgs "noctalia") {
      services.displayManager.noctalia-greeter.package = pkgs.noctalia-greeter;
    })
    (lib.mkIf (dp.useNixpkgs dmsGreeterKey && has [ "programs" "dms-greeter" "package" ]) {
      programs.dms-greeter.package = pkgs.dms-greeter;
    })

    # DMS / MangoWC: the flake NixOS module may not expose `package`.
    (lib.mkIf (dp.useNixpkgs "dms" && has [ "programs" "dank-material-shell" "package" ]) {
      programs.dank-material-shell.package = pkgs.dms-shell;
    })

    # Caelestia is driven by Hyprland global shortcuts only: on the other
    # compositors no shell would start at all.
    {
      assertions = [{
        assertion = !(usesShell && cfg.shell == "caelestia" && cfg.type != "hyprland");
        message = "roudix: roudix.desktop.shell = \"caelestia\" only works with roudix.desktop.type = \"hyprland\" (use noctalia or dms with niri, mangowc or umbriel).";
      }];
    }

    # Tell the user when a nixpkgs version could not be applied.
    {
      warnings =
        lib.optional (usesShell && cfg.shell == "dms" && dp.useNixpkgs "dms"
                      && !has [ "programs" "dank-material-shell" "package" ])
          "roudix: DMS from nixpkgs is not available with the flake module (no `package` option): the flake version is used. Set roudix.desktop.latest.dms = true to silence this."
        ++ lib.optional (usesShell && cfg.shell != "noctalia" && dp.useNixpkgs dmsGreeterKey
                         && !has [ "programs" "dms-greeter" "package" ])
          "roudix: dms-greeter from nixpkgs is not available with the flake module (no `package` option): the flake version is used.";
    }
  ];
}

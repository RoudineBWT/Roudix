{ lib, ... }:
{
  imports = [
    ./niri.nix
    ./gnome.nix
    ./kde.nix
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
    type = lib.types.enum [ "niri" "gnome" "kde" "hyprland" "mangowc" "umbriel" ];
    default = "niri";
  };
  # ── Desktop shell option ─────────────────────────────────────────────────
  options.roudix.desktop.shell = lib.mkOption {
    description = "Shell/bar stack for Wayland compositors (niri, hyprland,mangowc). Set in local.nix.";
    type = lib.types.enum [ "noctalia" "dms" "caelestia" ];
    default = "noctalia";
  };
}

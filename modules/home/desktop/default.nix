{ ... }:
{
  # Home-Manager side of each desktop environment. Mirrors
  # modules/system/desktop/default.nix — one subfolder per DE, each
  # guarded internally by `lib.mkIf (osConfig.roudix.desktop.type == "...")`,
  # so importing all of them unconditionally is safe: only the active one
  # actually produces config.
  imports = [
    ./niri/default.nix
    ./gnome/default.nix
    ./kde/default.nix
    ./hyprland/default.nix
    ./mangowc/default.nix
    ./umbriel/default.nix
    # Desktop shell stacks (caelestia-shell, DankMaterialShell) — imported
    # only once here to avoid the "option already declared" conflict that
    # happens if both niri/ and hyprland/ imported it themselves.
    ./shell-modules.nix
  ];
}

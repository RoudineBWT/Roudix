{ pkgs, inputs, osConfig, ... }:
let
  pkgs-stable = import inputs.nixpkgs-stable { system = pkgs.stdenv.hostPlatform; config.allowUnfree = true; };
  isKde = osConfig.roudix.desktop.type == "kde";
in
{
  # ── Gaming packages (user) ───────────────────────────────────────────────
  home.packages = with pkgs; [
    heroic                              # Epic/GOG launcher
    lutris                              # Multi-platform launcher
    prismlauncher                       # Minecraft launcher
    vintagestory                        # Minecraft but harder
    winetricks
    wineWow64Packages.staging
    mangohud                            # Performance overlay
    (if isKde then protonup-qt          # Qt-native Proton manager (KDE)
               else protonplus)         # GTK Proton manager (Niri, Hyprland, GNOME)
  ];
}

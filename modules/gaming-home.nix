{ pkgs, ... }:
{
  # ── Packages gaming (user) ───────────────────────────────────────────────
  home.packages = with pkgs; [
    heroic           # Launcher Epic/GOG
    lutris           # Launcher multi-plateformes
    prismlauncher    # Launcher Minecraft
    winetricks
    wineWow64Packages.staging
    protonplus       # Gestionnaire de versions Proton
    mangohud         # Overlay de performances
    gamemode         # Daemon gamemode (client)
  ];
}

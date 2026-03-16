{ pkgs, inputs, ... }:
let
  pkgs-stable = import inputs.nixpkgs-stable { system = pkgs.stdenv.hostPlatform.system; config.allowUnfree = true; };
in
{
  # ── Packages gaming (user) ───────────────────────────────────────────────
  home.packages = with pkgs; [
    pkgs-stable.heroic           # Launcher Epic/GOG
    lutris           # Launcher multi-plateformes
    prismlauncher    # Launcher Minecraft
    winetricks
    wineWow64Packages.staging
    protonplus       # Gestionnaire de versions Proton
    mangohud         # Overlay de performances
    gamemode         # Daemon gamemode (client)
  ];
}

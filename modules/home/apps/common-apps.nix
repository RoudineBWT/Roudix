{ pkgs, inputs, dotfiles, osConfig, lib, ... }:
let
  # Fluxer — a self-hostable Discord alternative. Not in nixpkgs yet, so it
  # comes straight from the nix-gaming-edge flake's prebuilt package rather
  # than a map like matrix/discord/telegram (../matrix.nix, ../discord.nix,
  # ../telegram.nix). Deliberately independent of roudix.discord (people
  # may want both) and of roudix.gaming.enable (it has nothing to do with
  # gaming, so it doesn't need that overlay). Option declared in
  # modules/system/apps/apps.nix
  fluxerPackage = inputs.nix-gaming-edge.packages.${pkgs.stdenv.hostPlatform.system}.fluxer-desktop;
in
{
  # ── Easyeffects preset ──────────────────────────────────────────────────
  xdg.configFile."easyeffects" = lib.mkIf osConfig.roudix.apps.easyeffects.enable {
    source = "${dotfiles}/easyeffects";
    recursive = true;
  };

  # Optional common apps (roudix.apps.*)
  home.packages =
    lib.optional osConfig.roudix.apps.gimp.enable pkgs.gimp
    ++ lib.optional osConfig.roudix.apps.inkscape.enable pkgs.inkscape
    ++ lib.optional osConfig.roudix.apps.songrec.enable pkgs.songrec
    ++ lib.optionals osConfig.roudix.apps.easyeffects.enable [ pkgs.easyeffects pkgs.rnnoise-plugin ]
    ++ lib.optional osConfig.roudix.apps.signal.enable pkgs.signal-desktop
    ++ lib.optional osConfig.roudix.apps.zapzap.enable pkgs.zapzap
    ++ lib.optional osConfig.roudix.apps.fluxer.enable fluxerPackage;
}

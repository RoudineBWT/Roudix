{ pkgs, inputs, dotfiles, osConfig, lib, ... }:
let
  # Fluxer — a self-hostable Discord alternative. Not in nixpkgs yet, so it
  # comes straight from the nix-gaming-edge flake's prebuilt package rather
  # than a map like matrix/discord/telegram (communication/matrix.nix,
  # communication/discord.nix, communication/telegram.nix). Deliberately
  # independent of roudix.discord (people may want both) and of
  # roudix.gaming.enable (it has nothing to do with gaming, so it doesn't
  # need that overlay). Option declared in
  # modules/system/apps/apps.nix
  # The channel is picked by roudix.apps.fluxer.channel ("stable" | "canary").
  fluxerPackages = inputs.nix-gaming-edge.packages.${pkgs.stdenv.hostPlatform.system};
  fluxerPackage =
    if osConfig.roudix.apps.fluxer.channel == "canary"
    then fluxerPackages.fluxer-desktop-canary
    else fluxerPackages.fluxer-desktop;

  # Cressida — unofficial native Wayland Discord client. Same idea as
  # fluxerPackage: not in nixpkgs, taken straight from its own flake input
  # (inputs.cressida), independent of roudix.discord / roudix.apps.fluxer /
  # roudix.gaming.enable. Option declared in modules/system/apps/apps.nix
  cressidaPackage = inputs.cressida.packages.${pkgs.stdenv.hostPlatform.system}.default;
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
    ++ lib.optional osConfig.roudix.apps.fluxer.enable fluxerPackage
    ++ lib.optional osConfig.roudix.apps.cressida.enable cressidaPackage;
}

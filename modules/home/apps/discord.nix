{ pkgs, osConfig, lib, ... }:
let
  discordType = osConfig.roudix.discord or "vencord";

  discordPackage = {
    vencord = pkgs.discord.override { withVencord = true; };
    vanilla = pkgs.discord;
    none    = null;
  }.${discordType};
in
{
  # Discord (optionnel) — option declared in modules/system/apps/discord.nix
  home.packages = lib.optional (discordPackage != null) discordPackage;
}

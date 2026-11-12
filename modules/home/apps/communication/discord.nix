{ pkgs, osConfig, lib, ... }:
let
  discordType = osConfig.roudix.discord or "vencord";

  # Vesktop installs a `vesktop` binary (app_id/class "vesktop"), while the
  # desktop configs (autostart, scratchpads, spawn_when_empty...) launch
  # `discord`. This thin wrapper keeps every one of them working unchanged.
  vesktopAsDiscord = pkgs.writeShellScriptBin "discord" ''
    exec ${lib.getExe pkgs.vesktop} "$@"
  '';

  discordPackages = {
    vencord = [ (pkgs.discord.override { withVencord = true; }) ];
    vanilla = [ pkgs.discord ];
    vesktop = [ pkgs.vesktop vesktopAsDiscord ];
    none    = [ ];
  }.${discordType};
in
{
  # Discord (optionnel) — option declared in modules/system/apps/communication/discord.nix
  home.packages = discordPackages;
}

{ lib, ... }:
{
  # ── Discord: none, vanilla, Vencord-patched, or Vesktop ──────────────────────────
  # Read on the home-manager side (modules/home/apps/communication/discord.nix) via osConfig —
  # that's where the discord package is actually installed
  # (home.packages); this option only controls WHICH package is chosen
  # (or none).
  options.roudix.discord = lib.mkOption {
    type    = lib.types.enum [ "none" "vanilla" "vencord" "vesktop" ];
    default = "vencord";
    description = ''
      "none"    : Discord isn't installed.
      "vanilla" : Discord with no client patch.
      "vencord" : Discord already patched with Vencord
                  (`discord.override { withVencord = true; }`).
      "vesktop" : Vesktop, the standalone Vencord client (Electron + native
                  Wayland, working screen share with audio). Alternative to
                  both vanilla Discord and the patched Discord above.
    '';
  };
}

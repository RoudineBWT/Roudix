{ lib, ... }:
{
  # ── Discord: none, vanilla, or Vencord-patched ──────────────────────────
  # Read on the home-manager side (modules/home/apps/discord.nix) via osConfig —
  # that's where the discord package is actually installed
  # (home.packages); this option only controls WHICH package is chosen
  # (or none).
  options.roudix.discord = lib.mkOption {
    type    = lib.types.enum [ "none" "vanilla" "vencord" ];
    default = "vencord";
    description = ''
      "none"    : Discord isn't installed.
      "vanilla" : Discord with no client patch.
      "vencord" : Discord already patched with Vencord
                  (`discord.override { withVencord = true; }`).
    '';
  };
}

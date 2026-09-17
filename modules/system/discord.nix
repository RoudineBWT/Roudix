{ lib, ... }:
{
  # ── Discord : aucun, vanilla, ou patché Vencord ──────────────────────────
  # Lu côté home-manager (modules/home/common.nix) via osConfig — c'est là
  # que le paquet discord est réellement installé (home.packages), cette
  # option ne fait que piloter QUEL paquet est choisi (ou aucun).
  options.roudix.discord = lib.mkOption {
    type    = lib.types.enum [ "none" "vanilla" "vencord" ];
    default = "vencord";
    description = ''
      "none"    : Discord n'est pas installé.
      "vanilla" : Discord sans aucun patch client.
      "vencord" : Discord avec Vencord déjà patché
                  (`discord.override { withVencord = true; }`).
    '';
  };
}

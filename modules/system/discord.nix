{ lib, ... }:
{
  # ── Discord : vanilla ou patché Vencord ──────────────────────────────────
  # Lu côté home-manager (modules/home/common.nix) via osConfig — c'est là
  # que le paquet discord est réellement installé (home.packages), cette
  # option ne fait que piloter QUEL paquet est choisi.
  options.roudix.discord.vencord.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
    description = ''
      Si true (défaut), installe Discord avec Vencord déjà patché
      (`discord.override { withVencord = true; }`). Si false, installe
      Discord vanilla, sans aucun patch client.
    '';
  };
}

{ lib, ... }:
{
  # ── Password manager: pick one, or none ──────────────────────────────────
  # Read on the home-manager side (modules/home/apps/password-manager.nix) via osConfig —
  # same pattern as roudix.torrentClient / roudix.mailClient.
  options.roudix.passwordManager = lib.mkOption {
    type    = lib.types.enum [ "none" "bitwarden" "keepassxc" "protonpass" ];
    default = "none";
    description = ''
      "none"       : No password manager installed.
      "bitwarden"  : Bitwarden Desktop — cloud-synced vault
                     (`pkgs.bitwarden-desktop`).
      "keepassxc"  : KeePassXC — local, offline vault file, no account
                     needed.
      "protonpass" : Proton Pass — cloud-synced vault tied to a Proton
                     account (`pkgs.proton-pass`).
    '';
  };
}

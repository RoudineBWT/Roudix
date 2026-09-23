{ lib, ... }:
{
  # ── Mail client: pick one, or none ───────────────────────────────────────
  # Read on the home-manager side (modules/home/common.nix) via osConfig —
  # same pattern as roudix.torrentClient / roudix.videoPlayer.
  options.roudix.mailClient = lib.mkOption {
    type    = lib.types.enum [ "none" "thunderbird" "betterbird" "geary" ];
    default = "none";
    description = ''
      "none"        : No mail client installed.
      "thunderbird" : Thunderbird — full-featured (mail, calendar, RSS,
                      add-ons).
      "betterbird"  : Betterbird — a fine-tuned fork of Thunderbird with
                      extra patches/UX tweaks. Not in nixpkgs, pulled from
                      the `betterbird-nix` flake input's `betterbird`
                      package.
      "geary"       : Geary — lightweight GNOME/libadwaita mail client.
    '';
  };
}

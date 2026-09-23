{ lib, ... }:
{
  # ── Mail client: pick one, or none ───────────────────────────────────────
  # Read on the home-manager side (modules/home/common.nix) via osConfig —
  # same pattern as roudix.torrentClient / roudix.videoPlayer.
  options.roudix.mailClient = lib.mkOption {
    type    = lib.types.enum [ "none" "thunderbird" "geary" ];
    default = "none";
    description = ''
      "none"        : No mail client installed.
      "thunderbird" : Thunderbird — full-featured (mail, calendar, RSS,
                      add-ons).
      "geary"       : Geary — lightweight GNOME/libadwaita mail client.
    '';
  };
}

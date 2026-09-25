{ lib, ... }:
{
  # ── Torrent client: pick one, or none ───────────────────────────────────
  # Read on the home-manager side (modules/home/apps/utilities/torrent-client.nix) via osConfig —
  # same pattern as roudix.discord / roudix.matrixClient / roudix.telegram.
  # Used to be a plain roudix.apps.qbittorrent.enable boolean (always
  # qBittorrent) — promoted to its own enum so an alternative client can be
  # picked instead.
  options.roudix.torrentClient = lib.mkOption {
    type    = lib.types.enum [ "none" "qbittorrent" "fragments" "deluge" ];
    default = "none";
    description = ''
      "none"        : No torrent client installed.
      "qbittorrent" : qBittorrent — feature-rich, Qt-based (Roudix default
                      when enabled).
      "fragments"   : Fragments — minimal GNOME/libadwaita client.
      "deluge"      : Deluge — plugin-based, lightweight core + WebUI/daemon.
    '';
  };
}

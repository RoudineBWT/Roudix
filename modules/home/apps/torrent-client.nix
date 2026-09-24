{ pkgs, osConfig, lib, ... }:
let
  torrentClientType = osConfig.roudix.torrentClient or "none";

  torrentClientPackage = {
    qbittorrent = pkgs.qbittorrent;
    fragments   = pkgs.fragments;
    deluge      = pkgs.deluge;
    none        = null;
  }.${torrentClientType};
in
{
  # Torrent client (optional) — option declared in
  # modules/system/apps/torrent-client.nix
  home.packages = lib.optional (torrentClientPackage != null) torrentClientPackage;
}

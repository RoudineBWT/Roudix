{ lib, ... }:
{
  # ── Telegram: none, official Telegram Desktop, or the AyuGram fork ──────
  # Read on the home-manager side (modules/home/common.nix) via osConfig —
  # same pattern as roudix.discord / roudix.matrixClient. Used to live as a
  # plain roudix.apps.telegram.enable boolean (always installing
  # telegram-desktop) — promoted to its own enum, like Discord, so an
  # alternative client can be picked instead of just on/off.
  options.roudix.telegram = lib.mkOption {
    type    = lib.types.enum [ "none" "telegram" "ayugram" ];
    default = "none";
    description = ''
      "none"     : Telegram isn't installed.
      "telegram" : Official Telegram Desktop (`pkgs.telegram-desktop`).
      "ayugram"  : AyuGram, an unofficial Telegram Desktop fork with ghost
                   mode, message history, anti-recall and more
                   (`pkgs.ayugram-desktop`).
    '';
  };
}

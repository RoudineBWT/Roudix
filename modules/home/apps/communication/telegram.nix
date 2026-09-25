{ pkgs, osConfig, lib, ... }:
let
  telegramType = osConfig.roudix.telegram or "none";

  telegramPackage = {
    telegram = pkgs.telegram-desktop;
    ayugram  = pkgs.ayugram-desktop;
    none     = null;
  }.${telegramType};
in
{
  # Telegram — official client or the AyuGram fork (optional) — option
  # declared in modules/system/apps/communication/telegram.nix
  home.packages = lib.optional (telegramPackage != null) telegramPackage;
}

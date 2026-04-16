{ config, ... }:
{
  xdg.configFile."DankMaterialShell/settings.json".source =
    config.lib.file.mkOutOfStoreSymlink
      "${config.home.homeDirectory}/.config/DankMaterialShell/settings.json";
  # ou juste laisser DMS gérer son propre fichier, le greeter le lira via configHome
}

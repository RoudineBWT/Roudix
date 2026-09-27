{ lib, ... }:
{
  options.roudix.editor = lib.mkOption {
    type = lib.types.enum [ "vscode" "zed" "neovim" "none" ];
    default = "zed";
    description = ''
      Éditeur de code par défaut installé côté home-manager
      (voir modules/home/apps/utilities/editor.nix). "none" pour n'en installer aucun
      (utile si tu préfères gérer ton éditeur toi-même, ex: AppImage,
      Flatpak, ou snap).
    '';
  };
}

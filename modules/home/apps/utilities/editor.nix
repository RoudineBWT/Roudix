{ pkgs, osConfig, lib, ... }:
let
  editorType = osConfig.roudix.editor or "zed";

  editorPackage = {
    vscode  = pkgs.vscode;
    zed     = pkgs.zed-editor;
    neovim  = pkgs.neovim;
    none    = null;
  }.${editorType};
in
{
  # Editor chosen by the user (roudix.editor, "none" for none) — option
  # declared in modules/system/apps/utilities/editor.nix
  home.packages = lib.optional (editorPackage != null) editorPackage;
}

{ pkgs, lib, ... }: {
  home.activation.copyPapirus = lib.hm.dag.entryAfter ["writeBoundary"] ''
    if [ ! -d "$HOME/.local/share/icons/Papirus-Dark" ]; then
      mkdir -p $HOME/.local/share/icons/
      cp -r ${pkgs.papirus-icon-theme}/share/icons/Papirus* $HOME/.local/share/icons/
      chmod -R u+w $HOME/.local/share/icons/Papirus*
    fi
  '';
}

{ lib, osConfig, ... }:
let
  isCinnamon = osConfig.roudix.desktop.type == "cinnamon";
in
{
  # The panel pins and the menu icon are now per-applet *defaults* patched
  # into Cinnamon itself (modules/system/desktop/cinnamon.nix). A default only
  # applies to an applet instance that has no settings file yet, so the files
  # left by the previous home-manager seeding (and any older default) are
  # removed once; after that, whatever the user changes in the panel stays.
  # Bump the marker's version to reset again.
  home.activation.cinnamonPanelDefaults = lib.mkIf isCinnamon (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      marker="''${XDG_STATE_HOME:-$HOME/.local/state}/roudix/cinnamon-panel-defaults-v2"
      if [ ! -e "$marker" ]; then
        rm -f "$HOME"/.config/cinnamon/spices/grouped-window-list@cinnamon.org/*.json \
              "$HOME"/.config/cinnamon/spices/menu@cinnamon.org/*.json
        mkdir -p "$(dirname "$marker")"
        touch "$marker"
      fi
    ''
  );
}

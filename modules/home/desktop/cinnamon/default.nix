{ lib, pkgs, osConfig, ... }:
let
  isCinnamon = osConfig.roudix.desktop.type == "cinnamon";
  pinnedApps = osConfig.roudix.desktop.cinnamon.pinnedApps;

  logo = "/run/current-system/sw/share/icons/hicolor/256x256/apps/roudix-logo.png";

  # Text shown next to the logo in the panel menu button. "" = logo only,
  # or e.g. "Roudix". Only a default: changeable in the applet's settings.
  menuLabel = "";

  # ── Per-applet defaults without rebuilding Cinnamon ─────────────────────
  # An applet's settings file (~/.config/cinnamon/spices/<applet>/<id>.json)
  # is created on first load from the applet's settings-schema.json. So the
  # defaults are changed there: a copy of the two applets with a patched
  # schema (a few KB, built in a second), placed in ~/.local/share/cinnamon/
  # applets, which Cinnamon searches before the system directories. Nothing
  # of Cinnamon itself is rebuilt, and the copies follow the installed
  # Cinnamon version on every update.
  # A missing key fails the build and prints the keys the schema really has.
  patchedApplet = uuid: patches:
    pkgs.runCommand "roudix-${uuid}" { nativeBuildInputs = [ pkgs.jq ]; } ''
      cp -r ${pkgs.cinnamon}/share/cinnamon/applets/${uuid} $out
      chmod -R u+w $out
      f=$out/settings-schema.json
      patch() {
        jq -e --arg k "$1" 'has($k)' "$f" > /dev/null || {
          echo "roudix: ${uuid} has no '$1' key; keys: $(jq -c keys "$f")" >&2
          exit 1
        }
        jq --arg k "$1" --argjson v "$2" '.[$k].default = $v' "$f" > "$f.tmp"
        mv "$f.tmp" "$f"
      }
      ${patches}
    '';
in
{
  xdg.dataFile = lib.mkIf isCinnamon {
    "cinnamon/applets/grouped-window-list@cinnamon.org".source =
      patchedApplet "grouped-window-list@cinnamon.org" ''
        patch pinned-apps '${builtins.toJSON pinnedApps}'
      '';
    "cinnamon/applets/menu@cinnamon.org".source =
      patchedApplet "menu@cinnamon.org" ''
        patch menu-custom true
        patch menu-icon '${builtins.toJSON logo}'
        patch menu-label '${builtins.toJSON menuLabel}'
      '';
  };

  # A default only applies to an applet instance that has no settings file
  # yet, so the files left by the previous attempts are removed once; after
  # that, whatever the user changes in the panel stays. Bump the marker's
  # version to reset again.
  home.activation.cinnamonPanelDefaults = lib.mkIf isCinnamon (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      marker="''${XDG_STATE_HOME:-$HOME/.local/state}/roudix/cinnamon-panel-defaults-v4"
      if [ ! -e "$marker" ]; then
        rm -f "$HOME"/.config/cinnamon/spices/grouped-window-list@cinnamon.org/*.json \
              "$HOME"/.config/cinnamon/spices/menu@cinnamon.org/*.json
        mkdir -p "$(dirname "$marker")"
        touch "$marker"
      fi
    ''
  );
}

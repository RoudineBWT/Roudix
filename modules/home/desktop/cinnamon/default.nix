{ lib, pkgs, osConfig, ... }:
let
  isCinnamon = osConfig.roudix.desktop.type == "cinnamon";

  # Pinned apps of the panel's window list (grouped-window-list applet):
  # default browser, Roudix Store, Settings. The list lives in
  # modules/system/desktop/cinnamon.nix (roudix.desktop.cinnamon.pinnedApps).
  pinnedApps = osConfig.roudix.desktop.cinnamon.pinnedApps;

  # Instance id of grouped-window-list in `enabled-applets`
  # ("...:grouped-window-list@cinnamon.org:2"), set in cinnamon.nix.
  gwlInstance = "2";
in
{
  # Cinnamon's look & feel is shipped as dconf *defaults* by cinnamon.nix, but
  # the panel's pinned apps are not a dconf key: they are stored in
  # ~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/<id>.json.
  # Seeded once per user (marker file), then left alone, so a rebuild never
  # reverts pins the user changed. Bump the marker's version to re-apply.
  home.activation.cinnamonPinnedApps = lib.mkIf isCinnamon (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      marker="''${XDG_STATE_HOME:-$HOME/.local/state}/roudix/cinnamon-pinned-apps-v1"
      if [ ! -e "$marker" ]; then
        dir="$HOME/.config/cinnamon/spices/grouped-window-list@cinnamon.org"
        file="$dir/${gwlInstance}.json"
        apps='${builtins.toJSON pinnedApps}'
        mkdir -p "$dir" "$(dirname "$marker")"
        if [ -f "$file" ]; then
          # Existing settings: only replace the pinned apps, keep the rest.
          ${pkgs.jq}/bin/jq --argjson apps "$apps" \
            '.["pinned-apps"] = ((.["pinned-apps"] // {"type": "generic", "default": $apps}) | .value = $apps)' \
            "$file" > "$file.roudix-tmp" && mv -f "$file.roudix-tmp" "$file"
        else
          ${pkgs.jq}/bin/jq -n --argjson apps "$apps" \
            '{"pinned-apps": {"type": "generic", "default": $apps, "value": $apps}}' > "$file"
        fi
        touch "$marker"
      fi
    ''
  );
}

{ pkgs, lib, roudixPalette, ... }:
let
  papirusIconsOut = "${pkgs.papirus-icon-theme}/share/icons";

  # File-manager app icons recolored next to the folders (same list as
  # modules/system/desktop/icon-theme.nix): system-file-manager is Papirus'
  # 3-tab cabinet, org.kde.dolphin is the blue folder the Dolphin launcher uses.
  fileManagerApps = lib.concatStringsSep " " [
    "system-file-manager" "file-manager" "nemo" "org.gnome.Nautilus"
    "org.kde.dolphin" "dolphin" "org.xfce.filemanager" "thunar"
  ];

  papirusSync = pkgs.writeShellScriptBin "noctalia-papirus-sync" ''
    set -euo pipefail
    primaryFile="$HOME/.config/noctalia/generated/tela-primary.txt"
    # Noctalia's generated primary wins; otherwise Roudix.json's primary.
    if [ -f "$primaryFile" ]; then
      primary=$(tr -d '[:space:]' < "$primaryFile")
    else
      primary="${roudixPalette.primary}"
    fi
    case "$primary" in
      \#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
      *) exit 0 ;;
    esac

    # Papirus uses 2 shades per color: #5294e2 (body) and #4877b1
    # (tab, ~80% darker). Computes primary's dark equivalent.
    hex="''${primary#\#}"
    r=$((16#''${hex:0:2})); g=$((16#''${hex:2:2})); b=$((16#''${hex:4:2}))
    r=$(( r * 80 / 100 )); g=$(( g * 80 / 100 )); b=$(( b * 80 / 100 ))
    darker=$(printf '#%02x%02x%02x' "$r" "$g" "$b")

    # Lighter shades of the primary (25 % / 50 % toward white) for the 2nd and
    # 3rd tab of the cabinet (stock: green / yellow), so they follow Noctalia.
    lighten() {
      h="''${1#\#}"
      r=$((16#''${h:0:2})); g=$((16#''${h:2:2})); b=$((16#''${h:4:2}))
      r=$(( r + (255 - r) * $2 / 100 )); g=$(( g + (255 - g) * $2 / 100 )); b=$(( b + (255 - b) * $2 / 100 ))
      printf '#%02x%02x%02x' "$r" "$g" "$b"
    }
    tab2=$(lighten "$primary" 25)
    tab3=$(lighten "$primary" 50)

    for variant in Papirus Papirus-Light Papirus-Dark; do
      dest="$HOME/.icons/''${variant}-noctalia"
      rm -rf "$dest"
      mkdir -p "$dest"

      # Inherits from the original theme ONLY for what isn't provided
      # here -> only folders + file-manager icons copied, zero risk of breakage.
      cp "${papirusIconsOut}/$variant/index.theme" "$dest/index.theme"
      ${pkgs.gnused}/bin/sed -i \
        -e "s/^Inherits=.*/Inherits=$variant/" \
        -e "s/^Name=.*/Name=''${variant} Noctalia/" \
        "$dest/index.theme"

      # Only copies the "places" folder for each available size,
      # dereferencing (-L) internal/cross-variant symlinks
      # (e.g. Papirus-Dark/48x48 -> ../Papirus/48x48), plus the file-manager
      # app icons listed in fileManagerApps (missing ones are skipped).
      base="${papirusIconsOut}/$variant"
      for size in 16x16 22x22 24x24 32x32 48x48 64x64 96x96 128x128 scalable symbolic; do
        src="$base/$size/places"
        if [ -d "$src" ]; then
          mkdir -p "$dest/$size/places"
          cp -rL "$src/." "$dest/$size/places/"
        fi
        for app in ${fileManagerApps}; do
          f="$base/$size/apps/$app.svg"
          [ -e "$f" ] || continue
          mkdir -p "$dest/$size/apps"
          cp -L "$f" "$dest/$size/apps/$app.svg"
        done
        # HiDPI: "<size>@2x" dirs are symlinks to <size> in Papirus. Without
        # them here, scaled displays fall back to the stock blue icons.
        if [ -e "$base/$size@2x" ] && [ -d "$dest/$size" ]; then
          ln -s "$size" "$dest/$size@2x"
        fi
      done

      find "$dest" -path '*/places/*.svg' -print0 \
        | xargs -0 ${pkgs.gnused}/bin/sed -i \
            -e "s/#5294e2/$primary/g" \
            -e "s/#4877b1/$darker/g"

      # File-manager icons: cabinet tabs (#5294e2 / #5895dc at small sizes,
      # #89e058, #ffcd54) and Dolphin (#127bdc body, #1f6394 back tab).
      find "$dest" -path '*/apps/*.svg' -print0 \
        | xargs -0 -r ${pkgs.gnused}/bin/sed -i \
            -e "s/#5294e2/$primary/Ig" \
            -e "s/#5895dc/$primary/Ig" \
            -e "s/#89e058/$tab2/Ig" \
            -e "s/#ffcd54/$tab3/Ig" \
            -e "s/#127bdc/$primary/Ig" \
            -e "s/#1f6394/$darker/Ig"

      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest" || true
      fi
    done
    # Themes generated in ~/.icons/{Papirus,Papirus-Light,Papirus-Dark}-noctalia,
    # but not applied automatically — pick them manually (nwg-look).
  '';
in
{
  home.activation.papirusSyncRecolor = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    # Also regenerates themes built before the file-manager icons were added.
    [ -e "$HOME/.icons/Papirus-Dark-noctalia/48x48/apps/org.kde.dolphin.svg" ] || ${papirusSync}/bin/noctalia-papirus-sync || true
  '';

  home.packages = [ pkgs.papirus-icon-theme papirusSync pkgs.gnused ];

  # Reuses the shared template defined in tela-icon.nix
  # (~/.config/noctalia/templates/tela-primary.tmpl), with its own post_hook.
  xdg.configFile."noctalia/51-papirus-icons.toml".text = ''
    [theme.templates.user.papirus_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${papirusSync}/bin/noctalia-papirus-sync"
  '';
}

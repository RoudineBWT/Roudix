{ pkgs, lib, roudixPalette, ... }:
let
  telaIconsOut = "${pkgs.tela-icon-theme}/share/icons";

  # File-manager app icons recolored next to the folders (same list as
  # modules/system/desktop/icon-theme.nix): system-file-manager and Dolphin
  # resolve to file-manager.svg (blue folder), nemo.svg is the green one.
  fileManagerApps = lib.concatStringsSep " " [
    "system-file-manager" "file-manager" "nemo" "org.gnome.Nautilus"
    "org.kde.dolphin" "dolphin" "org.xfce.filemanager" "thunar"
  ];

  telaSync = pkgs.writeShellScriptBin "noctalia-tela-sync" ''
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

    for variant in Tela Tela-light Tela-dark; do
      dest="$HOME/.icons/''${variant}-noctalia"
      rm -rf "$dest"
      mkdir -p "$dest"

      # Inherits from the original theme ONLY for what isn't provided
      # here -> only folders + file-manager icons copied, zero risk of breakage.
      cp "${telaIconsOut}/$variant/index.theme" "$dest/index.theme"
      ${pkgs.gnused}/bin/sed -i \
        -e "s/^Inherits=.*/Inherits=$variant/" \
        -e "s/^Name=.*/Name=''${variant} Noctalia/" \
        "$dest/index.theme"

      # Only copies the "places" folder for each available size,
      # dereferencing (-L) internal/cross-variant symlinks, plus the
      # file-manager app icons listed in fileManagerApps (missing ones are
      # skipped).
      base="${telaIconsOut}/$variant"
      for size in 16 22 24 32 scalable symbolic; do
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
        # HiDPI links, if the base theme ships any (Tela currently doesn't).
        if [ -e "$base/$size@2x" ] && [ -d "$dest/$size" ]; then
          ln -s "$size" "$dest/$size@2x"
        fi
      done

      find "$dest" -path '*/places/*.svg' -print0 \
        | xargs -0 ${pkgs.gnused}/bin/sed -i "s/#5294e2/$primary/g"

      # File-manager icons: blue folder (#5294e2) and nemo's green (#4ed09d).
      find "$dest" -path '*/apps/*.svg' -print0 \
        | xargs -0 -r ${pkgs.gnused}/bin/sed -i \
            -e "s/#5294e2/$primary/Ig" \
            -e "s/#4ed09d/$primary/Ig"

      if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dest" || true
      fi
    done
    # Themes generated in ~/.icons/{Tela,Tela-light,Tela-dark}-noctalia, but
    # not applied automatically — pick them manually (nwg-look, etc.).
  '';
in
{
  home.activation.telaSyncRecolor = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    # Also regenerates themes built before the file-manager icons were added.
    [ -e "$HOME/.icons/Tela-dark-noctalia/scalable/apps/file-manager.svg" ] || ${telaSync}/bin/noctalia-tela-sync || true
  '';

  home.packages = [ pkgs.tela-icon-theme telaSync pkgs.gnused ];

  xdg.configFile."noctalia/templates/tela-primary.tmpl".text =
    "{{colors.primary.default.hex}}";

  xdg.configFile."noctalia/50-tela-icons.toml".text = ''
    [theme.templates.user.tela_primary]
    input_path  = "~/.config/noctalia/templates/tela-primary.tmpl"
    output_path = "~/.config/noctalia/generated/tela-primary.txt"
    post_hook   = "${telaSync}/bin/noctalia-tela-sync"
  '';
}

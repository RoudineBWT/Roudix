# Live recolour of the Roudix cursor from the Noctalia palette.
#
# The static theme (pkgs/roudix-cursor, Roudix.json colours) is always there as
# the fallback. On Noctalia sessions of the bare compositors this module adds
# `roudix-cursor-sync RRGGBB RRGGBB`, run by a Noctalia template hook whenever
# the palette changes (wallpaper / accent):
#
#   accent  = Noctalia primary         (cursor fill)
#   outline = Noctalia terminal bg     (cursor outline)
#
# It rebuilds the cursor from nixpkgs' Bibata-Modern-Ice bitmaps (same recipe as
# pkgs/roudix-cursor) into
#   ~/.local/share/icons/Bibata-Modern-Roudix-<accent>-<outline>
# and repoints the symlink ~/.local/share/icons/Bibata-Modern-Roudix at it. That
# user-level symlink shadows the static theme of the same name, so every config
# that says "Bibata-Modern-Roudix" (GTK, XCURSOR_THEME, compositor configs)
# picks up the new colours the next time it loads the theme.
#
# The previous revision is kept for one cycle (a compositor may still be using
# it) and older ones created by this script are pruned.
#
# Same Noctalia-template mechanism as tela-icon.nix / papirus-icon.nix.
# Approach borrowed from Ly-sec's cursor module.
{ lib, pkgs, osConfig, roudix-cursor, ... }:

let
  desktopType = osConfig.roudix.desktop.type;
  shellType   = osConfig.roudix.desktop.shell or "noctalia";

  # Same "bare compositor" set as gtk-theme.nix's needsGtkTheme, minus COSMIC
  # (own cursor handling) — and only with Noctalia, which provides the palette.
  live = shellType == "noctalia"
    && builtins.elem desktopType [ "niri" "hyprland" "mangowc" "umbriel" ];

  theme = roudix-cursor.themeName;
  size  = 24;

  syncScript = pkgs.writeShellApplication {
    name = "roudix-cursor-sync";
    runtimeInputs = [
      pkgs.clickgen
      pkgs.coreutils
      pkgs.findutils
      pkgs.imagemagick
    ];
    text = ''
      accent="''${1:-}"
      outline="''${2:-}"

      if [[ ! "$accent" =~ ^[0-9A-Fa-f]{6}$ || ! "$outline" =~ ^[0-9A-Fa-f]{6}$ ]]; then
        echo "usage: roudix-cursor-sync RRGGBB RRGGBB" >&2
        exit 2
      fi

      theme='${theme}'
      runtime="$theme-$accent-$outline"
      icons_dir="''${XDG_DATA_HOME:-$HOME/.local/share}/icons"
      target="$icons_dir/$runtime"
      previous=""

      install -dm0755 "$icons_dir"

      # Never replace something that is not our own symlink.
      if [[ -e "$icons_dir/$theme" && ! -L "$icons_dir/$theme" ]]; then
        echo "roudix-cursor-sync: $icons_dir/$theme exists and is not a symlink, leaving it alone" >&2
        exit 1
      fi

      if [[ -L "$icons_dir/$theme" ]]; then
        candidate="$(readlink "$icons_dir/$theme")"
        if [[ "$candidate" =~ ^$theme-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}$ ]]; then
          previous="$candidate"
        fi
      fi

      # Same palette as the active revision (the hook can fire more than once):
      # nothing to do, and do not prune the previous revision yet.
      if [[ "$previous" == "$runtime" && -d "$target/cursors" ]]; then
        exit 0
      fi

      if [[ ! -d "$target/cursors" ]]; then
        work_dir="$(mktemp -d "$icons_dir/.roudix-cursor-build.XXXXXX")"
        trap 'rm -rf -- "$work_dir"' EXIT

        install -dm0755 "$work_dir/bitmaps/$theme"
        cp -r ${pkgs.bibata-cursors.bitmaps}/Bibata-Modern-Ice/. "$work_dir/bitmaps/$theme/"
        chmod -R u+w "$work_dir/bitmaps/$theme"

        magick mogrify \
          -channel RGB \
          +level-colors "#$outline,#$accent" \
          -type TrueColorAlpha \
          -define png:color-type=6 \
          "$work_dir/bitmaps/$theme"/*.png

        cd "$work_dir"
        ctgen ${pkgs.bibata-cursors.src}/configs/normal/x.build.toml \
          -p x11 \
          -d "bitmaps/$theme" \
          -o "$work_dir/themes" \
          -n "$theme" \
          -c 'Bibata Modern cursor in the Roudix/Noctalia palette' \
          >/dev/null

        if [[ ! -e "$target" ]]; then
          mv "themes/$theme" "$target"
        fi
      fi

      # Atomic swap of the alias symlink.
      ln -sfn "$runtime" "$icons_dir/.$theme.tmp"
      mv -Tf "$icons_dir/.$theme.tmp" "$icons_dir/$theme"

      # Hyprland can switch the cursor of the running session right away.
      if [[ -n "''${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && command -v hyprctl >/dev/null 2>&1; then
        hyprctl setcursor "$runtime" ${toString size} >/dev/null 2>&1 || true
      fi

      # Keep the previous revision for one cycle, prune older ones (only
      # directories this script could have created).
      while IFS= read -r -d "" candidate; do
        name="''${candidate##*/}"
        if [[ "$name" =~ ^$theme-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}$ \
          && "$name" != "$runtime" \
          && "$name" != "$previous" ]]; then
          rm -rf -- "$candidate"
        fi
      done < <(find "$icons_dir" -mindepth 1 -maxdepth 1 -type d -name "$theme-*" -print0)
    '';
  };

  # What Noctalia renders on every palette change. Hex values are inserted by
  # Noctalia exactly as passed to the hook below, so the names always match.
  revision = "${theme}-{{colors.primary.default.hex_stripped}}-{{colors.terminal_background.default.hex_stripped}}";

  # Umbriel reloads its config when an included file changes, and re-applies
  # the cursor only if the theme *name* changed — hence a name that carries the
  # colours. Needs _include-cursor.nix (opt-in, see its header).
  # Everywhere else the rendered file is just a marker that fires the hook.
  template =
    if desktopType == "umbriel"
    then ''
      [input.cursor]
      theme = "${revision}"
    ''
    else revision;

  outputPath =
    if desktopType == "umbriel"
    then "~/.config/umbriel/bibata-cursor.toml"
    else "~/.config/noctalia/generated/roudix-cursor.txt";
in
{
  config = lib.mkIf live {
    home.packages = [ syncScript ];

    xdg.configFile."noctalia/templates/roudix-cursor.tmpl".text = template;

    # pre_hook: the cursor theme must exist on disk before the rendered file
    # (and Umbriel's reload) refers to it.
    xdg.configFile."noctalia/60-roudix-cursor.toml".text = ''
      [theme.templates.user.roudix_cursor]
      input_path  = "~/.config/noctalia/templates/roudix-cursor.tmpl"
      output_path = "${outputPath}"
      pre_hook    = "${lib.getExe syncScript} {{colors.primary.default.hex_stripped}} {{colors.terminal_background.default.hex_stripped}}"
    '';
  };
}

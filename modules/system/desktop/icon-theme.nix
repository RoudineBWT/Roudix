{ config, lib, pkgs, ... }:
let
  cfg = config.roudix.iconTheme;

  # ── Roudix icon themes: Papirus-Roudix / Tela-Roudix ─────────────────────
  # Same idea as the Noctalia recolor scripts (modules/home/theming/
  # papirus-icon.nix, tela-icon.nix), but built once by Nix, with the fixed
  # Roudix primary from assets/palette/Roudix.json instead of generated at
  # runtime. The theme only contains the "places" icons (the folders, home,
  # desktop...) plus the file-manager app icons (system-file-manager, nemo...)
  # recolored; everything else is inherited from the stock Papirus-Dark /
  # Tela-dark, which therefore has to be installed next to it.
  # Result: orange folders and file manager on every desktop, a handful of
  # copied app icons, zero risk of breaking anything else.
  palette = builtins.fromJSON (builtins.readFile ../../../assets/palette/Roudix.json);
  primary = palette.dark.mPrimary;
  secondary = palette.dark.mSecondary;

  # Papirus draws its folders with two shades: #5294e2 (body) and #4877b1 (tab,
  # ~80 % of the body). Same ratio for the Roudix primary.
  hex     = lib.removePrefix "#" primary;
  channel = i: lib.fromHexString (builtins.substring i 2 hex);
  darker  = "#" + lib.concatMapStrings
    (i: lib.fixedWidthString 2 "0" (lib.toHexString (channel i * 80 / 100)))
    [ 0 2 4 ];

  # File-manager app icons (what the panel / dock shows for Nemo, Nautilus,
  # Dolphin...). Papirus: system-file-manager is the 3-tab cabinet; Tela:
  # system-file-manager -> file-manager.svg is the blue folder.
  fileManagerApps = [
    "system-file-manager" "file-manager" "nemo" "org.gnome.Nautilus"
    "org.kde.dolphin" "dolphin" "org.xfce.filemanager" "thunar"
  ];

  mkRoudixIcons = { name, title, base, baseName, sizes, extraSed ? "", appSed }:
    pkgs.runCommand "${lib.toLower name}-icon-theme" { } ''
      src="${base}/share/icons/${baseName}"
      dest="$out/share/icons/${name}"
      mkdir -p "$dest"

      # Same index.theme as the base theme, inheriting from it for every icon
      # not provided here.
      sed -e "s/^Inherits=.*/Inherits=${baseName}/" \
          -e "s/^Name=.*/Name=${title}/" \
          "$src/index.theme" > "$dest/index.theme"

      # "places" only, for each size the base theme has. -L dereferences the
      # internal / cross-variant symlinks (e.g. Papirus-Dark/48x48 -> ../Papirus/48x48).
      for size in ${lib.concatStringsSep " " sizes}; do
        [ -d "$src/$size/places" ] || continue
        mkdir -p "$dest/$size/places"
        cp -rL "$src/$size/places/." "$dest/$size/places/"
      done

      # File-manager app icons: same size loop, apps/ folder, only the names
      # in fileManagerApps (missing ones are skipped).
      for size in ${lib.concatStringsSep " " sizes}; do
        for app in ${lib.concatStringsSep " " fileManagerApps}; do
          f="$src/$size/apps/$app.svg"
          [ -e "$f" ] || continue
          mkdir -p "$dest/$size/apps"
          cp -L "$f" "$dest/$size/apps/$app.svg"
        done
      done
      chmod -R u+w "$dest"

      find "$dest" -path '*/places/*.svg' -print0 | xargs -0 -r sed -i \
        -e "s/#5294e2/${primary}/Ig" \
        ${extraSed}

      # Recolor the copied file-manager icons (palette differs per theme).
      find "$dest" -path '*/apps/*.svg' -print0 | xargs -0 -r sed -i \
        ${appSed}
    '';

  papirusRoudix = mkRoudixIcons {
    name     = "Papirus-Roudix";
    title    = "Papirus Roudix";
    base     = pkgs.papirus-icon-theme;
    baseName = "Papirus-Dark";
    sizes    = [ "16x16" "22x22" "24x24" "32x32" "48x48" "64x64" "96x96" "128x128" "scalable" "symbolic" ];
    extraSed = ''-e "s/#4877b1/${darker}/Ig"'';
    # Cabinet tabs: blue (#5294e2, or #5895dc at small sizes) -> primary,
    # green -> secondary, yellow -> palette's bright yellow.
    appSed   = ''-e "s/#5294e2/${primary}/Ig" -e "s/#5895dc/${primary}/Ig" -e "s/#89e058/${secondary}/Ig" -e "s/#ffcd54/#FFC878/Ig"'';
  };

  telaRoudix = mkRoudixIcons {
    name     = "Tela-Roudix";
    title    = "Tela Roudix";
    base     = pkgs.tela-icon-theme;
    baseName = "Tela-dark";
    sizes    = [ "16" "22" "24" "32" "scalable" "symbolic" ];
    # file-manager.svg: blue folder (#5294e2); nemo.svg: green folder (#4ed09d).
    appSed   = ''-e "s/#5294e2/${primary}/Ig" -e "s/#4ed09d/${primary}/Ig"'';
  };

  # Curated ids -> theme name + the packages that provide it. Anything else is
  # taken as a literal icon-theme name the user made available himself.
  curated = {
    papirus  = { name = "Papirus-Roudix"; packages = [ papirusRoudix pkgs.papirus-icon-theme ]; };
    tela     = { name = "Tela-Roudix";    packages = [ telaRoudix pkgs.tela-icon-theme ]; };
    qogir    = { name = "Qogir-dark";     packages = [ pkgs.qogir-icon-theme ]; };
    whitesur = { name = "WhiteSur-dark";  packages = [ pkgs.whitesur-icon-theme ]; };
    colloid  = { name = "Colloid-dark";   packages = [ pkgs.colloid-icon-theme ]; };
  };
  chosen = curated.${cfg} or { name = cfg; packages = [ ]; };

  # Desktops with their own native icon setting, seeded from this option as a
  # DEFAULT (dconf / kdeglobals / cosmic-config): the user's own pick in the
  # desktop's settings app wins. The bare compositors go through
  # modules/home/theming/gtk-theme.nix instead.
  nativeDesktops = [ "gnome" "kde" "cinnamon" "cosmic" ];
in
{
  options.roudix.iconTheme = lib.mkOption {
    # Free-form string, not an enum: modules/home/theming/gtk-theme.nix special-cases
    # the curated ids below (installs the matching nixpkgs package) and
    # treats anything else as a literal GTK icon-theme name already present
    # on the system (roudix-switcher's icon-theme scan writes those) —
    # never a package reference, so a typo/unknown name can't break a
    # rebuild, it just falls back to hicolor icons at runtime.
    type    = lib.types.str;
    default = "papirus";
    description = ''
      Curated choices (each pulls in its own nixpkgs package):
        "papirus"  : Papirus-Roudix on GNOME / KDE / Cinnamon / COSMIC (Papirus-Dark
                     with the folders in the Roudix primary, see above); plain
                     Papirus-Dark on the bare compositors — Roudix's original default.
        "tela"     : Tela-Roudix on GNOME / KDE / Cinnamon / COSMIC. On the bare
                     compositors, when roudix.desktop.shell = "noctalia", this
                     is the Noctalia-recolored variant generated by
                     modules/home/theming/tela-icon.nix (~/.icons/Tela-dark-noctalia)
                     — first recolor happens on the next Noctalia
                     theme/accent change, not immediately on switch. Any
                     other shell falls back to plain Tela-dark from nixpkgs.
        "qogir"    : Qogir-dark (pkgs.qogir-icon-theme).
        "whitesur" : WhiteSur-dark (pkgs.whitesur-icon-theme).
        "colloid"  : Colloid-dark (pkgs.colloid-icon-theme).

      Any other value is taken as a literal icon-theme name (the folder's
      own name, e.g. "Numix-Circle") that you've made available yourself —
      via home.packages in modules/home/local.nix, or sitting in ~/.icons.
      roudix-switcher's "Icon Theme" page scans both locations and lists
      whatever it finds beyond the curated set above.
    '';
  };

  # Name of the theme the native-icon desktops should default to.
  options.roudix.iconThemeName = lib.mkOption {
    type     = lib.types.str;
    readOnly = true;
    internal = true;
    default  = chosen.name;
    description = "Resolved icon-theme name for roudix.iconTheme (GNOME / KDE / Cinnamon / COSMIC defaults).";
  };

  config = lib.mkIf (builtins.elem config.roudix.desktop.type nativeDesktops) {
    environment.systemPackages = chosen.packages;
  };
}

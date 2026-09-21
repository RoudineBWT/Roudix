{ lib, pkgs }:
let
  # Icon-theme packages kept around purely so the "Icon Theme" page can show
  # each theme's own real "folder" glyph as a live preview (see
  # _theme_preview_icon() in roudix-switcher.py) instead of hand-drawn
  # placeholder art. Picking a theme in the UI does NOT depend on these
  # being installed system-wide — modules/home/gtk-theme.nix pulls in
  # whichever one is actually selected via roudix.iconTheme on its own.
  iconThemesForPreview = with pkgs; [
    papirus-icon-theme
    tela-icon-theme
    qogir-icon-theme
    whitesur-icon-theme
    colloid-icon-theme
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "roudix-switcher";
  version = "2.0.0";
  src = ./.;
  nativeBuildInputs = with pkgs; [
    wrapGAppsHook4
    gobject-introspection
  ];
  buildInputs = with pkgs; [
    gtk4
    libadwaita
    (python3.withPackages (ps: with ps; [
      pygobject3
    ]))
  ];
  # wrapGAppsHook4 picks this array up automatically in its own fixupPhase
  # wrapping — no separate wrapProgram call needed.
  preFixup = ''
    gappsWrapperArgs+=(
      --set ROUDIX_ICON_THEME_PREVIEW_PATH "${lib.concatMapStringsSep ":" (p: "${p}/share/icons") iconThemesForPreview}"
    )
  '';
  installPhase = ''
    mkdir -p $out/bin $out/share/applications \
      $out/share/icons/hicolor/scalable/apps \
      $out/share/icons/hicolor/symbolic/apps \
      $out/share/roudix-switcher $out/share/polkit-1/actions
    # Install the Python script
    cp roudix-switcher.py $out/bin/roudix-switcher
    chmod +x $out/bin/roudix-switcher
    patchShebangs $out/bin/roudix-switcher
    # Install the custom icons folders
    cp -r icons $out/share/roudix-switcher/
    # Install app icon (dark — default)
    cp roudix-switcher.svg $out/share/icons/hicolor/scalable/apps/io.roudix.switcher.svg
    # Install app icon (light — for Papirus-Light / light themes)
    cp roudix-switcher-light.svg $out/share/icons/hicolor/scalable/apps/io.roudix.switcher-light.svg
    # Install Polkit policy
    cp io.roudix.switcher.policy $out/share/polkit-1/actions/
    # Install .desktop file
    cat > $out/share/applications/io.roudix.switcher.desktop << EOF
    [Desktop Entry]
    Name=Roudix Customizer
    Comment=Customize your desktop, apps and system tweaks on Roudix
    Exec=roudix-switcher
    Icon=io.roudix.switcher
    Terminal=false
    Type=Application
    Categories=System;Settings;
    Keywords=desktop;environment;switch;niri;hyprland;gnome;kde;customize;browser;editor;terminal;gaming;
    EOF
  '';
  meta = {
    description = "Customize your desktop, apps and system tweaks on Roudix";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

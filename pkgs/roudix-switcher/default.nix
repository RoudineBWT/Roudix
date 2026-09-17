{ lib, pkgs }:
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

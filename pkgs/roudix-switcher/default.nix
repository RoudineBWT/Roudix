{ lib, pkgs }:

pkgs.stdenv.mkDerivation {
  pname = "roudix-switcher";
  version = "1.0.4";

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
    mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps $out/share/roudix-switcher

    # Install the Python script
    cp roudix-switcher.py $out/bin/roudix-switcher
    chmod +x $out/bin/roudix-switcher
    patchShebangs $out/bin/roudix-switcher
    # Install the custom icons folders
    cp -r icons $out/share/roudix-switcher/

    # Install .desktop file
    cat > $out/share/applications/io.roudix.switcher.desktop << EOF
    [Desktop Entry]
    Name=Roudix Desktop Switcher
    Comment=Switch between desktop environments
    Exec=roudix-switcher
    Icon=preferences-desktop-display
    Terminal=false
    Type=Application
    Categories=System;Settings;
    Keywords=desktop;environment;switch;niri;gnome;kde;
    EOF
  '';

  meta = {
    description = "Switch desktop environments on Roudix";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

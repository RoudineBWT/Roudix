{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-kernel-switcher";
  version = "1.0.0";
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
    mkdir -p $out/bin \
              $out/share/applications \
              $out/share/icons/hicolor/scalable/apps

    # Script principal
    cp roudix-kernel-switcher.py $out/bin/roudix-kernel-switcher
    chmod +x $out/bin/roudix-kernel-switcher
    patchShebangs $out/bin/roudix-kernel-switcher

    # Icône
    if [ -f roudix-kernel-switcher.svg ]; then
      cp roudix-kernel-switcher.svg \
        $out/share/icons/hicolor/scalable/apps/io.roudix.kernel-switcher.svg
    fi

    # Entrée .desktop
    cat > $out/share/applications/io.roudix.kernel-switcher.desktop << EOF
    [Desktop Entry]
    Name=Roudix Kernel Switcher
    Comment=Switch between CachyOS kernel variants
    Exec=roudix-kernel-switcher
    Icon=io.roudix.kernel-switcher
    Terminal=false
    Type=Application
    Categories=System;Settings;
    Keywords=kernel;cachyos;nix;switch;boot;
    EOF
  '';

  meta = {
    description = "Switch CachyOS kernel variants on Roudix";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-hw-sync";
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

    # CLI (all the logic) — also what the GUI drives
    cp roudix-hw-sync $out/bin/roudix-hw-sync
    chmod +x $out/bin/roudix-hw-sync
    patchShebangs $out/bin/roudix-hw-sync

    # GUI
    cp roudix-hw-sync-gui.py $out/bin/roudix-hw-sync-gui
    chmod +x $out/bin/roudix-hw-sync-gui
    patchShebangs $out/bin/roudix-hw-sync-gui

    # Icon
    cp roudix-hw-sync.svg \
      $out/share/icons/hicolor/scalable/apps/io.roudix.hw-sync.svg

    # .desktop entry
    cat > $out/share/applications/io.roudix.hw-sync.desktop << EOF
    [Desktop Entry]
    Name=Roudix Hardware Sync
    Comment=Changed PC? Update your CPU/GPU settings
    Exec=roudix-hw-sync-gui
    Icon=io.roudix.hw-sync
    Terminal=false
    Type=Application
    Categories=System;Settings;X-Roudix;
    Keywords=gpu;cpu;nvidia;amd;intel;hardware;pc;nix;
    EOF
  '';

  meta = {
    description = "Re-detect CPU/GPU after a hardware change and update Roudix's local.nix (GUI + CLI)";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

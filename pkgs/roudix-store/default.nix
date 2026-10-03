{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-store";
  version = "0.1.0";
  src = ./.;
  nativeBuildInputs = with pkgs; [ wrapGAppsHook4 gobject-introspection ];
  buildInputs = with pkgs; [
    gtk4
    libadwaita
    (python3.withPackages (ps: with ps; [ pygobject3 brotli ]))
  ];
  installPhase = ''
    mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
    cp roudix-store.py $out/bin/roudix-store
    chmod +x $out/bin/roudix-store
    patchShebangs $out/bin/roudix-store
    cp io.roudix.store.svg $out/share/icons/hicolor/scalable/apps/io.roudix.store.svg
    cat > $out/share/applications/io.roudix.store.desktop << EOF2
    [Desktop Entry]
    Name=Roudix Store
    Comment=Search and install nixpkgs apps, written to your local.nix
    Exec=roudix-store
    Icon=io.roudix.store
    Terminal=false
    Type=Application
    Categories=System;PackageManager;
    Keywords=store;software;apps;packages;nixpkgs;install;
    EOF2
  '';
  meta = {
    description = "Software center for Roudix: nixpkgs search, installs recorded in local.nix";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

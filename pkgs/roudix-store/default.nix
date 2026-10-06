{ lib, pkgs, nixos-appstream-data }:
let
  py = pkgs.python3.withPackages (ps: with ps; [ pygobject3 brotli ]);
in
pkgs.stdenv.mkDerivation {
  pname = "roudix-store";
  version = "0.2.0";
  src = ./.;
  dontBuild = true;

  nativeBuildInputs = with pkgs; [ wrapGAppsHook4 gobject-introspection ];
  buildInputs = with pkgs; [ gtk4 libadwaita gdk-pixbuf appstream py ];

  installPhase = ''
    mkdir -p $out/bin $out/share/roudix-store $out/share/applications \
             $out/share/icons/hicolor/scalable/apps
    cp -r roudix_store $out/share/roudix-store/
    # app icon (dark — default) + light variant for light icon themes
    cp io.roudix.store.svg $out/share/icons/hicolor/scalable/apps/
    cp io.roudix.store-light.svg $out/share/icons/hicolor/scalable/apps/

    cat > $out/bin/roudix-store << EOF2
    #!${py}/bin/python3
    import sys
    sys.path.insert(0, "$out/share/roudix-store")
    from roudix_store.main import main
    sys.exit(main())
    EOF2
    chmod +x $out/bin/roudix-store

    cat > $out/share/applications/io.roudix.store.desktop << EOF2
    [Desktop Entry]
    Name=Roudix Store
    Comment=Browse and install nixpkgs apps, recorded in your local.nix
    Comment[fr]=Parcourir et installer des applications nixpkgs et Flatpak, enregistrées dans ton local.nix
    Exec=roudix-store
    Icon=io.roudix.store
    Terminal=false
    Type=Application
    Categories=System;PackageManager;X-Roudix;
    Keywords=store;software;apps;packages;nixpkgs;install;
    EOF2
  '';

  # AppStream catalog + icons for nixpkgs (read by roudix_store/appstream_catalog.py)
  preFixup = ''
    gappsWrapperArgs+=(--set ROUDIX_STORE_CATALOG "${nixos-appstream-data}/share/swcatalog")
  '';

  meta = {
    description = "Software center for Roudix: nixpkgs apps with icons, installs recorded in local.nix";
    # UI derived from Nobara's dnf-app-center (GPL-2.0)
    license = lib.licenses.gpl2Only;
    platforms = lib.platforms.linux;
    mainProgram = "roudix-store";
  };
}

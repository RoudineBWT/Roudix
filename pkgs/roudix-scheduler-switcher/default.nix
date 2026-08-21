{ lib
, stdenv
, python3
, gtk4
, libadwaita
, gobject-introspection
, wrapGAppsHook4
, makeWrapper
, scxctl        # passé depuis flake.nix / callPackage (inputs.roudix-caches.packages.${system}.scxctl)
, systemd
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.pygobject3 ]);
in
stdenv.mkDerivation {
  pname = "roudix-scheduler";
  version = "1.0.0";

  src = ./roudix-scheduler.py;
  dontUnpack = true;

  # wrapGAppsHook4 wrappe automatiquement tout exécutable sous $out/bin
  # durant fixupPhase, en injectant GI_TYPELIB_PATH / XDG_DATA_DIRS /
  # GSETTINGS_SCHEMA_DIR calculés sur toute la fermeture transitive de
  # buildInputs (gtk4 propage déjà Pango, GdkPixbuf, Graphene, HarfBuzz,
  # GLib...). Évite d'avoir à lister les typelibs à la main un par un.
  nativeBuildInputs = [ makeWrapper wrapGAppsHook4 gobject-introspection ];
  buildInputs = [ gtk4 libadwaita ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps

    install -Dm755 $src $out/bin/roudix-scheduler
    substituteInPlace $out/bin/roudix-scheduler \
      --replace "#!/usr/bin/env python3" "#!${pythonEnv}/bin/python3"

    install -Dm644 ${./io.roudix.scheduler-dark.svg} \
      $out/share/icons/hicolor/scalable/apps/io.roudix.scheduler.svg
    install -Dm644 ${./io.roudix.scheduler-light.svg} \
      $out/share/icons/hicolor/scalable/apps/io.roudix.scheduler-light.svg

    cat > $out/share/applications/io.roudix.scheduler.desktop <<EOF
    [Desktop Entry]
    Type=Application
    Name=Roudix Scheduler
    Comment=Choose and apply an SCX scheduler
    Exec=$out/bin/roudix-scheduler
    Icon=io.roudix.scheduler
    Categories=System;Settings;
    EOF

    runHook postInstall
  '';

  # Ajoute scxctl/systemd au PATH, en plus de tout ce que wrapGAppsHook4
  # configure déjà automatiquement pour GTK4/Adwaita.
  preFixup = ''
    gappsWrapperArgs+=(--prefix PATH : ${lib.makeBinPath [ scxctl systemd ]})
  '';

  meta = {
    description = "GTK4/Adwaita picker for SCX schedulers (Roudix)";
    mainProgram = "roudix-scheduler";
    platforms = lib.platforms.linux;
  };
}

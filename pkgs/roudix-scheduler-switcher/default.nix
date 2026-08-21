{ lib
, stdenv
, python3
, gtk4
, libadwaita
, gobject-introspection
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

  nativeBuildInputs = [ makeWrapper gobject-introspection ];
  buildInputs = [ gtk4 libadwaita ];

  installPhase = ''
    mkdir -p $out/bin $out/share/applications

    install -Dm755 $src $out/bin/roudix-scheduler
    substituteInPlace $out/bin/roudix-scheduler \
      --replace "#!/usr/bin/env python3" "#!${pythonEnv}/bin/python3"

    wrapProgram $out/bin/roudix-scheduler \
      --prefix PATH : ${lib.makeBinPath [ scxctl systemd ]} \
      --set GI_TYPELIB_PATH "${lib.makeSearchPath "lib/girepository-1.0" [ gtk4 libadwaita ]}"

    cat > $out/share/applications/io.roudix.scheduler.desktop <<EOF
    [Desktop Entry]
    Type=Application
    Name=Roudix Scheduler
    Comment=Choose and apply an SCX scheduler
    Exec=$out/bin/roudix-scheduler
    Icon=utilities-system-monitor
    Categories=System;Settings;
    EOF
  '';

  meta = {
    description = "GTK4/Adwaita picker for SCX schedulers (Roudix)";
    mainProgram = "roudix-scheduler";
    platforms = lib.platforms.linux;
  };
}

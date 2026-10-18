{ lib, pkgs }:
let
  # One interpreter for both front-ends: PyGObject (GUI) + Textual (TUI).
  py = pkgs.python3.withPackages (ps: with ps; [
    pygobject3
    textual
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "roudix-config";
  version = "0.1.0";
  src = ./.;

  nativeBuildInputs = with pkgs; [
    wrapGAppsHook4
    gobject-introspection
  ];

  buildInputs = with pkgs; [
    gtk4
    libadwaita
    adwaita-icon-theme
    py
  ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/lib/roudix-config $out/share/applications \
             $out/share/icons/hicolor/scalable/apps
    cp roudix_config_core.py $out/lib/roudix-config/

    # The sources start with a 2-line `nix-shell` shebang so they also run
    # straight from a checkout. Packaged copies use the env python instead
    # (wrapGAppsHook4 then adds the GTK/libadwaita typelibs and schemas).
    #   roudix-config      → GUI (what the launcher starts)
    #   roudix-config-tui  → terminal version (SSH / TTY)
    for pair in "roudix-config-gui.py:roudix-config" "roudix-config.py:roudix-config-tui"; do
      from=''${pair%%:*}
      to=''${pair##*:}
      { echo '#!${py}/bin/python3'; tail -n +3 "$from"; } > "$out/bin/$to"
      chmod +x "$out/bin/$to"
    done

    # Own icon, same convention as roudix-store / roudix-switcher: dark badge
    # by default + a -light variant, in hicolor so any icon theme falls back to it.
    cp io.roudix.config.svg io.roudix.config-light.svg $out/share/icons/hicolor/scalable/apps/

    cat > $out/share/applications/io.roudix.config.desktop << EOF2
    [Desktop Entry]
    Name=Roudix Config
    Comment=Configure Umbriel — règles de fenêtres, écrans, workspaces, raccourcis
    Exec=roudix-config
    Icon=io.roudix.config
    Terminal=false
    Type=Application
    StartupNotify=true
    Categories=System;Settings;X-Roudix;
    Keywords=umbriel;config;raccourcis;écrans;workspaces;règles;fenêtres;
    EOF2

    runHook postInstall
  '';

  meta = {
    description = "Roudix Config : configure Umbriel (règles de fenêtres, écrans, workspaces, raccourcis) sans écrire de Nix";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "roudix-config";
  };
}

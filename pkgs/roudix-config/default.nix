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

    mkdir -p $out/bin $out/lib/roudix-config $out/share/applications
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

    # Icon: reuse roudix-logo (roudix-branding, already in hicolor), like
    # roudix-welcome does, instead of shipping a duplicate.
    cat > $out/share/applications/io.roudix.config.desktop << EOF2
    [Desktop Entry]
    Name=Roudix Config
    Comment=Configure Umbriel — règles de fenêtres, écrans, workspaces, raccourcis
    Exec=roudix-config
    Icon=roudix-logo
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

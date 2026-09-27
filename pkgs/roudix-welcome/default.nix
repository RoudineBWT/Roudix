{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-welcome";
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
              $out/share/roudix-welcome

    # Script principal
    cp roudix-welcome.py $out/bin/roudix-welcome
    chmod +x $out/bin/roudix-welcome
    patchShebangs $out/bin/roudix-welcome

    # Pas d'icône propre : la fenêtre affiche roudix-logo (roudix-branding,
    # déjà installée dans hicolor à toutes les tailles). Le lanceur du menu
    # réutilise donc directement cette icône plutôt que d'en dupliquer une.
    cat > $out/share/applications/io.roudix.welcome.desktop << EOF
    [Desktop Entry]
    Name=Roudix Welcome
    Comment=Bienvenue sur Roudix — accès rapide aux outils de personnalisation
    Exec=roudix-welcome
    Icon=roudix-logo
    Terminal=false
    Type=Application
    Categories=System;Settings;
    Keywords=welcome;bienvenue;switcher;kernel;scheduler;
    EOF
  '';

  meta = {
    description = "Écran de bienvenue Roudix : accès rapide à roudix-switcher, roudix-kernel-switcher et roudix-scheduler";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

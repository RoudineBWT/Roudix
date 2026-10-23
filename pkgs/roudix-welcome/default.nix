{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-welcome";
  version = "1.0.0";
  src = ./.;

  nativeBuildInputs = with pkgs; [
    wrapGAppsHook4
    gobject-introspection
    gettext
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
    Comment=Welcome to Roudix — quick access to the customization tools
    Comment[fr]=Bienvenue sur Roudix — accès rapide aux outils de personnalisation
    Comment[es]=Te damos la bienvenida a Roudix — acceso rápido a las herramientas de personalización
    Comment[pt_BR]=Bem-vindo ao Roudix — acesso rápido às ferramentas de personalização
    Comment[ru]=Добро пожаловать в Roudix — быстрый доступ к инструментам настройки
    Comment[zh_CN]=欢迎使用 Roudix — 快速访问各种定制工具
    Comment[hi]=Roudix में आपका स्वागत है — अनुकूलन टूल्स तक त्वरित पहुँच
    Comment[ar]=مرحبًا بك في Roudix — وصول سريع إلى أدوات التخصيص
    Exec=roudix-welcome
    Icon=roudix-logo
    Terminal=false
    Type=Application
    Categories=System;Settings;X-Roudix;
    Keywords=welcome;bienvenue;switcher;kernel;scheduler;store;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-welcome.mo
    # (the app looks them up relative to its own install prefix: see tr() in the sources)
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-welcome.mo" "$po"
    done
  '';

  meta = {
    description = "Écran de bienvenue Roudix : accès rapide à roudix-store, roudix-switcher, roudix-kernel-switcher et roudix-scheduler";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

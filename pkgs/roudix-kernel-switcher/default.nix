{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-kernel-switcher";
  version = "2.0.0";
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
              $out/share/icons/hicolor/scalable/apps

    # Script principal
    cp roudix-kernel-switcher.py $out/bin/roudix-kernel-switcher
    chmod +x $out/bin/roudix-kernel-switcher
    patchShebangs $out/bin/roudix-kernel-switcher

    # Icon
    if [ -f roudix-kernel-switcher.svg ]; then
      cp roudix-kernel-switcher.svg \
        $out/share/icons/hicolor/scalable/apps/io.roudix.kernel-switcher.svg
    fi

    # .desktop entry
    cat > $out/share/applications/io.roudix.kernel-switcher.desktop << EOF
    [Desktop Entry]
    Name=Roudix Kernel Switcher
    Comment=Switch between CachyOS kernel variants
    Comment[fr]=Bascule entre les variantes du noyau CachyOS
    Comment[es]=Cambia entre las variantes del kernel de CachyOS
    Comment[pt_BR]=Alterne entre as variantes do kernel CachyOS
    Comment[ru]=Переключение между вариантами ядра CachyOS
    Comment[zh_CN]=在 CachyOS 内核变体之间切换
    Comment[hi]=CachyOS कर्नल वेरिएंट के बीच स्विच करें
    Comment[ar]=التبديل بين متغيّرات نواة CachyOS
    Exec=roudix-kernel-switcher
    Icon=io.roudix.kernel-switcher
    Terminal=false
    Type=Application
    Categories=System;Settings;X-Roudix;
    Keywords=kernel;cachyos;nix;switch;boot;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-kernel-switcher.mo
    # (the app looks them up relative to its own install prefix: see tr() in the sources)
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-kernel-switcher.mo" "$po"
    done
  '';

  meta = {
    description = "Switch CachyOS kernel variants on Roudix (xddxdd or Chaotic-Nyx, depending on hardware.myGpu)";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

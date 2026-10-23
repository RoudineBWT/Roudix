{ lib, pkgs }:
pkgs.stdenv.mkDerivation {
  pname = "roudix-hw-sync";
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
              $out/share/icons/hicolor/scalable/apps

    # CLI (all the logic) — also what the GUI drives
    cp roudix-hw-sync $out/bin/roudix-hw-sync
    chmod +x $out/bin/roudix-hw-sync
    patchShebangs $out/bin/roudix-hw-sync
    # Translations of the CLI's messages: where the catalogs end up + the gettext binary
    substituteInPlace $out/bin/roudix-hw-sync \
      --replace-fail '@localedir@' "$out/share/locale" \
      --replace-fail '@gettext@' "${pkgs.gettext}/bin/gettext"

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
    Comment[fr]=Changement de PC ? Mets à jour tes réglages CPU/GPU
    Comment[es]=¿Cambiaste de PC? Actualiza tus ajustes de CPU/GPU
    Comment[pt_BR]=Trocou de PC? Atualize as configurações de CPU/GPU
    Comment[ru]=Сменили ПК? Обновите настройки CPU/GPU
    Comment[zh_CN]=换了电脑？更新你的 CPU/GPU 设置
    Comment[hi]=PC बदला? अपनी CPU/GPU सेटिंग्स अपडेट करें
    Comment[ar]=غيّرت حاسوبك؟ حدّث إعدادات المعالج وبطاقة الرسوميات
    Exec=roudix-hw-sync-gui
    Icon=io.roudix.hw-sync
    Terminal=false
    Type=Application
    Categories=System;Settings;X-Roudix;
    Keywords=gpu;cpu;nvidia;amd;intel;hardware;pc;nix;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-hw-sync.mo
    # (the GUI looks them up relative to its own install prefix: see tr() in the sources;
    # the CLI gets the path substituted above)
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-hw-sync.mo" "$po"
    done
  '';

  meta = {
    description = "Re-detect CPU/GPU after a hardware change and update Roudix's local.nix (GUI + CLI)";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}

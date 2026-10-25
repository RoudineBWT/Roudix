{ lib
, stdenv
, python3
, gtk4
, libadwaita
, adwaita-icon-theme
, gobject-introspection
, wrapGAppsHook4
, gettext
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.pygobject3 ]);
in
stdenv.mkDerivation {
  pname = "roudix-firewall";
  version = "1.0.0";

  # The whole directory: the app, its GTK-free core, po/ (compiled to .mo below).
  src = ./.;

  # wrapGAppsHook4 wraps every executable under $out/bin and injects
  # GI_TYPELIB_PATH / XDG_DATA_DIRS for GTK4 + libadwaita.
  nativeBuildInputs = [ wrapGAppsHook4 gobject-introspection gettext ];
  buildInputs = [ gtk4 libadwaita adwaita-icon-theme ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/lib/roudix-firewall $out/share/applications \
             $out/share/icons/hicolor/scalable/apps

    # The core sits next to nothing else: the app finds it in ../lib/roudix-firewall
    # (and next to itself when run from a checkout).
    install -Dm644 roudix_firewall_core.py $out/lib/roudix-firewall/roudix_firewall_core.py

    # The source starts with an env shebang so it also runs from a checkout;
    # the packaged copy uses the Python that has PyGObject.
    { echo '#!${pythonEnv}/bin/python3'; tail -n +2 roudix-firewall.py; } > $out/bin/roudix-firewall
    chmod +x $out/bin/roudix-firewall

    install -Dm644 io.roudix.firewall.svg \
      $out/share/icons/hicolor/scalable/apps/io.roudix.firewall.svg
    install -Dm644 io.roudix.firewall-light.svg \
      $out/share/icons/hicolor/scalable/apps/io.roudix.firewall-light.svg

    cat > $out/share/applications/io.roudix.firewall.desktop <<EOF
    [Desktop Entry]
    Type=Application
    Name=Roudix Firewall
    Name[fr]=Pare-feu Roudix
    Name[es]=Cortafuegos de Roudix
    Name[pt_BR]=Firewall do Roudix
    Name[ru]=Брандмауэр Roudix
    Name[zh_CN]=Roudix 防火墙
    Name[hi]=Roudix फ़ायरवॉल
    Name[ar]=جدار حماية Roudix
    Comment=Manage the firewall: open ports and trusted interfaces
    Comment[fr]=Gère le pare-feu : ports ouverts et interfaces de confiance
    Comment[es]=Gestiona el cortafuegos: puertos abiertos e interfaces de confianza
    Comment[pt_BR]=Gerencie o firewall: portas abertas e interfaces confiáveis
    Comment[ru]=Управление брандмауэром: открытые порты и доверенные интерфейсы
    Comment[zh_CN]=管理防火墙：开放端口和受信任的接口
    Comment[hi]=फ़ायरवॉल प्रबंधित करें: खुले पोर्ट और भरोसेमंद इंटरफ़ेस
    Comment[ar]=إدارة جدار الحماية: المنافذ المفتوحة والواجهات الموثوقة
    Exec=$out/bin/roudix-firewall
    Icon=io.roudix.firewall
    Terminal=false
    StartupNotify=true
    Categories=System;Settings;Security;X-Roudix;
    Keywords=firewall;pare-feu;ports;network;réseau;security;sécurité;nixos;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-firewall.mo
    # (the app looks them up relative to its own install prefix: see tr() in the sources)
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-firewall.mo" "$po"
    done

    runHook postInstall
  '';

  meta = {
    description = "GTK4/Adwaita firewall manager for Roudix (ports, trusted interfaces)";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "roudix-firewall";
  };
}

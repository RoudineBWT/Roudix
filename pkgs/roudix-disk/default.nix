{ lib, pkgs }:
let
  # What the app and its pkexec'd root helper call. Prefixed to the wrapper's
  # PATH so formatting works even if none of these are in the system profile.
  # (nh, pkexec and nix-instantiate come from the system, like in the other
  # Roudix apps.)
  runtimeTools = with pkgs; [ util-linux parted e2fsprogs btrfs-progs systemd coreutils ];
in
pkgs.stdenv.mkDerivation {
  pname = "roudix-disk";
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
    adwaita-icon-theme
    (python3.withPackages (ps: with ps; [
      pygobject3
    ]))
  ];

  installPhase = ''
    mkdir -p $out/bin \
              $out/share/applications \
              $out/share/icons/hicolor/scalable/apps

    cp roudix-disk.py $out/bin/roudix-disk
    chmod +x $out/bin/roudix-disk
    patchShebangs $out/bin/roudix-disk
    # pkexec has to run the *wrapper* (it sets PATH for parted/mkfs/...), so
    # bake its final path into the script (see self_launcher()).
    substituteInPlace $out/bin/roudix-disk \
      --replace-fail '@self@' "$out/bin/roudix-disk"

    # Icon
    cp roudix-disk.svg \
      $out/share/icons/hicolor/scalable/apps/io.roudix.disk.svg

    # .desktop entry
    cat > $out/share/applications/io.roudix.disk.desktop << EOF
    [Desktop Entry]
    Name=Roudix Disks
    Name[fr]=Disques Roudix
    Name[es]=Discos de Roudix
    Name[pt_BR]=Discos do Roudix
    Name[ru]=Диски Roudix
    Name[zh_CN]=Roudix 磁盘
    Name[hi]=Roudix डिस्क
    Name[ar]=أقراص Roudix
    Comment=Mount, format and manage your extra disks
    Comment[fr]=Monte, formate et gère tes disques supplémentaires
    Comment[es]=Monta, formatea y gestiona tus discos adicionales
    Comment[pt_BR]=Monte, formate e gerencie seus discos extras
    Comment[ru]=Монтирование, форматирование и управление дополнительными дисками
    Comment[zh_CN]=挂载、格式化和管理你的额外磁盘
    Comment[hi]=अपनी अतिरिक्त डिस्क माउंट, फ़ॉर्मैट और प्रबंधित करें
    Comment[ar]=تركيب أقراصك الإضافية وتهيئتها وإدارتها
    Exec=roudix-disk
    Icon=io.roudix.disk
    Terminal=false
    Type=Application
    Categories=System;Settings;X-Roudix;
    Keywords=disk;drive;partition;mount;format;ssd;hdd;usb;btrfs;ext4;fstab;nix;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-disk.mo
    # (the app looks them up relative to its own install prefix: see _find_localedir())
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-disk.mo" "$po"
    done
  '';

  preFixup = ''
    gappsWrapperArgs+=(--prefix PATH : ${lib.makeBinPath runtimeTools})
  '';

  meta = {
    description = "Mount-point manager and disk formatter for Roudix (GTK4/libadwaita, edits hardware-configuration.nix)";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
    mainProgram = "roudix-disk";
  };
}

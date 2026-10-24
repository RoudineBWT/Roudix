{ lib
, stdenv
, python3
, gtk4
, libadwaita
, gobject-introspection
, wrapGAppsHook4
, makeWrapper
, gettext
, scxctl        # passed from flake.nix / callPackage (inputs.roudix-caches.packages.${system}.scxctl)
, systemd
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.pygobject3 ]);
in
stdenv.mkDerivation {
  pname = "roudix-scheduler";
  version = "1.0.0";

  # The whole directory: roudix-scheduler.py plus po/ (compiled to .mo below).
  src = ./.;

  # wrapGAppsHook4 automatically wraps every executable under $out/bin
  # during fixupPhase, injecting GI_TYPELIB_PATH / XDG_DATA_DIRS /
  # GSETTINGS_SCHEMA_DIR computed over buildInputs' full transitive
  # closure (gtk4 already propagates Pango, GdkPixbuf, Graphene, HarfBuzz,
  # GLib...). Saves having to list typelibs by hand one by one.
  nativeBuildInputs = [ makeWrapper wrapGAppsHook4 gobject-introspection gettext ];
  buildInputs = [ gtk4 libadwaita ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps

    install -Dm755 roudix-scheduler.py $out/bin/roudix-scheduler
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
    Comment[fr]=Choisit et applique un ordonnanceur SCX
    Comment[es]=Elige y aplica un planificador SCX
    Comment[pt_BR]=Escolha e aplique um escalonador SCX
    Comment[ru]=Выбор и применение планировщика SCX
    Comment[zh_CN]=选择并应用 SCX 调度器
    Comment[hi]=SCX शेड्यूलर चुनें और लागू करें
    Comment[ar]=اختيار مُجدوِل SCX وتطبيقه
    Exec=$out/bin/roudix-scheduler
    Icon=io.roudix.scheduler
    Categories=System;Settings;X-Roudix;
    EOF

    # Translations: po/<lang>.po → share/locale/<lang>/LC_MESSAGES/roudix-scheduler.mo
    # (the app looks them up relative to its own install prefix: see tr() in the sources)
    for po in po/*.po; do
      [ -e "$po" ] || continue
      lang=$(basename "$po" .po)
      mkdir -p "$out/share/locale/$lang/LC_MESSAGES"
      msgfmt --check -o "$out/share/locale/$lang/LC_MESSAGES/roudix-scheduler.mo" "$po"
    done

    runHook postInstall
  '';

  # Adds scxctl/systemd to PATH, on top of everything wrapGAppsHook4
  # already configures automatically for GTK4/Adwaita.
  preFixup = ''
    gappsWrapperArgs+=(--prefix PATH : ${lib.makeBinPath [ scxctl systemd ]})
  '';

  meta = {
    description = "GTK4/Adwaita picker for SCX schedulers (Roudix)";
    mainProgram = "roudix-scheduler";
    platforms = lib.platforms.linux;
  };
}

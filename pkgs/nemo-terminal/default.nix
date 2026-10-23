# nemo-terminal — embedded VTE terminal for Nemo (toggle with F4, like
# Dolphin/Konsole). Not packaged in nixpkgs. It is a pure-Python extension
# loaded by nemo-python, so there is nothing to compile: we only install the
# .py file and its (compiled) GSettings schema. The typelib (Vte) and the schema
# lookup are wired in modules/system/apps/utilities/filemanager.nix, on top of
# the nemo-with-extensions wrapper.
{ lib, stdenv, fetchFromGitHub, glib }:

stdenv.mkDerivation (finalAttrs: {
  pname = "nemo-terminal";
  # Same tag as nixpkgs' nemo-python, so both stay in sync.
  version = "6.6.0";

  src = fetchFromGitHub {
    owner = "linuxmint";
    repo = "nemo-extensions";
    rev = finalAttrs.version;
    hash = "sha256-tXeMkaCYnWzg+6ng8Tyg4Ms1aUeE3xiEkQ3tKEX6Vv8=";
  };

  sourceRoot = "${finalAttrs.src.name}/nemo-terminal";

  nativeBuildInputs = [ glib ]; # glib-compile-schemas

  # Upstream connects its F4 handler with connect_after: once the terminal has
  # focus (it grabs it when shown), VTE swallows F4 and sends it to the shell,
  # so the handler never runs and the pane can't be hidden again. A plain
  # connect() runs before the focused widget gets the key.
  postPatch = ''
    substituteInPlace src/nemo_terminal.py \
      --replace-fail 'window.connect_after("key-press-event", self._toggle_visible)' \
                     'window.connect("key-press-event", self._toggle_visible)'
  '';

  dontConfigure = true;
  dontBuild = true;

  # The schema is compiled in its own XDG-style root (share/nemo-terminal/
  # schemas-root), NOT in share/glib-2.0/schemas: nemo-with-extensions merges
  # all extensions into one tree, where our gschemas.compiled would clash with
  # nemo's own. filemanager.nix adds this root to nemo's XDG_DATA_DIRS.
  installPhase = ''
    runHook preInstall
    install -Dm644 src/nemo_terminal.py \
      -t $out/share/nemo-python/extensions
    schemas=$out/share/nemo-terminal/schemas-root/glib-2.0/schemas
    install -Dm644 src/org.nemo.extensions.nemo-terminal.gschema.xml -t $schemas
    glib-compile-schemas $schemas
    runHook postInstall
  '';

  meta = {
    homepage = "https://github.com/linuxmint/nemo-extensions/tree/master/nemo-terminal";
    description = "Embedded terminal for the Nemo file manager (F4)";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
})

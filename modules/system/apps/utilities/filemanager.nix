{ lib, pkgs, config, ... }:
with lib;
let
  # Nemo + its default extensions + nemo-terminal (F4 embedded terminal, see
  # pkgs/nemo-terminal). nemo-terminal needs two things the nemo-with-extensions
  # wrapper doesn't give it: the Vte typelib, and its GSettings schema in
  # XDG_DATA_DIRS (it reads it at import time, a missing schema kills the
  # extension). nemo-with-extensions is a symlinkJoin whose postBuild isn't an
  # attribute (overrideAttrs can't extend it), so we wrap its result once more.
  nemoTerminal = pkgs.callPackage ../../../../pkgs/nemo-terminal { };
  nemoBase = pkgs.nemo-with-extensions.override { extensions = [ nemoTerminal ]; };
  nemoWithTerminal = pkgs.symlinkJoin {
    name = "nemo-with-terminal-${pkgs.nemo.version}";
    paths = [ nemoBase ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      for f in $(find $out/bin/ $out/libexec/ -type l -not -path "*/.*"); do
        wrapProgram "$f" \
          --prefix XDG_DATA_DIRS : "${nemoTerminal}/share/nemo-terminal/schemas-root" \
          --prefix GI_TYPELIB_PATH : "${pkgs.vte}/lib/girepository-1.0"
      done

      # Point the D-Bus / polkit files to *this* wrapped nemo (same as nixpkgs does)
      for file in "share/dbus-1/services/nemo.FileManager1.service" \
        "share/dbus-1/services/nemo.service" \
        "share/polkit-1/actions/org.nemo.root.policy"
      do
        rm "$out/$file"
        substitute "${nemoBase}/$file" "$out/$file" --replace-fail "${nemoBase}" "$out"
      done
    '';
    meta = removeAttrs pkgs.nemo.meta [ "name" "outputsToInstall" "position" ];
  };

  # `command` = the binary actually launched (used by the niri MOD+E bind).
  # The attribute names below already match the real binaries.
  fileManagerDefs = {
    "nautilus"   = { package = pkgs.nautilus;             command = "nautilus";   extras = [ pkgs.gvfs ]; };
    "dolphin"    = { package = pkgs.kdePackages.dolphin;   command = "dolphin";    extras = [ pkgs.kdePackages.kio-extras pkgs.kdePackages.kio-admin pkgs.kdePackages.ark pkgs.kdePackages.kdegraphics-thumbnailers ]; };
    # nemoWithTerminal = Nemo + extensions (nemo-fileroller → "Compress…" / "Extract
    # here" in the context menu, nemo-emblems, nemo-python, nemo-terminal → F4).
    # Plain `pkgs.nemo` has none of them. file-roller + the CLI backends do the work.
    "nemo"       = { package = nemoWithTerminal;               command = "nemo";       extras = [ pkgs.gvfs pkgs.file-roller pkgs.p7zip pkgs.unrar pkgs.zip pkgs.unzip ]; };
    "thunar"     = { package = pkgs.thunar;           command = "thunar";     extras = [ pkgs.gvfs pkgs.thunar-volman ]; };
    "pcmanfm-qt" = { package = pkgs.libsForQt5.pcmanfm-qt; command = "pcmanfm-qt"; extras = []; };
  };
in
{
  options.roudix.fileManager = mkOption {
    type = types.enum (attrNames fileManagerDefs);
    # Follows roudix.desktopIntegration: Dolphin when the KDE stack is
    # selected, Nautilus otherwise. An explicit value in local.nix (or from
    # roudix-switcher / the installer) always wins.
    default = if config.roudix.desktopIntegration == "kde" then "dolphin" else "nautilus";
    description = ''
      Default file manager: installed, and wired to the niri MOD+E bind
      as well as the "open a terminal here" integration (nautilus via
      nautilus-open-any-terminal, nemo via a Cinnamon dconf default).
    '';
  };

  config = mkIf (elem config.roudix.desktop.type [ "niri" "hyprland" "mangowc" "umbriel" ]) {
    environment.systemPackages =
      [ fileManagerDefs.${config.roudix.fileManager}.package ]
      ++ fileManagerDefs.${config.roudix.fileManager}.extras;

    # Nautilus needs its extension to respect roudix.terminal. Other
    # file managers have their own native mechanism (or no packaged
    # equivalent currently).
    programs.nautilus-open-any-terminal =
      mkIf (config.roudix.fileManager == "nautilus") {
        enable   = true;
        terminal = config.roudix.terminal;
      };

    # Nemo reads its "Open in Terminal" command from Cinnamon's gsettings key.
    # System-level dconf default (same approach as gnome.nix): the user's own
    # choice in the user db still wins.
    programs.dconf.enable = mkIf (config.roudix.fileManager == "nemo") true;
    programs.dconf.profiles.user.databases =
      mkIf (config.roudix.fileManager == "nemo") [
        { settings = {
            "org/cinnamon/desktop/default-applications/terminal".exec = config.roudix.terminal;
            # nemo-terminal pane at the bottom (upstream default is "top")
            "org/nemo/extensions/nemo-terminal" = {
              terminal-position = "bottom";
              # lines (upstream default: 5). Must be typed: the GSettings key is "i".
              default-terminal-height = lib.gvariant.mkInt32 32;
            };
            # Sort by name, A→Z (not reversed), folders first.
            "org/nemo/preferences" = {
              default-sort-order = "name";
              default-sort-in-reverse-order = false;
              sort-directories-first = true;
            };
          };
        }
      ];
  };
}

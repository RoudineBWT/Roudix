{ pkgs, inputs, lib, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
  isDms      = shellType == "dms";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  # ⚠ PAS d'import de `inputs.niri.homeModules.niri` ici : il est déjà
  # importé automatiquement au niveau système (le module NixOS niri
  # l'enregistre pour home-manager-as-module). L'importer une 2e fois ici
  # provoque `error: The option 'programs.niri.finalConfig' ... is
  # already declared` — c'est l'erreur qu'on a eue.
  #
  # Les fichiers _general/_animation/etc. posent programs.niri.settings.*
  # directement (pas de lib.mkIf à l'intérieur) : on ne les importe donc
  # QUE si niri est le compositeur actif, pour ne rien toucher côté niri
  # sur un host qui utilise un autre desktop.
  imports = [
    ../../mangohud.nix
    ../../papirus-icon.nix
    ../../tela-icon.nix
  ]
  ++ lib.optionals (osConfig.roudix.desktop.type == "niri") ([
    ./_general.nix
    ./_animation.nix
    ./_input.nix
    ./_layout.nix
    ./_output.nix
    ./_rules-common.nix
  ]
  ++ lib.optionals isNoctalia [
    ./_binds-noctalia.nix
    ./_rules-noctalia.nix
    ./_include-noctalia.nix
  ]
  ++ lib.optionals isDms [
    ./_binds-dms.nix
    ./_rules-dms.nix
    ./_include-dms.nix
  ]);

  config = lib.mkIf (osConfig.roudix.desktop.type == "niri") {

    # ── Noctalia (shell) ─────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    # ── Terminal / navigateur / fichiers résolus depuis roudix.* ──────────
    # Ces binds sont DÉJÀ définis par _binds-noctalia.nix / _binds-dms.nix ;
    # comme c'est la même clé (attrsOf, un point de fusion par bind), il
    # faut lib.mkForce pour que la valeur ci-dessous gagne — exactement le
    # même principe que pour un override dans local.nix.
    programs.niri.settings.binds = {
      "Mod+Return" = lib.mkForce {
        hotkey-overlay.title = "Open Terminal: ${terminalCmd}";
        action.spawn = [ terminalCmd ];
      };
      "Mod+E" = lib.mkForce {
        hotkey-overlay.title = "File Manager: ${fileManagerCmd}";
        action.spawn = [ fileManagerCmd ];
      };
    }
    // lib.optionalAttrs (browserCmd != null) {
      "Mod+B" = lib.mkForce {
        hotkey-overlay.title = "Open Browser: ${browserCmd}";
        action.spawn = [ browserCmd ];
      };
    }
    // (lib.listToAttrs (lib.imap1 (i: b: {
      name = "Mod+Ctrl+Alt+${toString i}";
      value = {
        hotkey-overlay.title = "Open Browser: ${b.name}";
        action.spawn = [ b.command ];
      };
    }) extraBrowsers));

    # ── Packages ─────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      awww
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper

      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
      clapper-enhancers
      gpu-screen-recorder

      nwg-look
      adw-gtk3
      papirus-icon-theme
      papirus-folders

      qt6Packages.qt6ct
      libsForQt5.qt5ct

      gvfs
      cava
    ]
    ++ lib.optionals isNoctalia [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}

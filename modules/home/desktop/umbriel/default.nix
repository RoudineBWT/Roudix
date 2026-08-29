{ lib, pkgs, inputs, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  imports = [
    inputs.umbriel.homeModules.default
    ../../mangohud.nix
    ../../papirus-icon.nix
    ../../tela-icon.nix
  ]
  # Les fichiers _foo.nix posent programs.umbriel.settings.* directement
  # (sans lib.mkIf) : on ne les importe que si umbriel est le compositeur
  # actif, pour ne rien toucher côté umbriel sur un host qui utilise un
  # autre desktop. Les LISTES (window_rule/layer_rule) et l'include se
  # fusionnent automatiquement entre ces fichiers via le système de
  # modules — pas de merge manuel nécessaire ici.
  ++ lib.optionals (osConfig.roudix.desktop.type == "umbriel") [
    ./_general.nix
    ./_appearance.nix
    ./_animation.nix
    ./_input.nix
    ./_layout.nix
    ./_output.nix
    ./_binds.nix
    ./_rules.nix
  ]
  ++ lib.optionals (osConfig.roudix.desktop.type == "umbriel" && isNoctalia) [
    ./_include-noctalia.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "umbriel") {

    # ── Noctalia (shell) ─────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    programs.umbriel = {
      enable = true;
      validateConfig = true; # umbriel valide le TOML généré au build
    };

    # ── Terminal / navigateur / fichiers résolus depuis roudix.* ──────────
    # Même clé ("Mod+Return" etc.) que dans _binds.nix : attrsOf → un
    # point de fusion par bind, donc lib.mkForce pour que cette valeur
    # gagne (même principe qu'un override côté local.nix).
    programs.umbriel.settings.keybinds = {
      "Mod+Return" = lib.mkForce "spawn:${terminalCmd}";
      "Mod+E" = lib.mkForce "spawn:${fileManagerCmd}";
    }
    // lib.optionalAttrs (browserCmd != null) {
      "Mod+B" = lib.mkForce "spawn:${browserCmd}";
    }
    // (lib.listToAttrs (lib.imap1 (i: b: {
      name = "Mod+Ctrl+Alt+${toString i}";
      value = "spawn:${b.command}";
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

      grim
      slurp

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

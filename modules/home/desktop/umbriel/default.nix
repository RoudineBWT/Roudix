{ config, lib, pkgs, inputs, dotfiles, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;

  # ── Assemblage déclaratif de programs.umbriel.settings ──────────────────
  # Chaque fichier _foo.nix ne renvoie qu'un fragment de l'attrset TOML
  # final (general/environment/..., appearance/..., animation, input,
  # layout, output/workspace, keybinds, window_rule/layer_rule). Umbriel
  # sérialise cet attrset en TOML via pkgs.formats.toml — pas besoin de
  # gérer un fichier config.toml séparé.
  umbrielSettings = lib.foldl' lib.recursiveUpdate { } [
    (import ./_general.nix    { inherit lib pkgs; })
    (import ./_appearance.nix { inherit lib pkgs; })
    (import ./_animation.nix  { inherit lib pkgs; })
    (import ./_input.nix      { inherit lib pkgs; })
    (import ./_layout.nix     { inherit lib pkgs; })
    (import ./_output.nix     { inherit lib pkgs; })
    (import ./_binds.nix      { inherit lib pkgs; })
    (import ./_rules.nix      { inherit lib pkgs; })
    (import ./_noctalia-include.nix      { inherit lib pkgs; })
  ];
in
{
  imports = [
    inputs.umbriel.homeModules.default
    ../../mangohud.nix
    ../../papirus-icon.nix
    ../../tela-icon.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "umbriel") {

    # ── Noctalia (shell) ─────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    # ── Umbriel config ──────────────────────────────────────────────────
    programs.umbriel = {
      enable = true;
      validateConfig = true;   # umbriel valide le TOML généré au build
      settings = umbrielSettings;
    };

    # Note : on ne copie plus ${dotfiles}/umbriel vers ~/.config/umbriel —
    # programs.umbriel.settings génère désormais le config.toml lui-même.
    # S'il te reste d'autres assets Umbriel dans le dépôt dotfiles (pas du
    # config.toml), remonte-les avec un xdg.configFile plus ciblé plutôt
    # qu'un `recursive = true` sur tout le dossier, pour éviter un conflit
    # avec le fichier généré.

    # ── Packages (mêmes packages communs que niri/hyprland) ──────────────
    home.packages = with pkgs; [
      # Wayland tools (communs à tous les shells)
      awww
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper

      # Capture d'écran (utilisé par le bind Ctrl+Shift+3 dans _binds.nix)
      grim
      slurp

      # Apps (communes)
      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
      clapper-enhancers
      gpu-screen-recorder

      # GTK theming
      nwg-look
      adw-gtk3
      papirus-icon-theme
      papirus-folders

      # Qt theming
      qt6Packages.qt6ct
      libsForQt5.qt5ct

      # Misc
      gvfs
      cava
    ]
    # Packages exclusifs à noctalia
    ++ lib.optionals isNoctalia [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}

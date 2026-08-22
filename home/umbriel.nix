{ config, lib, pkgs, inputs, dotfiles, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";

  resolveUmbrielDotfiles = shell:
    let
      candidates = {
        noctalia = "${dotfiles}/umbriel";
      };
    in
      candidates.${shell} or candidates.noctalia;

  umbrielDir = resolveUmbrielDotfiles shellType;
  terminalCmd = osConfig.roudix.terminal or "ghostty";

  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  # Les navigateurs restants (hors default) reçoivent un bind supplémentaire.
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  imports = [
    inputs.umbriel.homeModules.default
    ../modules/home/mangohud.nix
    ../modules/home/papirus-icon.nix
    ../modules/home/tela-icon.nix
  ];

  programs.umbriel = {
    enable = true;
    validateConfig = true;   # umbriel valide le TOML au build (via `umbriel validate`)

    # Le fichier ci-contre (config.toml) est la traduction de tes 9 fichiers
    # niri .kdl. Il est chargé tel quel — remplace LEGION-OUTPUT/HKC-OUTPUT
    # dedans par les vrais noms de connecteur avant le premier build
    # (`umbriel outputs` une fois en session pour les récupérer).
    #settings = ./config.toml;
  };

  xdg.configFile."umbriel" = {
    source    = umbrielDir;
    recursive = true;
  };
}
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

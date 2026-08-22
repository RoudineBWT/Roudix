# umbriel.nix
{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isUmbriel = shellType == "umbriel";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-icon.nix
    ../modules/home/tela-icon.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "umbriel") {

    # ── Umbriel ─────────────────────────────────────────────────────────────
    programs.umbriel = {
      enable = true;
      # package = inputs.umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default;
    };

    # ── Noctalia shell sur Umbriel (optionnel) ────────────────────────────
    programs.noctalia = lib.mkIf isUmbriel {
      enable = true;
      package = null;
    };

    # ── Configuration Umbriel ──────────────────────────────────────────────
   # xdg.configFile."umbriel" = {
   #   source    = "${dotfiles}/umbriel";
   #   recursive = true;
   # };


    # ── Packages ─────────────────────────────────────────────────────────────
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
    ++ lib.optionals isUmbriel [
      inputs.umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}

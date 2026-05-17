{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";

  resolveHyprDotfiles = shell:
    let
      candidates = {
        noctalia  = "${dotfiles}/hyprland";
        dms       = "${dotfiles}/hyprland-dms";
        caelestia = "${dotfiles}/hyprland-caelestia";
      };
      desired  = candidates.${shell} or candidates.noctalia;
      fallback = candidates.noctalia;
    in
      if builtins.pathExists desired then desired else fallback;

  hyprDir = resolveHyprDotfiles shellType;
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "hyprland") {

    # ── Noctalia ─────────────────────────────────────────────────────────────
    programs.noctalia-shell = lib.mkIf (shellType == "noctalia") {
      enable = true;
      package = null;
    };

    # ── Caelestia ────────────────────────────────────────────────────────────
    # No programs.* option — the homeManagerModules.default handles the
    # systemd service automatically. Just add the package in home.packages.

    # ── Config files ─────────────────────────────────────────────────────────
    # On copie le dossier tel quel — format et structure gérés par l'utilisateur.
    xdg.configFile."hypr" = {
      source    = hyprDir;
      recursive = true;
    };

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper

      # Apps
      nautilus
      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
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
    ++ lib.optionals (shellType == "noctalia") [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ]
    ++ lib.optionals (shellType == "caelestia") [
      inputs.caelestia-shell.packages.${pkgs.stdenv.hostPlatform.system}.with-cli
    ]
    ;
  };
}

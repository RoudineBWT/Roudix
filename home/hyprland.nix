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
    programs.noctalia = lib.mkIf (shellType == "noctalia") {
      enable = true;
      package = null;
    };

    # ── Caelestia ────────────────────────────────────────────────────────────
    # No programs.* option — the homeManagerModules.default handles the
    # systemd service automatically. Just add the package in home.packages.

    # ── Config files ─────────────────────────────────────────────────────────
    # On copie le dossier tel quel — format et structure gérés par l'utilisateur.
    # xdg.configFile."hypr" = {
    #   source    = hyprDir;
    #   recursive = true;
    #  };

    # ── Plugins Hyprland ─────────────────────────────────────────────────────
    # hyprscroller : REQUIS — layout.lua active `general.layout = "scroller"` et
    # configure `plugin.scroller.*`, mais sans cette déclaration le plugin n'est
    # jamais chargé et le layout scroller ne fonctionne pas.
    # Package désormais natif dans nixpkgs unstable (plus besoin d'un flake input
    # séparé comme pour les plugins "first-party" de hyprland-plugins).
    #
    # hypr-dynamic-cursors : curseur qui s'incline/accélère selon le mouvement,
    # cohérent avec le côté "fluide" des animations spring déjà configurées.
    # borders-plus-plus : double bordure — permet d'ajouter un liseré extérieur
    # en plus du dégradé teal déjà défini sur active_border dans decorations.lua.
    wayland.windowManager.hyprland.plugins = [
      pkgs.hyprlandPlugins.hyprscroller
      pkgs.hyprlandPlugins.hypr-dynamic-cursors
      pkgs.hyprlandPlugins.borders-plus-plus
    ];

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper
      hyprpicker
      satty

      # Apps
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

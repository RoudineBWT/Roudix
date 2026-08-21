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
    xdg.configFile."hypr/config/nix-plugins.lua".text =
      let
        hyprPlugins = [
          pkgs.hyprlandPlugins.borders-plus-plus
        ];

        loadPluginSoFrom = pkg: ''
          do
              local p = io.popen('find "${pkg}/lib" -maxdepth 1 -name "*.so" 2>/dev/null')
              if p then
                  for so in p:lines() do
                      hl.plugin.load(so)
                  end
                  p:close()
              end
          end
        '';

        header = ''
          -- Généré par hyprland.nix — NE PAS ÉDITER À LA MAIN.
          -- Charge les plugins Hyprland construits par Nix. Doit être require()
          -- en tout premier dans hyprland.lua, avant tout hl.config() qui touche
          -- aux clés plugin.dynamic_cursors / plugin.borders_plus_plus / plugin.hyprscrolling.
        '';
      in
        header + lib.concatMapStrings loadPluginSoFrom hyprPlugins;

    wayland.windowManager.hyprland.plugins = [
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

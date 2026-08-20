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
    # IMPORTANT : depuis Hyprland 0.55+, si un hyprland.lua existe, il est chargé
    # à la place de hyprland.conf (choix fait une seule fois au démarrage). Or
    # l'option HM `wayland.windowManager.hyprland.plugins` écrit ses `plugin = ...`
    # dans le hyprland.conf généré — qui n'est donc JAMAIS lu ici. On la garde
    # quand même pour forcer la construction des paquets dans le store/closure,
    # mais le chargement réel doit se faire depuis le Lua via hl.plugin.load(path)
    # (et non hl.plugin(path) — hl.plugin est un namespace/table, pas une fonction).
    #
    # hyprscroller a été retiré : plus maintenu upstream, et "scrolling" est
    # désormais un layout NATIF de Hyprland (au même titre que dwindle/master),
    # plus besoin de plugin pour ça — voir layout.lua. hyprscrolling (plugin
    # officiel hyprwm/hyprland-plugins) ajoute juste des options en plus
    # (column_width, fullscreen_on_one_column) par-dessus ce layout natif.
    xdg.configFile."hypr/config/nix-plugins.lua".text =
      let
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
      in
      ''
        -- Généré par hyprland.nix — NE PAS ÉDITER À LA MAIN.
        -- Charge les plugins Hyprland construits par Nix. Doit être require()
        -- en tout premier dans hyprland.lua, avant tout hl.config() qui touche
        -- aux clés plugin.dynamic_cursors / plugin.borders_plus_plus / plugin.hyprscrolling.
      ''
      + loadPluginSoFrom pkgs.hyprlandPlugins.hypr-dynamic-cursors
      + loadPluginSoFrom pkgs.hyprlandPlugins.borders-plus-plus

    wayland.windowManager.hyprland.plugins = [
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

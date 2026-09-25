{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
in
{
  imports = [
    ../../theming/mangohud.nix
    ../../theming/papirus-folders.nix
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

    # ── Hyprland Lua configuration ─────────────────────────────────────────
    # Copy the modular Lua tree file-by-file so the Nix-generated plugin loader
    # can coexist with the user-owned configuration.
    hyprFiles = [
      "hyprland.lua"
      "README.md"
      "config/animations.lua"
      "config/autostart.lua"
      "config/colors.lua"
      "config/decorations.lua"
      "config/defaults.lua"
      "config/environment.lua"
      "config/input.lua"
      "config/layout.lua"
      "config/misc.lua"
      "config/monitors.lua"
      "config/shell.lua"
      "config/workspaces.lua"
      "config/binds/common.lua"
      "config/rules/apps.lua"
      "config/rules/common.lua"
      "config/rules/gaming.lua"
      "config/shells/caelestia.lua"
      "config/shells/dms.lua"
      "config/shells/noctalia.lua"
      "scripts/gamemode.sh"
    ];

    xdg.configFile = lib.mkMerge [
      (lib.genAttrs hyprFiles (file: {
        source = "${dotfiles}/hyprland/${file}";
      }))
      {
        "hypr/config/nix-plugins.lua".text =
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
              -- Les plugins doivent être chargés avant les modules qui utilisent
              -- leurs options.
            '';
          in
            header + lib.concatMapStrings loadPluginSoFrom hyprPlugins;
      }
    ];

    # The shell is selected by the existing Roudix desktop option and exposed
    # to the Lua config at session start.
    home.sessionVariables = {
      ROUDIX_HYPR_SHELL = shellType;
      ROUDIX_HYPR_START_DISCORD = if osConfig.roudix.discord != "none" then "1" else "0";
    };

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

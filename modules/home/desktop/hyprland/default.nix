{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
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
    "config/ws.lua"
    "config/nix-noctalia.lua"
    "config/binds/common.lua"
    "config/rules/apps.lua"
    "config/rules/common.lua"
    "config/rules/gaming.lua"
    "config/shells/caelestia.lua"
    "config/shells/dms.lua"
    "config/shells/noctalia.lua"
    "scripts/gamemode.sh"
  ];

  # ── Terminal / browser / files resolved from roudix.* ──────────────────
  # Same principle as niri/umbriel/mangowc (see umbriel/default.nix): Lua
  # has no attrsOf to fight with lib.mkForce though — TERMINAL/FILE_MANAGER/
  # BROWSER/BROWSER_ALT/EXTRA_BROWSERS are plain globals, so a later
  # `require` in hyprland.lua simply reassigning them wins over
  # config/defaults.lua's fallback values.
  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";
  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;

  # Noctalia's keybind-cheatsheet uses hyprctl binds -j as the live source of
  # truth, then scans a Lua file for categories/descriptions. Scanning our full
  # hyprland.lua tree is unnecessarily expensive (and can hit Noctalia's Luau
  # CPU budget), so give it a tiny metadata-only file containing just the
  # common + Noctalia bind descriptions.
  noctaliaCheatsheet = pkgs.runCommand "roudix-noctalia-cheatsheet.lua" { } ''
    cat > $out <<'EOF'
    -- Généré par modules/home/desktop/hyprland/default.nix — NE PAS ÉDITER.
    -- Les binds live viennent de `hyprctl binds -j`; ce fichier ne contient
    -- que les catégories et descriptions que le plugin Noctalia doit scanner.
    EOF
    awk '
      /^-- [0-9]+ / { print; next }
      /description = \"/ {
        if (match($0, /description = \"[^\"]*\"( *\.\. *[A-Za-z0-9_\[\]]+)?/))
          print substr($0, RSTART, RLENGTH)
      }
    ' "${dotfiles}/hyprland/config/binds/common.lua" "${dotfiles}/hyprland/config/shells/noctalia.lua" >> $out
  '';
in
{
  imports = [
    ../../theming/mangohud.nix
    ../../theming/papirus-folders.nix
    ../../theming/tela-icon.nix
  ]
  ++ lib.optionals (osConfig.roudix.desktop.type == "hyprland" && isNoctalia) [
    ./_include-noctalia.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "hyprland") {

    # ── Noctalia ─────────────────────────────────────────────────────────────
    programs.noctalia = lib.mkIf (shellType == "noctalia") {
      enable = true;
      package = inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default;
      systemd.enable = false;
      settings.plugin_settings."kenn/keybind-cheatsheet" = {
        # The live bind list still comes from Hyprland; this tiny file only
        # supplies the categories/descriptions for the Noctalia plugin.
        hyprland_lua_config = "~/.config/hypr/noctalia-cheatsheet.lua";
        hyprland_parser = "lua";
      };
    };

    programs.dank-material-shell = lib.mkIf (shellType == "dms") {
      enable = true;
      systemd.enable = false;
    };

    programs.caelestia = lib.mkIf (shellType == "caelestia") {
      enable = true;
      systemd.enable = false;
      cli.enable = true;
    };

    # ── Hyprland Lua configuration ─────────────────────────────────────────
    # Copy the modular Lua tree file-by-file so the Nix-generated plugin loader
    # can coexist with the user-owned configuration.
    xdg.configFile = lib.mkMerge [
      (lib.listToAttrs (map (file: {
        name = "hypr/${file}";
        value = {
          source = "${dotfiles}/hyprland/${file}";
        };
      }) hyprFiles))
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
      {
        "hypr/config/nix-apps.lua".text = ''
          -- Généré par hyprland/default.nix depuis roudix.terminal /
          -- roudix.fileManager / roudix.browser.* — NE PAS ÉDITER À LA MAIN.
          -- Rechargé après config/defaults.lua dans hyprland.lua : ces
          -- affectations gagnent (dernière écriture d'une globale Lua).
          TERMINAL = "${terminalCmd}"
          FILE_MANAGER = "${fileManagerCmd}"
          ${lib.optionalString (browserCmd != null) ''BROWSER = "${browserCmd}"''}
          EXTRA_BROWSERS = {
          ${lib.concatMapStringsSep "\n" (b: ''    { name = "${b.name}", command = "${b.command}" },'') extraBrowsers}
          }
          -- Le premier navigateur "extra" reste sur Mod+Shift+B (ancien
          -- BROWSER_ALT hardcodé) ; les suivants passent par la boucle
          -- Mod+Ctrl+Alt+N dans binds/common.lua.
          BROWSER_ALT = EXTRA_BROWSERS[1] and EXTRA_BROWSERS[1].command or nil
        '';
      }
      {
        "hypr/noctalia-cheatsheet.lua".source = noctaliaCheatsheet;
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
    ;
  };
}

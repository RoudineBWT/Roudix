{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";

  resolveNiriDotfiles = shell:
    let
      candidates = {
        noctalia  = "${dotfiles}/niri-noc-v5";
        dms       = "${dotfiles}/niri-dms";
      };
      desired  = candidates.${shell} or candidates.noctalia;
      fallback = candidates.noctalia;
    in
      if builtins.pathExists desired then desired else fallback;

  niriDir = resolveNiriDotfiles shellType;

  isNoctalia = shellType == "noctalia";
  isDms      = shellType == "dms";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  browserCmd  = osConfig.roudix.browser.command or null;
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-icon.nix
    ../modules/home/tela-icon.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "niri") {

    # ── Noctalia ─────────────────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    # ── Niri config ───────────────────────────────────────────────────────────
    xdg.configFile."niri" = {
      source    = niriDir;
      recursive = true;
    };

    xdg.configFile."niri/config.kdl" = {
      force = true;
      text = ''
        include "${niriDir}/cfg/autostart.kdl"
        include "${niriDir}/cfg/keybinds.kdl"

        // ── Terminal / navigateur (résolus depuis roudix.terminal / roudix.browser) ──
        include optional=true "${config.home.homeDirectory}/.config/niri/apps.kdl"

        include "${niriDir}/cfg/input.kdl"
        include "${niriDir}/cfg/display.kdl"
        include "${niriDir}/cfg/layout.kdl"
        include "${niriDir}/cfg/rules.kdl"
        include "${niriDir}/cfg/misc.kdl"
      '' + lib.optionalString isNoctalia ''
        include optional=true "${config.home.homeDirectory}/.config/niri/noctalia.kdl"
      '' + lib.optionalString isDms ''
        include "${config.home.homeDirectory}/.config/niri/dms/alttab.kdl"
        include "${config.home.homeDirectory}/.config/niri/dms/wpblur.kdl"
        include "${config.home.homeDirectory}/.config/niri/dms/colors.kdl"
        include "${config.home.homeDirectory}/.config/niri/dms/cursor.kdl"
        include "${config.home.homeDirectory}/.config/niri/dms/layout.kdl"
      '' + ''

        // ── User overrides (injected by Nix) ─────────────────────────────
        include "${config.home.homeDirectory}/.config/niri/user.kdl"
      '';
    };

    xdg.configFile."niri/apps.kdl" = {
      force = true;
      text = ''
        // ── Généré par Nix depuis roudix.terminal / roudix.browser ──
        // Ce fichier override les binds MOD+RETURN / MOD+B définis dans keybinds.kdl.
        binds {
            MOD+RETURN hotkey-overlay-title="Open Terminal: ${terminalCmd}" { spawn "${terminalCmd}"; }
      '' + lib.optionalString (browserCmd != null) ''
            MOD+B hotkey-overlay-title="Open Browser: ${browserCmd}" { spawn "${browserCmd}"; }
      '' + ''
        }
      '';
    };

    xdg.configFile."niri/user.kdl" = {
      text = lib.mkDefault ''
        // Personal Niri overrides — edit this in home/local.nix
      '';
    };


    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      # Niri / Wayland tools (communs à tous les shells)
      awww              # ex-swww, binaires swww/swww-daemon inchangés
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper

      # Apps (communes)
      nautilus
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

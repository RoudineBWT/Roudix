{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";

  resolveNiriDotfiles = shell:
    let
      candidates = {
        noctalia  = "${dotfiles}/niri";
        dms       = "${dotfiles}/niri-dms";
      };
      desired  = candidates.${shell} or candidates.noctalia;
      fallback = candidates.noctalia;
    in
      if builtins.pathExists desired then desired else fallback;

  niriDir = resolveNiriDotfiles shellType;
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "niri") {

    # ── Noctalia ─────────────────────────────────────────────────────────────
    programs.noctalia-shell = lib.mkIf (shellType == "noctalia") {
      enable = true;
      package = null;
    };

    # ── DankMaterialShell ────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkIf (shellType == "dms") {
      enable = true;
    };

    # ── Niri config ───────────────────────────────────────────────────────────
    xdg.configFile."niri" = {
      source    = niriDir;
      recursive = true;
    };

    # config.kdl est généré par Nix : chemins absolus vers le nix store
    # + include absolu vers user.kdl (niri n'expand pas '~').
    xdg.configFile."niri/config.kdl" = {
      force = true;
      text = ''
        include "${niriDir}/cfg/autostart.kdl"
        include "${niriDir}/cfg/keybinds.kdl"
        include "${niriDir}/cfg/input.kdl"
        include "${niriDir}/cfg/display.kdl"
        include "${niriDir}/cfg/layout.kdl"
        include "${niriDir}/cfg/rules.kdl"
        include "${niriDir}/cfg/misc.kdl"
      '' + lib.optionalString (shellType == "noctalia") ''
        include "${config.home.homeDirectory}/.config/niri/noctalia.kdl"
      '' + ''

        // ── User overrides (injected by Nix) ─────────────────────────────
        include "${config.home.homeDirectory}/.config/niri/user.kdl"
      '';
    };

    # ── User overrides file ───────────────────────────────────────────────────
    # Empty by default — the user fills it in home/local.nix.
    xdg.configFile."niri/user.kdl" = {
      text = lib.mkDefault ''
        // Personal Niri overrides — edit this in home/local.nix
        // See home/local.nix.example for examples (outputs, keybinds, etc.)
      '';
    };

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      # Niri / Wayland tools
      awww
      xwayland-satellite
      playerctl
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
    ;
  };
}

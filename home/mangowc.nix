{ pkgs, inputs, config, lib, osConfig, dotfiles, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  mangowcDir = if shellType == "dms"
               then dotfiles + "/mangowc-dms"
               else dotfiles + "/mangowc";
in
{
  imports = [
    ../modules/home/mangohud.nix
    ../modules/home/papirus-folders.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "mangowc") {

    # ── Config files ─────────────────────────────────────────────────────────
    xdg.configFile."mango" = {
      source    = mangowcDir;
      recursive = true;
    };

    # mango.conf est généré par Nix : chemins absolus vers le nix store
    # + source absolu vers user.conf pour éviter tout conflit avec le récursif.
    xdg.configFile."mango/config.conf" = {
      force = true;
      text = ''
        source = ${mangowcDir}/cfg/env.conf
        source = ${mangowcDir}/cfg/appearance.conf
        source = ${mangowcDir}/cfg/animations.conf
        source = ${mangowcDir}/cfg/input.conf
        source = ${mangowcDir}/cfg/layout.conf
        source = ${mangowcDir}/cfg/monitors.conf
        source = ${mangowcDir}/cfg/rules.conf
        source = ${mangowcDir}/cfg/keybinds.conf
        source = ${mangowcDir}/cfg/autostart.conf
        source = ${mangowcDir}/cfg/misc.conf

        # ── User overrides (injected by Nix) ─────────────────────────────
        source = ${config.home.homeDirectory}/.config/mango/user.conf
      '';
    };

    # ── User overrides file ───────────────────────────────────────────────────
    # Empty by default — the user fills it in home/local.nix.
    xdg.configFile."mango/user.conf" = {
      text = lib.mkDefault ''
        # Personal MangoWC overrides — edit this in home/local.nix
        # See home/local.nix.example for examples (monitors, keybinds, etc.)
      '';
    };

    # ── Packages ─────────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      mangowc
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
      (pkgs.writeShellScriptBin "noctalia-ipc" ''
        exec ${inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/noctalia-shell ipc "$@"
      '')
    ]
    ;
  };
}

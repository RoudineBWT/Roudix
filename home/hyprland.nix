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

    # ── DankMaterialShell ────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkIf (shellType == "dms") {
      enable = true;
    };

    # ── Caelestia ────────────────────────────────────────────────────────────
    # No programs.* option — the homeManagerModules.default handles the
    # systemd service automatically. Just add the package in home.packages.

    # ── Config files ─────────────────────────────────────────────────────────
    xdg.configFile."hypr" = {
      source    = hyprDir;
      recursive = true;
    };

    # hyprland.conf est généré par Nix : chemins absolus vers le nix store
    # + source absolu vers user.conf pour éviter tout conflit avec le récursif.
    xdg.configFile."hypr/hyprland.conf" = {
      force = true;
      text = ''
        source = ${hyprDir}/cfg/monitors.conf
        source = ${hyprDir}/cfg/environment.conf
        source = ${hyprDir}/cfg/autostart.conf
        source = ${hyprDir}/cfg/input.conf
        source = ${hyprDir}/cfg/appearance.conf
        source = ${hyprDir}/cfg/animations.conf
        source = ${hyprDir}/cfg/workspaces.conf
        source = ${hyprDir}/cfg/rules.conf
        source = ${hyprDir}/cfg/keybinds.conf
        source = ${hyprDir}/cfg/misc.conf

        # ── User overrides (injected by Nix) ───────────────────────────────
        source = ${config.home.homeDirectory}/.config/hypr/user.conf
      '';
    };

    # ── User overrides file ───────────────────────────────────────────────────
    # Empty by default — the user fills it in home/local.nix.
    xdg.configFile."hypr/user.conf" = {
      text = lib.mkDefault ''
        # Personal Hyprland overrides — edit this in home/local.nix
        # See home/local.nix.example for examples (monitors, keybinds, etc.)
      '';
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
      inputs.caelestia-shell.packages.${pkgs.stdenv.hostPlatform.system}.cli
    ]
    ;
  };
}

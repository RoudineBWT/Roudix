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
      source    = resolveHyprDotfiles shellType;
      recursive = true;
    };

    # hyprland.conf est généré par Nix : dotfiles + source absolu vers user.conf
    xdg.configFile."hypr/hyprland.conf".text =
      builtins.readFile "${resolveHyprDotfiles shellType}/hyprland.conf" + ''

        # ── User overrides (injected by Nix) ─────────────────────────────────
        source = ${config.home.homeDirectory}/.config/hypr/user.conf
      '';

    # ── User overrides file ───────────────────────────────────────────────────
    # Empty by default — the user fills it in home/local.nix.
    xdg.configFile."hypr/user.conf" = lib.mkDefault {
      text = ''
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
    ]
    ;
  };
}

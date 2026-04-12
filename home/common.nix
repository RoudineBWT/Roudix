{ pkgs, inputs, lib, username, osConfig, roudixSwitcher, dotfiles, ... }:
let
  desktopType = osConfig.roudix.desktop.type;
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isHyprlandOrNiri = desktopType == "hyprland" || desktopType == "niri";
in
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  imports = [
    ../modules/home/fastfetch.nix
    ../modules/home/fish.nix
    ../modules/home/bash.nix
    ../modules/home/git.nix
    ../modules/home/ssh.nix
    ../modules/home/spicetify.nix
    ../modules/home/gaming-home.nix
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix;

  # ── Easyeffects preset ───────────────────────────────────────────────────
  xdg.configFile."easyeffects" = {
    source = "${dotfiles}/easyeffects";
    recursive = true;
  };

  # ── Default branding wallpaper ───────────────────────────────────────────
  # Set a Roudix wallpaper by default — the user can override it via the shell UI.
  # These files live in ~/.cache / ~/.local/state so they're not read-only symlinks
  # and will be overwritten as soon as the user picks their own wallpaper.

  # Noctalia
  home.file.".cache/noctalia/wallpapers.json" = lib.mkIf (isHyprlandOrNiri && shellType == "noctalia") {
    text = builtins.toJSON {
      defaultWallpaper = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
      wallpapers = {};
    };
  };

  # DMS
  home.file.".local/state/DankMaterialShell/session.json" = lib.mkIf (isHyprlandOrNiri && shellType == "dms") {
    text = builtins.toJSON {
      wallpaperPath = "/run/current-system/sw/share/backgrounds/roudix/roudix-dark.png";
      wallpaperFillMode = "PreserveAspectCrop";
    };
  };

  # Caelestia
  programs.caelestia = lib.mkIf (isHyprlandOrNiri && shellType == "caelestia") {
    settings.paths.wallpaperDir = "/run/current-system/sw/share/backgrounds/roudix";
  };

  home.packages = (with pkgs; [
    # Common apps
    roudixSwitcher
    ghostty
    zed-editor
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
    deluge-gtk
    (discord.override { withVencord = true; })
    (element-desktop.override {
      commandLineArgs = if osConfig.roudix.desktop.type == "kde"
        then "--password-store=kwallet6"
        else "--password-store=gnome-libsecret";
    })
    openrgb-with-all-plugins
    rustdesk-flutter
    kodi-wayland
    inkscape
    gimp
    starship
    easyeffects
    rnnoise-plugin

    # OBS Studio
    (pkgs.wrapOBS {
      plugins = with pkgs.obs-studio-plugins; [
        obs-pipewire-audio-capture
        obs-vkcapture
      ];
    })
  ])
  # Zen Browser (optional)
  ++ lib.optional osConfig.roudix.zen.enable
       inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.twilight;

  programs.home-manager.enable = true;
}

{ pkgs, inputs, lib, username, osConfig, roudixSwitcher, dotfiles, ... }:
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

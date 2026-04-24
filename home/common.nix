{ pkgs, inputs, lib, username, osConfig, roudixSwitcher, dotfiles, roudixBranding, roudix-kernel-switcher, ... }:
let
  desktopType = osConfig.roudix.desktop.type;
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isHyprlandOrNiri = desktopType == "hyprland" || desktopType == "niri";

  brandingWallpaper = "${roudixBranding}/share/backgrounds/roudix/roudix-dark.png";
in
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.05";

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
  # Write the Roudix wallpaper only on first install (file absent).
  # Rebuilds never overwrite the user's own wallpaper choice.
  home.activation.defaultWallpaper = lib.mkIf isHyprlandOrNiri (
    lib.hm.dag.entryAfter [ "writeBoundary" ] (
      lib.optionalString (shellType == "noctalia") ''
        if [ ! -f "$HOME/.cache/noctalia/wallpapers.json" ]; then
          mkdir -p "$HOME/.cache/noctalia"
          printf '%s' '{"defaultWallpaper":"${roudixBranding}/share/backgrounds/roudix/roudix-dark.png","wallpapers":{}}' \
            > "$HOME/.cache/noctalia/wallpapers.json"
        fi
      ''
      + lib.optionalString (shellType == "dms") ''
        if [ ! -f "$HOME/.local/state/DankMaterialShell/session.json" ]; then
          mkdir -p "$HOME/.local/state/DankMaterialShell"
          printf '%s' '{"wallpaperPath":"${roudixBranding}/share/backgrounds/roudix/roudix-dark.png","wallpaperFillMode":"PreserveAspectCrop"}' \
            > "$HOME/.local/state/DankMaterialShell/session.json"
        fi
      ''
      + lib.optionalString (shellType == "caelestia") ''
        if [ ! -f "$HOME/.config/caelestia/shell.json" ]; then
          mkdir -p "$HOME/.config/caelestia"
          printf '%s' '{"paths":{"wallpaperDir":"${roudixBranding}/share/backgrounds/roudix"}}' \
            > "$HOME/.config/caelestia/shell.json"
        fi
      ''
    )
  );

  home.packages = (with pkgs; [
    # Common apps
    roudixSwitcher
    roudix-kernel-switcher
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
    songrec

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
       inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.beta;

  programs.home-manager.enable = true;
}

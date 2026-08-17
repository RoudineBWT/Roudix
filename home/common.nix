{ pkgs, inputs, lib, username, osConfig, roudixSwitcher, dotfiles, roudixBranding, roudix-kernel-switcher, ... }:
let
  desktopType = osConfig.roudix.desktop.type;
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isHyprlandOrNiri = desktopType == "hyprland" || desktopType == "niri";

  brandingWallpaper = "${roudixBranding}/share/backgrounds/roudix/roudix-dark.png";

  matrixClient = osConfig.roudix.matrixClient or "element";

  matrixPackage = {
    element = pkgs.element-desktop.override {
      commandLineArgs = if osConfig.roudix.desktop.type == "kde"
        then "--password-store=kwallet6"
        else "--password-store=gnome-libsecret";
    };
    cinny  = pkgs.cinny-desktop;
    none   = null;
  }.${matrixClient};

  terminalType = osConfig.roudix.terminal or "ghostty";

  terminalPackage = {
    ghostty   = pkgs.ghostty;
    kitty     = pkgs.kitty;
    alacritty = pkgs.alacritty;
    foot      = pkgs.foot;
    wezterm   = pkgs.wezterm;
    ptyxis    = pkgs.ptyxis;
    konsole   = pkgs.kdePackages.konsole;
  }.${terminalType};
in
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.11";

  imports = [
    ../modules/home/fastfetch.nix
    ../modules/home/fish.nix
    ../modules/home/bash.nix
    ../modules/home/git.nix
    ../modules/home/ssh.nix
    ../modules/home/spicetify.nix
    ../modules/home/gaming-home.nix
    ../modules/home/gitwatch.nix
    # Zen Browser HM module — imported unconditionally (lazy), only builds
    # anything when `programs.zen-browser.enable` is actually true below.
    inputs.zen-browser.homeModules.twilight
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
    zed-editor
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
    bibata-cursors
    (discord.override { withVencord = true; })
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
  # Matrix client (optional)
  ++ lib.optional (matrixPackage != null) matrixPackage
  # Note: Zen Browser is no longer added here as a raw package — see
  # `programs.zen-browser` below, driven by `osConfig.roudix.zen.*`.
  # Terminal choisi par l'utilisateur (roudix.terminal)
  ++ [ terminalPackage ]
++ lib.optional (desktopType != "kde") pkgs.xdg-user-dirs-gtk;

       xdg.userDirs = {
         enable = true;
         createDirectories = true;
       };

       dconf.settings = {
         "org/gnome/desktop/interface" = {
           gtk-enable-primary-paste = true;
         };
       };

  programs.zen-browser = lib.mkIf osConfig.roudix.zen.enable {
    enable = true;
    profiles.default = {
      sine = {
        enable = osConfig.roudix.zen.sine.enable;
        mods   = osConfig.roudix.zen.sine.mods;
      };
      mods = lib.mkIf (!osConfig.roudix.zen.sine.enable) osConfig.roudix.zen.mods;
    };
  };

  programs.home-manager.enable = true;
}

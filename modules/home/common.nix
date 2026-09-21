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

  discordType = osConfig.roudix.discord or "vencord";

  discordPackage = {
    vencord = pkgs.discord.override { withVencord = true; };
    vanilla = pkgs.discord;
    none    = null;
  }.${discordType};

  telegramType = osConfig.roudix.telegram or "none";

  telegramPackage = {
    telegram = pkgs.telegram-desktop;
    ayugram  = pkgs.ayugram-desktop;
    none     = null;
  }.${telegramType};

  # Video player — was hardcoded (clapper, on niri/hyprland/mangowc/umbriel
  # only) or a DE-agnostic opt-in boolean (roudix.apps.mpv.enable); now one
  # DE-agnostic choice. Returns a *list* (clapper needs its enhancers
  # alongside it), unlike the single-package matrix/discord/telegram maps.
  videoPlayerType = osConfig.roudix.videoPlayer or "vlc";

  videoPlayerPackages = {
    clapper   = [ pkgs.clapper pkgs.clapper-enhancers ];
    mpv       = [ pkgs.mpv pkgs.yt-dlp ];
    celluloid = [ pkgs.celluloid ];
    vlc       = [ pkgs.vlc ];
    none      = [ ];
  }.${videoPlayerType};

  torrentClientType = osConfig.roudix.torrentClient or "none";

  torrentClientPackage = {
    qbittorrent = pkgs.qbittorrent;
    fragments   = pkgs.fragments;
    deluge      = pkgs.deluge;
    none        = null;
  }.${torrentClientType};

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

  editorType = osConfig.roudix.editor or "zed";

  editorPackage = {
    vscode  = pkgs.vscode;
    zed     = pkgs.zed-editor;
    neovim  = pkgs.neovim;
    none    = null;
  }.${editorType};

  # ── Zen Browser variant ────────────────────────────────────────────────
  # `homeModules.<name>` bakes the channel in at import time (it can't be
  # switched via a config option inside `programs.zen-browser`), so we pick
  # which HM module to import based on `roudix.zen.variant`.
  zenVariant = osConfig.roudix.zen.variant or "twilight";
  zenHomeModules = {
    beta     = inputs.zen-browser.homeModules.beta;
    twilight = inputs.zen-browser.homeModules.twilight;
  };

  # ── Content creation ─────────────────────────────────────────────────────
  ccPluginDefaults = {
    vkcapture.enable               = true;
    pipewireAudioCapture.enable    = true;
    backgroundRemoval.enable       = false;
    moveTransition.enable          = false;
    aitumMultistream.enable        = false;
    gstreamer.enable               = false;
    compositeBlur.enable           = false;
    advancedSceneSwitcher.enable   = false;
    inputOverlay.enable            = false;
    waveform.enable                = false;
  };
  ccCfg = osConfig.roudix.contentCreation or {
    enable = true;
    obs = { enable = true; plugins = ccPluginDefaults; };
    videoEditor = "kdenlive";
    streaming.chatterino.enable = false;
  };
  ccEnabled = ccCfg.enable or true;

  obsPluginCfg = (ccCfg.obs.plugins or {});
  obsPluginMap = with pkgs.obs-studio-plugins; {
    vkcapture               = obs-vkcapture;
    pipewireAudioCapture    = obs-pipewire-audio-capture;
    backgroundRemoval       = obs-backgroundremoval;
    moveTransition          = obs-move-transition;
    aitumMultistream        = obs-aitum-multistream;
    gstreamer               = obs-gstreamer;
    compositeBlur           = obs-composite-blur;
    advancedSceneSwitcher   = advanced-scene-switcher;
    inputOverlay            = input-overlay;
    waveform                = waveform;
  };

  obsPackage = pkgs.wrapOBS {
    plugins = lib.filter (p: p != null) (lib.mapAttrsToList
      (name: pkg: if ((obsPluginCfg.${name} or { enable = false; }).enable or false) then pkg else null)
      obsPluginMap);
  };

  videoEditorType = ccCfg.videoEditor or "kdenlive";
  videoEditorPackage = {
    kdenlive                = pkgs.kdePackages.kdenlive;
    davinci-resolve          = pkgs.davinci-resolve;
    davinci-resolve-studio   = pkgs.davinci-resolve-studio;
    shotcut                    = pkgs.shotcut;
    none                       = null;
  }.${videoEditorType};
in
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.11";

  imports = [
    ./fastfetch.nix
    ./fish.nix
    ./bash.nix
    ./ssh.nix
    ./gaming-home.nix
    ./gitwatch.nix
    # GTK theme/icons/cursor + dconf for GSettings-reading apps (GTK3/4,
    # Chromium-family browsers incl. Helium). Imported unconditionally;
    # a no-op on gnome/kde, which theme themselves natively.
    ./gtk-theme.nix
    # Zen Browser HM module — imported unconditionally (lazy), only builds
    # anything when `programs.zen-browser.enable` is actually true below.
    # Which channel gets imported is driven by `roudix.zen.variant`.
    zenHomeModules.${zenVariant}
  ] ++ lib.optional (builtins.pathExists ./git.nix) ./git.nix
    ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix
    # Spotify + Spicetify (roudix.apps.spotify.enable)
    ++ lib.optional osConfig.roudix.apps.spotify.enable ./spicetify.nix
    # Widevine CDM pointer for Helium (DRM playback), only when helium is
    # actually one of the selected browsers.
    ++ lib.optional (lib.elem "helium" osConfig.roudix.browsers) ./helium-widevine.nix;

  # ── Easyeffects preset ───────────────────────────────────────────────────
  xdg.configFile."easyeffects" = lib.mkIf osConfig.roudix.apps.easyeffects.enable {
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
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
    bibata-cursors
    starship
  ])
  # Optional common apps (roudix.apps.*)
  ++ lib.optional osConfig.roudix.apps.gimp.enable pkgs.gimp
  ++ lib.optional osConfig.roudix.apps.inkscape.enable pkgs.inkscape
  ++ lib.optional osConfig.roudix.apps.songrec.enable pkgs.songrec
  ++ lib.optionals osConfig.roudix.apps.easyeffects.enable [ pkgs.easyeffects pkgs.rnnoise-plugin ]
  # Matrix client (optional)
  ++ lib.optional (matrixPackage != null) matrixPackage
  # Discord (optionnel)
  ++ lib.optional (discordPackage != null) discordPackage
  # Telegram — official client or the AyuGram fork (optional)
  ++ lib.optional (telegramPackage != null) telegramPackage
  # Video player — VLC (default), clapper, mpv, celluloid, or none
  ++ videoPlayerPackages
  # Torrent client (optional)
  ++ lib.optional (torrentClientPackage != null) torrentClientPackage
  # Note: Zen Browser is no longer added here as a raw package — see
  # `programs.zen-browser` below, driven by `osConfig.roudix.zen.*`.
  # Terminal choisi par l'utilisateur (roudix.terminal)
  ++ [ terminalPackage ]
  # Editor chosen by the user (roudix.editor, "none" for none)
  ++ lib.optional (editorPackage != null) editorPackage
  # OBS Studio, with plugins picked individually (roudix.contentCreation.obs.plugins)
  ++ lib.optional (ccEnabled && (ccCfg.obs.enable or true)) obsPackage
  # Chosen video editor (roudix.contentCreation.videoEditor)
  ++ lib.optional (ccEnabled && videoEditorPackage != null) videoEditorPackage
  # Client de chat Twitch (roudix.contentCreation.streaming.chatterino.enable)
  ++ lib.optional (ccEnabled && (ccCfg.streaming.chatterino.enable or false)) pkgs.chatterino2
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

{ config, lib, pkgs, roudixBranding, ... }:
let
  isCosmic = config.roudix.desktop.type == "cosmic";

  # Default Roudix wallpaper (installed by pkgs/roudix-branding, linked into
  # /run/current-system/sw/share/backgrounds through desktop-integration.nix).
  wallpaper = "/run/current-system/sw/share/backgrounds/roudix/roudix-kitsune.png";

  # ── How Roudix ships its COSMIC defaults without overriding the user ─────
  # cosmic-config (libcosmic) looks a key up in the user's own
  # ~/.config/cosmic/<id>/v<N>/<key> first, and only when that file does not
  # exist falls back to <XDG_DATA_DIRS>/cosmic/<id>/v<N>/<key>. So everything
  # below is a DEFAULT, exactly like the dconf defaults of gnome.nix and
  # cinnamon.nix: first login gets the Roudix layout, the moment the user
  # pins/unpins an app, moves the wallpaper or changes the layout in COSMIC
  # Settings their own file is written and wins, and a rebuild never touches it.
  # The values are RON, the format of the cosmic-config files.
  ron = {
    str  = s: ''"${s}"'';
    list = l: "[" + lib.concatStringsSep ", " l + "]";
  };

  mkDefault = id: key: text:
    pkgs.writeTextDir "share/cosmic/${id}/v1/${key}" text;

  # Same browser -> app id table as gnome.nix / cinnamon.nix, WITHOUT the
  # ".desktop" suffix: that is how cosmic-app-list identifies an application.
  # An id that matches no installed app is silently skipped, so a wrong guess
  # only means "not pinned".
  browserIds = {
    "brave"                = [ "brave-browser" ];
    "brave-beta"           = [ "brave-browser-beta" ];
    "brave-nightly"        = [ "brave-browser-nightly" ];
    "brave-origin"         = [ "brave-origin" ];
    "brave-origin-beta"    = [ "brave-origin-beta" ];
    "brave-origin-nightly" = [ "brave-origin-nightly" ];
    "helium"               = [ "helium" "helium-browser" ];
    "vivaldi"              = [ "vivaldi-stable" ];
    "chromium"             = [ "chromium-browser" ];
    "ungoogled-chromium"   = [ "chromium-browser" ];
    "firefox"              = [ "firefox" ];
    "librewolf"            = [ "librewolf" ];
    "google-chrome"        = [ "google-chrome" ];
    "microsoft-edge"       = [ "microsoft-edge" ];
  };
  zenIds =
    if config.roudix.zen.variant == "beta"
    then [ "zen-beta" "zen" ]
    else [ "zen-twilight" "zen" ];
  terminalIds = {
    ghostty   = [ "com.mitchellh.ghostty" ];
    kitty     = [ "kitty" ];
    alacritty = [ "Alacritty" ];
    foot      = [ "foot" ];
    wezterm   = [ "org.wezfurlong.wezterm" ];
    ptyxis    = [ "org.gnome.Ptyxis" ];
    konsole   = [ "org.kde.konsole" ];
  };

  # Same idea as the GNOME dash and the Plasma task manager: the browser(s)
  # chosen in Roudix, the file manager, Roudix Store (replaces the software
  # center), the user's terminal and the settings. COSMIC ships its own file
  # manager and settings app, so those are the native ones.
  favoriteApps =
    lib.concatMap (b: browserIds.${b} or [ ]) config.roudix.browsers
    ++ lib.optionals config.roudix.zen.enable zenIds
    ++ [ "com.system76.CosmicFiles" ]
    ++ terminalIds.${config.roudix.terminal} or [ ]
    ++ [
      "io.roudix.store"
      "com.system76.CosmicSettings"
    ];

  # ── Roudix apps ─────────────────────────────────────────────────────────
  # They all carry Categories=...;X-Roudix; in their .desktop files (see
  # pkgs/roudix-*/default.nix). The COSMIC app library turns that tag into a
  # "Roudix" folder, like the "Roudix" folders of GNOME and KDE.
  roudixAppIds = [
    "io.roudix.config"
    "io.roudix.hw-sync"
    "io.roudix.kernel-switcher"
    "io.roudix.scheduler"
    "io.roudix.store"
    "io.roudix.switcher"
    "io.roudix.welcome"
  ];

  # The app library lists an app in every folder whose category it matches, so
  # the Roudix apps (System;Settings;...) would also show up in "System" and
  # "Utilities". They are excluded there. The three COSMIC folders are the
  # stock ones of cosmic-applibrary (src/app_group.rs), copied as they are:
  # `groups` replaces the whole default list, so they have to be repeated.
  appFolder = { name, categories, include ? [ ], exclude ? [ ] }:
    ''(name: ${ron.str name}, icon: "folder-symbolic", filter: Categories(categories: ${ron.list (map ron.str categories)}, exclude: ${ron.list (map ron.str exclude)}, include: ${ron.list (map ron.str include)}))'';

  appLibraryGroups = ron.list [
    ''(name: "Roudix", icon: "roudix-logo", filter: Categories(categories: ["X-Roudix"], exclude: [], include: []))''
    (appFolder {
      name = "cosmic-office";
      categories = [ "Office" ];
      include = [ "org.gnome.Totem" "org.gnome.eog" "simple-scan" "thunderbird" ];
    })
    (appFolder {
      name = "cosmic-system";
      categories = [ "System" ];
      include = [ "gnome-language-selector" "im-config" "org.freedesktop.IBus.Setup" "system76-driver" ];
      exclude = [ "com.system76.CosmicStore" "com.system76.CosmicTerm" ] ++ roudixAppIds;
    })
    (appFolder {
      name = "cosmic-utilities";
      categories = [ "Utility" ];
      include = [ "nm-connection-editor" ];
      exclude = [ "com.system76.CosmicEdit" "com.system76.CosmicFiles" ] ++ roudixAppIds;
    })
  ];

  # ── Keyboard layout as seen by cosmic-comp ──────────────────────────────
  # COSMIC reads its layout from its own config (Settings > Keyboard), not
  # from services.xserver.xkb, so roudix.keyboardLayout is mirrored there as a
  # default. Variant "" = base layout.
  kbOptions = config.roudix.keyboardOptions;
  xkbConfig =
    ''(rules: "", model: "pc104", layout: ${ron.str config.roudix.keyboardLayout}, variant: ${ron.str config.roudix.keyboardVariant}, options: ${if kbOptions == "" then "None" else ''Some(${ron.str kbOptions})''}, repeat_delay: 600, repeat_rate: 25)'';

  # ── Roudix colour scheme (COSMIC theme) ─────────────────────────────────
  # assets/cosmic/ holds the Roudix theme as cosmic-config files, generated
  # from assets/palette/Roudix.json by scripts/gen-cosmic-theme (libcosmic's
  # own ThemeBuilder, so the derived colours are exactly what Settings >
  # Appearance would produce). Same mechanism as the rest of this file: they
  # land in share/cosmic/<id>/v2/ as DEFAULTS, so the first login is Roudix
  # orange on warm dark, and picking another accent/theme in COSMIC Settings
  # writes the user's own file, which wins. No Home Manager involved.
  themeDefaults = pkgs.runCommand "roudix-cosmic-theme" { } ''
    mkdir -p $out/share
    cp -r ${../../../assets/cosmic} $out/share/cosmic
  '';

  # ── Login screen wallpaper ────────────────────────────────────────────
  # cosmic-greeter has no system-wide wallpaper setting: it shows the
  # wallpaper cosmic-bg last applied for each user (~/.local/state/cosmic/
  # com.system76.CosmicBackground), and when there is none yet (fresh install,
  # first boot) it falls back to a picture compiled into the binary
  # (res/background.jpg). Roudix's Kitsune is already the default desktop
  # wallpaper above, so after the first login the greeter follows it; this
  # replaces the compiled-in fallback so the very first greeter matches too.
  # It rebuilds cosmic-greeter from source (not in the binary cache).
  greeterBackground = pkgs.runCommand "roudix-greeter-background.jpg"
    { nativeBuildInputs = [ pkgs.imagemagick ]; }
    ''
      magick ${../../../assets/wallpapers/roudix-kitsune.png} -quality 90 $out
    '';

  greeterPackage = pkgs.cosmic-greeter.overrideAttrs (old: {
    postPatch = (old.postPatch or "") + ''
      install -Dm644 ${greeterBackground} res/background.jpg
    '';
  });

  cosmicDefaults = pkgs.symlinkJoin {
    name  = "roudix-cosmic-defaults";
    paths = [
      themeDefaults
      (mkDefault "com.system76.CosmicAppList" "favorites" (ron.list (map ron.str favoriteApps)))
      (mkDefault "com.system76.CosmicAppLibrary" "groups" appLibraryGroups)
      (mkDefault "com.system76.CosmicComp" "xkb_config" xkbConfig)
      # Wallpaper: the same Kitsune as the other desktops, same on all outputs.
      (mkDefault "com.system76.CosmicBackground" "same-on-all" "true")
      (mkDefault "com.system76.CosmicBackground" "all"
        ''(output: "all", source: Path(${ron.str wallpaper}), filter_by_theme: false, rotation_frequency: 300, filter_method: Lanczos, scaling_mode: Zoom, sampling_method: Alphanumeric)'')
    ];
  };
in
{
  config = lib.mkIf isCosmic {
    # ── Session + greeter ─────────────────────────────────────────────────
    # COSMIC is a Wayland desktop (cosmic-comp), with its own greeter.
    services.desktopManager.cosmic.enable = true;
    services.displayManager.cosmic-greeter.enable = true;
    services.displayManager.cosmic-greeter.package = greeterPackage;

    # cosmic-greeter-daemon reads each user's COSMIC config to paint the
    # greeter (theme, wallpaper). Without XDG_DATA_DIRS a systemd service only
    # looks in /usr/share, so it would never see the Roudix defaults above.
    systemd.services.cosmic-greeter-daemon.environment.XDG_DATA_DIRS =
      "/run/current-system/sw/share";
    services.displayManager.defaultSession = "cosmic";

    # ── Keyring ───────────────────────────────────────────────────────────
    # cosmic-greeter runs on greetd: same PAM service as the other greetd
    # desktops (niri.nix, umbriel.nix), unlocked at login.
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.greetd.enableGnomeKeyring = true;

    # ── Look & feel defaults (see the top of this file) ───────────────────
    environment.pathsToLink = [ "/share/cosmic" "/share/desktop-directories" ];

    # Roudix has its own scheduler stack (SCX, optional ananicy-cpp): two
    # process schedulers fighting over priorities help nobody. The nixpkgs
    # COSMIC module turns system76-scheduler on with mkDefault, so this needs
    # a priority just above it (a second mkDefault would be a conflict); a
    # plain `services.system76-scheduler.enable = true;` in local.nix still
    # wins over both.
    services.system76-scheduler.enable = lib.mkOverride 900 false;

    # The portal stack (cosmic + gtk) comes with the nixpkgs COSMIC module.
    # Roudix Store replaces the COSMIC Store (the Flatpak side lives in Roudix
    # Store's Flatpak tab).
    environment.cosmic.excludePackages = with pkgs; [
      cosmic-store
    ];

    environment.systemPackages = with pkgs; [
      # hiPrio: Roudix's defaults win over any file with the same path
      # shipped by a COSMIC package.
      (lib.hiPrio cosmicDefaults)
      (lib.hiPrio roudixBranding)
      (writeTextDir "share/desktop-directories/roudix.directory" ''
        [Desktop Entry]
        Type=Directory
        Name=Roudix
        Icon=roudix-logo
      '')
      papirus-icon-theme
      capitaine-cursors
    ];
  };
}

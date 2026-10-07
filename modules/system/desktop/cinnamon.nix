{ config, lib, pkgs, roudixBranding, ... }:
let
  isCinnamon = config.roudix.desktop.type == "cinnamon";

  # Default Roudix wallpaper (installed by pkgs/roudix-branding, linked into
  # /run/current-system/sw/share/backgrounds through desktop-integration.nix).
  kitsunePath = "/run/current-system/sw/share/backgrounds/roudix/roudix-kitsune.png";
  wallpaper   = "file://${kitsunePath}";

  # ── LightDM (slick-greeter) wallpaper ─────────────────────────────────
  # slick-greeter has no settings app, it only reads `background=` from its
  # config. That config lives in the Nix store, so the path it points to is
  # a mutable file instead: by default a symlink to the Kitsune wallpaper,
  # replaced by `roudix-lightdm-wallpaper <image>` — no rebuild needed.
  lightdmBgDir = "/var/lib/roudix/lightdm";
  lightdmBg    = "${lightdmBgDir}/background.png";

  roudixLightdmWallpaper = pkgs.writeShellApplication {
    name = "roudix-lightdm-wallpaper";
    runtimeInputs = with pkgs; [ coreutils file imagemagick ];
    text = ''
      usage() {
        cat <<'EOF'
      Usage: roudix-lightdm-wallpaper <image>   set the LightDM login wallpaper
             roudix-lightdm-wallpaper --reset   restore the Roudix Kitsune default
      EOF
      }

      if [ $# -ne 1 ]; then usage >&2; exit 2; fi
      case "$1" in -h|--help) usage; exit 0 ;; esac

      # Writing to /var/lib needs root; keep the cwd so relative paths work.
      if [ "$(id -u)" -ne 0 ]; then
        exec /run/wrappers/bin/sudo "$0" "$@"
      fi

      dest="${lightdmBg}"

      if [ "$1" = "--reset" ]; then
        ln -sfn "${kitsunePath}" "$dest"
        echo "LightDM wallpaper reset to Roudix Kitsune."
        exit 0
      fi

      src="$1"
      if [ ! -f "$src" ] || [ ! -r "$src" ]; then
        echo "roudix-lightdm-wallpaper: cannot read '$src'" >&2
        exit 1
      fi
      case "$(file --brief --mime-type -- "$src")" in
        image/*) ;;
        *) echo "roudix-lightdm-wallpaper: '$src' is not an image" >&2; exit 1 ;;
      esac

      mkdir -p "$(dirname "$dest")"
      tmp="$(mktemp "$(dirname "$dest")/.background.XXXXXX")"
      trap 'rm -f "$tmp"' EXIT
      # Same normalisation as roudix-branding (8-bit RGB, no alpha, no
      # metadata): avoids the gdk-pixbuf/libpng crashes on odd PNGs. Written
      # to a temp file then moved, so the default symlink is replaced instead
      # of being followed into the read-only store.
      magick "''${src}[0]" -strip -depth 8 "PNG24:$tmp"
      chmod 0644 "$tmp"
      mv -f "$tmp" "$dest"
      trap - EXIT
      echo "LightDM wallpaper updated (visible at the next login screen)."
    '';
  };

  # Same browser -> .desktop id table as gnome.nix (kept in sync by hand;
  # an unknown id is silently ignored by Cinnamon's menu, so a wrong guess
  # only means "not pinned").
  browserDesktopIds = {
    "brave"                = [ "brave-browser.desktop" ];
    "brave-beta"           = [ "brave-browser-beta.desktop" ];
    "brave-nightly"        = [ "brave-browser-nightly.desktop" ];
    "brave-origin"         = [ "brave-origin.desktop" ];
    "brave-origin-beta"    = [ "brave-origin-beta.desktop" ];
    "brave-origin-nightly" = [ "brave-origin-nightly.desktop" ];
    "helium"               = [ "helium.desktop" "helium-browser.desktop" ];
    "vivaldi"              = [ "vivaldi-stable.desktop" ];
    "chromium"             = [ "chromium-browser.desktop" ];
    "ungoogled-chromium"   = [ "chromium-browser.desktop" ];
    "firefox"              = [ "firefox.desktop" ];
    "librewolf"            = [ "librewolf.desktop" ];
    "google-chrome"        = [ "google-chrome.desktop" ];
    "microsoft-edge"       = [ "microsoft-edge.desktop" ];
  };

  favoriteApps =
    lib.concatMap (b: browserDesktopIds.${b} or [ ]) config.roudix.browsers
    ++ [
      "nemo.desktop"
      "io.roudix.store.desktop"
      "cinnamon-settings.desktop"
    ];

  # Panel (grouped-window-list) pinned apps: the default browser (first of
  # roudix.browsers), Roudix Store and Cinnamon Settings.
  pinnedApps =
    lib.optionals (config.roudix.browsers != [ ])
      (browserDesktopIds.${lib.head config.roudix.browsers} or [ ])
    ++ [
      "io.roudix.store.desktop"
      "cinnamon-settings.desktop"
    ];

  # ── Roudix look & feel, as dconf DEFAULTS ─────────────────────────────
  # Same mechanism as gnome.nix: written to the *system* dconf database, so
  # it only applies to keys the user never touched. A rebuild never reverts
  # a choice made in Cinnamon Settings.
  cinnamonDefaults = {
    "org/cinnamon" = {
      # Favorites of the Cinnamon menu (the browser(s) chosen in Roudix, Nemo,
      # Roudix Store, Settings). The panel's window-list pinning and the menu
      # icon are NOT dconf keys but per-applet defaults, see cinnamonDefaultsOverlay.
      favorite-apps = favoriteApps;
    };
    "org/cinnamon/desktop/background" = {
      picture-uri     = wallpaper;
      picture-options = "zoom";
    };
    "org/cinnamon/desktop/interface" = {
      gtk-theme    = "Mint-Y-Dark-Aqua";
      icon-theme   = "Papirus-Dark";
      cursor-theme = "capitaine-cursors-white";
      cursor-size  = lib.gvariant.mkInt32 24;
    };
    "org/cinnamon/theme".name = "Mint-Y-Dark-Aqua";
    "org/cinnamon/desktop/wm/preferences".theme = "Mint-Y-Dark-Aqua";
    # libadwaita / GTK4 apps follow the color-scheme, which they get from the
    # settings portal. On Cinnamon that portal is xdg-desktop-portal-xapp,
    # which reads its own key (org.x.apps.portal) — not the GNOME one — so
    # both are set: otherwise GTK4 apps stay light with a dark theme.
    "org/gnome/desktop/interface" = {
      color-scheme = "prefer-dark";
      gtk-theme    = "Mint-Y-Dark-Aqua";
    };
    "org/x/apps/portal".color-scheme = "prefer-dark";
    # Terminal chosen in Roudix (gnome-terminal is excluded below).
    "org/cinnamon/desktop/default-applications/terminal" = {
      exec     = config.roudix.terminal;
      exec-arg = "-e";
    };
  };

  # ── Per-applet defaults (panel pins, menu icon) ───────────────────────
  # Cinnamon applets keep their settings in ~/.config/cinnamon/spices/<applet>/
  # <instance>.json, created on first load from the applet's
  # settings-schema.json. Seeding those files from home-manager depends on the
  # instance ids and the JSON layout, and did not work. Patching the schema
  # defaults does not: every new instance gets them, whatever its id (this is
  # how distros ship their own pinned apps). It rebuilds Cinnamon locally.
  # The attribute name is fixed on purpose: computing it from `prev` (e.g.
  # checking that prev.cinnamon is a derivation) forces the package while
  # pkgs itself is being built -> "infinite recursion encountered".
  cinnamonDefaultsOverlay = final: prev: {
    cinnamon = prev.cinnamon.overrideAttrs (old: {
      nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.jq ];
      postInstall = (old.postInstall or "") + ''
        patch_default() {
          f="$out/share/cinnamon/applets/$1/settings-schema.json"
          if [ -f "$f" ] && jq -e --arg k "$2" 'has($k)' "$f" > /dev/null; then
            jq --arg k "$2" --argjson v "$3" '.[$k].default = $v' "$f" > "$f.tmp"
            mv "$f.tmp" "$f"
          else
            echo "roudix: $1 has no '$2' key, default left unchanged" >&2
          fi
        }
        patch_default grouped-window-list@cinnamon.org pinned-apps '${builtins.toJSON config.roudix.desktop.cinnamon.pinnedApps}'
        patch_default menu@cinnamon.org menu-icon-custom true
        patch_default menu@cinnamon.org menu-icon '"roudix-logo"'
      '';
    });
  };

  # Same "Roudix" application-menu category as kde.nix: Roudix apps carry
  # Categories=...;X-Roudix; and this merged menu groups them in one folder.
  roudixMenu = {
    text = ''
      <!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
        "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
      <Menu>
        <Name>Applications</Name>
        <Menu>
          <Name>System</Name>
          <Exclude><Category>X-Roudix</Category></Exclude>
        </Menu>
        <Menu>
          <Name>Settingsmenu</Name>
          <Exclude><Category>X-Roudix</Category></Exclude>
        </Menu>
        <Menu>
          <Name>Roudix</Name>
          <Directory>roudix.directory</Directory>
          <Include><Category>X-Roudix</Category></Include>
        </Menu>
      </Menu>
    '';
  };
in
{
  options.roudix.desktop.cinnamon.pinnedApps = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = pinnedApps;
    description = ''
      .desktop ids pinned in the Cinnamon panel window list at first login
      (default browser, Roudix Store, Settings). Applied once per user, never
      re-applied afterwards. Override in local.nix.
    '';
  };

  config = lib.mkIf isCinnamon {
    # ── X11 session + LightDM ────────────────────────────────────────────────
    # Cinnamon is an X11 desktop (its Wayland session is still experimental).
    # That is the point of choosing it on older hardware: GNOME 49 is
    # Wayland-only. The nixpkgs module only configures the slick greeter, it
    # does not turn LightDM on.
    nixpkgs.overlays = [ cinnamonDefaultsOverlay ];

    services.xserver.enable = true;
    services.xserver.displayManager.lightdm.enable = true;
    # Mutable file (default: Kitsune) — change it with roudix-lightdm-wallpaper.
    services.xserver.displayManager.lightdm.background = lightdmBg;
    systemd.tmpfiles.rules = [
      "d /var/lib/roudix 0755 root root -"
      "d ${lightdmBgDir} 0755 root root -"
      # `L` (not `L+`): created once, never replaces a wallpaper the user set.
      "L ${lightdmBg} - - - - ${kitsunePath}"
    ];
    services.displayManager.defaultSession = "cinnamon";
    services.xserver.desktopManager.cinnamon.enable = true;

    # X11 keyboard layout (greeter + session); other DEs get theirs through
    # their own compositor/greeter settings, see keyboard.nix.
    services.xserver.xkb = {
      layout  = config.roudix.keyboardLayout;
      variant = config.roudix.keyboardVariant;
    };

    # ── Dark GTK4 ─────────────────────────────────────────────────────────────
    # The settings portal backend that serves color-scheme to libadwaita apps
    # (gtk reads org.gnome.desktop.interface, see the dconf defaults), plus
    # the GTK4 fallback for apps that do not use libadwaita.
    xdg.portal.extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
    environment.etc."xdg/gtk-4.0/settings.ini".text = ''
      [Settings]
      gtk-application-prefer-dark-theme=1
    '';

    # ── Keyring ───────────────────────────────────────────────────────────────
    # The nixpkgs Cinnamon module already enables gnome-keyring; unlock it at
    # the LightDM login.
    security.pam.services.lightdm.enableGnomeKeyring = true;

    # ── Look & feel (dconf defaults) ──────────────────────────────────────────
    programs.dconf.enable = true;
    programs.dconf.profiles.user.databases = [
      { settings = cinnamonDefaults; }
    ];

    # ── Menu: "Roudix" category ──────────────────────────────────────────────
    # Dropped in both merge dirs, as in kde.nix, because the directory name
    # depends on XDG_MENU_PREFIX.
    environment.etc."xdg/menus/applications-merged/roudix.menu"          = roudixMenu;
    environment.etc."xdg/menus/cinnamon-applications-merged/roudix.menu" = roudixMenu;

    # Roudix provides its own terminal; warpinator opens LAN ports nobody
    # asked for on a hands-off family machine.
    environment.cinnamon.excludePackages = with pkgs; [
      gnome-terminal
      warpinator
    ];

    environment.systemPackages = with pkgs; [
      (writeTextDir "share/desktop-directories/roudix.directory" ''
        [Desktop Entry]
        Type=Directory
        Name=Roudix
        Icon=roudix-logo
      '')
      (lib.hiPrio roudixBranding)
      papirus-icon-theme
      capitaine-cursors
      roudixLightdmWallpaper
    ];
  };
}

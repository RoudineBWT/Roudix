{ pkgs, lib, username, osConfig, roudixSwitcher, roudixBranding, roudix-kernel-switcher, roudix-hw-sync, roudix-disk, roudix-firewall, roudixStore, ... }:
let
  desktopType = osConfig.roudix.desktop.type;
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isHyprlandOrNiri = desktopType == "hyprland" || desktopType == "niri";
in
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.11";

  imports = [
    # Roudix.json palette -> config.roudix.palette / roudixPalette (see theming/palette.nix)
    ./theming/palette.nix
    # Roudix colours for the chosen terminal (ghostty/kitty/alacritty/foot/wezterm)
    ./theming/terminal-theme.nix
    ./shell
    ./gaming
    # GTK theme/icons/cursor + dconf for GSettings-reading apps (GTK3/4,
    # Chromium-family browsers incl. Helium). Imported unconditionally;
    # a no-op on gnome/kde, which theme themselves natively.
    ./theming/gtk-theme.nix
    # App-selection implementations (which package for each roudix.*
    # choice — discord, terminal, editor, browsers, content creation...).
    # Mirrors modules/system/apps/, which only declares the options.
    ./apps
    # roudix-welcome: écran de bienvenue au premier démarrage de session
    # (roudix.welcome.enable, default true — voir roudix-welcome.nix).
    ./roudix-welcome.nix
    ./roudix-config.nix
  ] ++ lib.optional (builtins.pathExists ./dev/ssh.nix) ./dev/ssh.nix
    ++ lib.optional (builtins.pathExists ./dev/gitwatch.nix) ./dev/gitwatch.nix
    ++ lib.optional (builtins.pathExists ./dev/git.nix) ./dev/git.nix
    ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix;

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
        # Dux Shell 2.0 renamed DankMaterialShell/ -> dms/ (and migrates on first
        # launch). Only seed the legacy dir if it is the only one that exists,
        # otherwise we would recreate a conflicting pair.
        if [ -d "$HOME/.local/state/DankMaterialShell" ] && [ ! -e "$HOME/.local/state/dms" ]; then
          dms_state="$HOME/.local/state/DankMaterialShell"
        else
          dms_state="$HOME/.local/state/dms"
        fi
        if [ ! -f "$dms_state/session.json" ]; then
          mkdir -p "$dms_state"
          printf '%s' '{"wallpaperPath":"${roudixBranding}/share/backgrounds/roudix/roudix-dark.png","wallpaperFillMode":"PreserveAspectCrop"}' \
            > "$dms_state/session.json"
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
    roudix-hw-sync
    roudix-disk
    roudix-firewall
    roudixStore
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
    bibata-cursors
    starship
  ])
  ++ [ pkgs.xdg-user-dirs ]
  ++ lib.optional (desktopType != "kde") pkgs.xdg-user-dirs-gtk;

  # Do NOT enable home-manager's xdg.userDirs: it writes ~/.config/user-dirs.dirs
  # with hardcoded English names (Documents, Downloads, ...) and creates them,
  # whatever the system language. xdg-user-dirs-update picks the names from the
  # session locale instead (Documents -> Documents, Downloads -> Téléchargements...).
  xdg.userDirs.enable = false;

  # xdg-user-dirs-gtk only runs through XDG autostart, which niri / mangowc /
  # hyprland sessions do not reliably honour — so run it ourselves at login.
  # Idempotent: it never renames existing folders or overrides a user's
  # ~/.config/user-dirs.dirs.
  systemd.user.services.xdg-user-dirs-update = {
    Unit.Description = "Create XDG user directories in the session language";
    Service = {
      Type = "oneshot";
      ExecStart = "${pkgs.xdg-user-dirs}/bin/xdg-user-dirs-update";
    };
    Install.WantedBy = [ "default.target" ];
  };

  # On GNOME this key is a system dconf *default* instead (see
  # modules/system/desktop/gnome.nix), so that changing it in Tweaks sticks
  # across rebuilds. home-manager's dconf.settings would reset it every switch.
  dconf.settings = lib.mkIf (desktopType != "gnome") {
    "org/gnome/desktop/interface" = {
      gtk-enable-primary-paste = true;
    };
  };

  programs.home-manager.enable = true;
}

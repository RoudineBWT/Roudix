{ pkgs, lib, username, osConfig, roudixSwitcher, roudixBranding, roudix-kernel-switcher, ... }:
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

  programs.home-manager.enable = true;
}

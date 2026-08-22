{ pkgs, config, lib, ... }:

{
  programs.umbriel.settings.window_rule = [
    # ─── Discord ──────────────────────────────────────────────────────────
    {
      match.app_id = "discord";
      default_workspace = 1;
      default_maximize = true;
    }

    # ─── Element ──────────────────────────────────────────────────────────
    {
      match.app_id = "Element";
      default_workspace = 2;
      default_maximize = true;
    }

    # ─── Ghostty ──────────────────────────────────────────────────────────
    {
      match.app_id = "com.mitchellh.ghostty";
      default_floating = true;
    }

    # ─── Telegram ─────────────────────────────────────────────────────────
    {
      match.app_id = "org.telegram.desktop";
      default_workspace = 3;
    }

    # ─── Firefox ──────────────────────────────────────────────────────────
    {
      match.app_id = "^firefox$";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.title = "About Mozilla Firefox";
      default_workspace = 4;
      default_floating = true;
    }
    {
      match.app_id = "^firefox$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }

    # ─── Zed ──────────────────────────────────────────────────────────────
    {
      match.app_id = "dev.zed.Zed";
      default_workspace = 5;
      default_maximize = true;
    }

    # ─── Zen Browser ──────────────────────────────────────────────────────
    {
      match.app_id = "zen-twilight";
      default_workspace = 4;
      default_maximize = true;
      opacity = 0.95;
    }
    {
      match.title = "About Zen Twilight";
      default_workspace = 4;
      default_floating = true;
      opacity = 0.95;
    }
    {
      match.app_id = "^zen$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }

    # ─── Brave ────────────────────────────────────────────────────────────
    {
      match.app_id = "brave-origin-beta";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.app_id = "brave-browser";
      default_workspace = 1;
      default_maximize = true;
    }
    {
      match.app_id = "^brave$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }

    # ─── Nautilus ─────────────────────────────────────────────────────────
    {
      match.app_id = "^org.gnome.Nautilus$";
      match.title = "^Save As$";
      default_focused = true;
    }
    {
      match.app_id = "^org\\.gnome\\.Nautilus$";
      default_workspace = 6;
      default_maximize = true;
    }

    # ─── Steam ────────────────────────────────────────────────────────────
    {
      match.app_id = "steam";
      default_workspace = 7;
      default_maximize = true;
    }
    {
      match.app_id = "steam";
      match.title = "^notificationtoasts_\d+_desktop$";
      # default_floating_position = { x = 10; y = 10; relative_to = "bottom-right"; };  # Supprimé (non supporté)
    }
    {
      match.title = "Friends List";
      default_workspace = 7;
      default_floating = true;
    }

    # ─── Jeux ─────────────────────────────────────────────────────────────
    {
      match.app_id = "^(steam_app_.*)$";
      default_workspace = 7;
      default_fullscreen = true;
    }
    {
      match.app_id = "^heroic$";
      default_workspace = 7;
      default_fullscreen = true;
    }
    {
      match.app_id = "org.prismlauncher.PrismLauncher";
      default_workspace = 7;
      default_maximize = true;
    }
    {
      match.app_id = "Minecraft";
      default_workspace = 7;
      default_fullscreen = true;
    }

    # ─── Autres ────────────────────────────────────────────────────────────
    {
      match.app_id = "openrgb";
      default_workspace = 7;
    }
    {
      match.app_id = "kitty";
      default_workspace = 5;
      default_floating = true;
    }
    {
      match.app_id = "org.gnome.Ptyxis";
      default_workspace = 5;
    }
    {
      match.app_id = "org.gnome.TextEditor";
      default_workspace = 6;
    }
    {
      match.app_id = "Spotify";
      default_workspace = 8;
      default_maximize = true;
    }
    {
      match.app_id = "com.kde.easyeffects";
      default_workspace = 8;
    }
    {
      match.app_id = "com.github.wwmm.easyeffects";
      default_workspace = 8;
    }
  ];
}

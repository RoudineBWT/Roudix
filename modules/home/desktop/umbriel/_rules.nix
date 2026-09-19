## _rules.nix — Umbriel: [[window_rule]] and [[layer_rule]].
##
## Every matching rule contributes its settings; on a conflict over the
## same key, the LOWEST rule in the list wins.
##
## `default_floating_size_px` sets a pixel-perfect floating size (used
## below); `default_floating_size` sets it as a fraction of the usable
## area instead (better if you change resolution often). It expects a
## TABLE — `{ width = <int>; height = <int>; }` — not an array.
##
## Docs: https://docs.noctalia.dev/umbriel/window-rules/
{ lib, osConfig, ... }:
let
  # roudix.umbriel.scratchpadApps (declared in
  # modules/system/desktop/umbriel.nix): toggles Discord/Telegram/Spotify
  # between fixed tiling (false, default) and named scratchpads (true).
  # See _binds.nix for the keybind side, and _animation.nix for the
  # scratchpad shader (applies in both cases; it's a no-op when no
  # scratchpad is shown).
  scratchpadApps = osConfig.roudix.umbriel.scratchpadApps or false;
in
{
  programs.umbriel.settings = {
  # scratchpad = [] while scratchpadApps is false: no [[scratchpad]] entry
  # in TOML → Umbriel keeps the implicit "default" scratchpad, so
  # Mod+Shift+Space/Mod+Space/etc. below work without a suffix.
  scratchpad = lib.optionals scratchpadApps [
    { name = "misc"; }
    { name = "communication"; }
    { name = "music"; }
  ];

  window_rule = [
    # Discord / Element: Umbriel has no "fixed-width tiled" equivalent
    # (default_width only accepts a fraction), so these are floating to
    # match the original niri size/position exactly.
    (
    {
      # A scratchpad always floats: default_floating=false only makes
      # sense in tiled mode, default_scratchpad only in scratchpad mode —
      # hence the conditional // instead of hardcoding both keys. Size and
      # position stay the same in both cases so Discord+Telegram sit
      # side by side (top_left/top_right).
      match.app_id = "^(discord|Element)$";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating_size_px = { width = 1316; height = 1011; };
      default_position = { x = 0; y = 0; anchor = "top_left"; };
    } // (if scratchpadApps
          then { default_scratchpad = "communication"; }
          else { default_floating = false; })
    )
    (
    {
      # Under Xwayland (native Wayland session capture is broken on this
      # machine), Telegram Desktop exposes the legacy X11 class
      # "TelegramDesktop" rather than the native Wayland app_id
      # "org.telegram.desktop". Both forms are kept in case Telegram
      # later runs natively under Wayland here.
      match.app_id = "^(org\\.telegram\\.desktop|TelegramDesktop)$";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating_size_px = { width = 555; height = 1011; };
      default_position = { x = 0; y = 0; anchor = "top_right"; };
    } // (if scratchpadApps
          then { default_scratchpad = "communication"; }
          else { default_floating = false; })
    )
    {
      match.app_id = "^com\\.mitchellh\\.ghostty$";
      default_floating = true;
      default_floating_size_px = { width = 1505; height = 755; };
      blur = true;
    }
    {
      match.app_id = "^firefox$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
    }
    {
      match.title = "^About Mozilla Firefox$";
      default_output = "DP-1";
      default_workspace = 1;
      default_floating = true;
    }
    {
      match.app_id = "^dev\\.zed\\.Zed$";
      default_output = "DP-1";
      default_workspace = 2;
      default_maximize = true;
    }
    {
      match.app_id = "^zen-twilight$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
      opacity = 0.95;
      blur = true;
    }
    {
      match.title = "^About Zen Twilight$";
      default_output = "DP-1";
      default_workspace = 1;
      default_floating = true;
      opacity = 0.95;
      blur = true;
    }
    {
      match.app_id = "^brave-origin-beta$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
    }
    {
      match.app_id = "^steam$";
      default_output = "DP-1";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.app_id = "^openrgb$";
      default_output = "DP-1";
      default_workspace = 4;
    }
    {
      match.app_id = "^kitty$";
      default_output = "DP-1";
      default_workspace = 3;
      default_floating = true;
    }
    {
      match.app_id = "^org\\.gnome\\.Ptyxis$";
      default_output = "DP-1";
      default_workspace = 3;
    }
    {
      match.app_id = "^brave-browser$";
      default_output = "DP-3";
      default_workspace = 3;
      default_maximize = true;
    }
    {
      match.app_id = "^steam_app_.*$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
      # Allows tearing on this window (requires tearing=true on output
      # DP-1, see _output.nix). Umbriel only enables it when the window
      # is actually fullscreen.
      tearing = true;
    }
    {
      match.app_id = "^heroic$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
    }
    {
      match.app_id = "^org\\.prismlauncher\\.PrismLauncher$";
      default_output = "DP-1";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.app_id = "^Minecraft$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
      tearing = true;
    }
    {
      match.app_id = "^firefox$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    {
      match.app_id = "^zen$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    {
      match.app_id = "^brave$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    # Steam notification toasts: default_focused=false + default_pinned=true
    # keeps the toast visible even over a fullscreen game.
    {
      match.title = "^notificationtoasts_\\d+_desktop$";
      default_floating = true;
      default_position = { x = 10; y = 10; anchor = "bottom_right"; };
      default_focused = false;
      default_pinned = true;
    }
    {
      match.title = "^Friends List$";
      default_output = "DP-1";
      default_workspace = 4;
      default_floating = true;
    }
    # Generic dialogs/utilities, matching ANY parent app (not just
    # Nautilus): file pickers via xdg-desktop-portal, zenity,
    # pavucontrol, calculator, etc.
    {
      match.app_id = "^(Emulator|zenity|xdg-desktop-portal|qalculate-gtk|org\\.pulseaudio\\.pavucontrol)$";
      default_floating = true;
    }
    {
      match.title = "^(Open File|Select|Choose a wallpaper|Open Folder|Save As|Library|Choose Where to Download|File Operation Progress|Rename|Copy Files|Move Files|Search Files)";
      default_floating = true;
    }
    {
      # ⚠ niri's case-insensitive (?i) prefix isn't confirmed supported by
      # Umbriel (ECMAScript regex, no flags mentioned in the doc) — verify
      # that mixed-case dialog titles are still excluded correctly.
      match.app_id = "^org\\.gnome\\.Nautilus$";
      match.title = "^(?!(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$).*$";
      default_output = "DP-1";
      default_workspace = 5;
      default_maximize = true;
    }
    {
      match.app_id = "^org\\.gnome\\.TextEditor$";
      default_output = "DP-1";
      default_workspace = 5;
    }
    (
    {
      # default_maximize (tiled) and default_scratchpad+default_floating_size
      # (scratchpad, sized as a fraction to stay correct across resolution
      # changes) are mutually exclusive, hence the conditional //.
      match.app_id = "^Spotify$";
      default_output = "DP-3";
      default_workspace = 2;
    } // (if scratchpadApps
          then { default_scratchpad = "music"; default_floating_size = { width = 0.8; height = 0.85; }; }
          else { default_maximize = true; })
    )
    {
      match.app_id = "^(com\\.kde\\.easyeffects|com\\.github\\.wwmm\\.easyeffects)$";
      default_output = "DP-3";
      default_workspace = 2;
    }
    {
      match.app_id = "^dev\\.noctalia\\.Noctalia$";
      default_floating = true;
      default_floating_size_px = { width = 1020; height = 900; };
      blur_popups = false;
    }
    {
      match.app_id = "^dev\\.noctalia\\.UmbrielSharePicker$";
      default_floating = true;
      default_floating_size_px = { width = 800; height = 600; };
      default_position = { x = 32; y = 32; anchor = "bottom_right"; };
    }
    # Global blur (niri equivalent: window-rule global { background-effect
    # { blur true; xray false } }) — blur_ignore_alpha=0.0 approximates
    # "xray false" (no unblurred transparent area); verify visually.
    {
      blur = true;
      blur_ignore_alpha = 0.0;
    }
  ];

  layer_rule = [
    # From the official Umbriel/Noctalia example:
    # https://docs.noctalia.dev/umbriel/rules/#layer-rules
    {
      match.namespace = "^noctalia-(bar-[^\"]+|notification|dock|panel|attached-panel|osd|desktop-widget-[^\"]*)$";
      blur = true;
      blur_ignore_alpha = 0.5;
      blur_popups = true;
    }
    {
      match.namespace = "^noctalia-window-switcher$";
      blur = true;
      blur_ignore_alpha = 0.0;
    }
  ];
  };
}

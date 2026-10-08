{ lib, ... }:
{
  # ── Graphical session keyboard layout (XKB) ───────────────────
  # `console.keyMap` (see common.nix) only covers the TTY, BEFORE the
  # graphical session starts (niri/hyprland/mangowc/umbriel — GNOME and
  # KDE manage their own layout via their settings daemon, not via these
  # options). These two options drive the actual XKB layout used in the
  # Wayland session: the greeter (noctalia-greeter) + the compositor's
  # own input.
  options.roudix.keyboardLayout = lib.mkOption {
    type = lib.types.str;
    default = "us";
    example = "be";
    description = ''
      XKB layout code (setxkbmap) for the graphical session: "us", "be",
      "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp",
      etc. Independent of `console.keyMap` (which stays TTY-only).
    '';
  };

  options.roudix.keyboardVariant = lib.mkOption {
    type = lib.types.str;
    default = "intl";
    example = "";
    description = ''
      XKB variant associated with `roudix.keyboardLayout` (e.g. "intl",
      "nodeadkeys", "bepo", "dvorak", "colemak"...). Empty string for no
      variant (base layout).
    '';
  };

  options.roudix.keyboardOptions = lib.mkOption {
    type = lib.types.str;
    default = "";
    example = "caps:digits_row";
    description = ''
      XKB options (comma-separated, as in `setxkbmap -option`). Currently
      applied on Cinnamon only (LightDM + session).

      Handy one for AZERTY ("fr"/"be") layouts: "caps:digits_row" makes
      Caps Lock turn the top row into digits (no Shift needed), handy on
      laptops without a numpad. Downside: capital É/À/Ç can't be typed
      directly while it is on. Needs a recent xkeyboard-config.
    '';
  };
}

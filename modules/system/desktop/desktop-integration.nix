{ lib, ... }:
{
  # dconf is what GSettings-backed apps (GTK3/4, and Chromium-family
  # browsers like Helium/Brave/Chromium) read their theme/icon/cursor
  # choice from. Previously only enabled inside modules/system/desktop/
  # gnome.nix, so niri/hyprland/mangowc/umbriel got no GTK theming at all
  # for those apps (no dconf database → GSettings falls back to
  # upstream/Adwaita defaults regardless of what modules/home/theming/gtk-theme.nix
  # writes to ~/.config/gtk-3.0/settings.ini). mkDefault so gnome.nix's own
  # (identical) assignment, or a user override in home/local.nix or
  # hosts/*/local.nix, still wins without a "defined twice" conflict.
  config.programs.dconf.enable = lib.mkDefault true;

  options.roudix.desktopIntegration = lib.mkOption {
    type = lib.types.enum [ "gnome" "kde" ];
    default = "gnome";
    description = ''
      Keyring + xdg-desktop-portal stack used by "bare" compositors (niri,
      hyprland, mangowc, umbriel) that have no full DE providing their own
      stack natively. Has no effect when roudix.desktop.type is "gnome" or
      "kde": those DEs always keep their own native integration.

      "gnome"  → gnome-keyring + xdg-desktop-portal-gtk/-gnome (default).
      "kde"    → KWallet + xdg-desktop-portal-kde. Useful if you mostly use
                 Qt/KDE apps (Dolphin, etc.) on a compositor that's
                 neither GNOME nor KDE.

      ⚠ On compositors using greetd (the default, via noctalia-greeter),
      KWallet auto-unlock at login has a known nixpkgs limitation (the
      "greetd" PAM service doesn't substack "login" — nixpkgs#357201).
      Verify after a rebuild; if the wallet stays locked, see the
      comments in modules/system/desktop/*.nix for the workaround.
    '';
  };
}

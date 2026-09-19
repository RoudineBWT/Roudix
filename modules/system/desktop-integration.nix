{ lib, ... }:
{
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

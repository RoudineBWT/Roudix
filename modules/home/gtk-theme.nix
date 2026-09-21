{ lib, pkgs, osConfig, ... }:

let
  desktopType = osConfig.roudix.desktop.type;

  # GNOME (modules/home/gnome.nix) and KDE (modules/home/kde.nix) already
  # apply their own native theming (dconf for GNOME, plasma-manager for
  # KDE). This module only needs to fill the gap for the "bare" compositors
  # (niri, hyprland, mangowc, umbriel), which otherwise ship no GTK theme
  # at all — see the "not applied automatically" note in
  # papirus-icon.nix/tela-icon.nix.
  needsGtkTheme = desktopType != "gnome" && desktopType != "kde";

  # roudix.iconTheme (modules/system/icon-theme.nix), set via roudix-switcher
  # ("Icon Theme" page, same non-gnome/kde scope) or hosts/roudix/local.nix.
  iconThemeChoice = osConfig.roudix.iconTheme or "papirus";
  shellType       = osConfig.roudix.desktop.shell or "noctalia";

  # "tela" on shell = "noctalia" points at the recolored variant that
  # modules/home/tela-icon.nix generates in ~/.icons (package = null: it's
  # not a Nix-store package, just files on disk — first recolor happens on
  # the next Noctalia theme/accent change, not immediately on switch). Any
  # other shell has nothing to generate that variant, so it falls back to
  # plain Tela-dark from nixpkgs.
  iconThemes = {
    papirus  = { name = "Papirus-Dark"; package = pkgs.papirus-icon-theme; };
    tela =
      if shellType == "noctalia"
      then { name = "Tela-dark-noctalia"; package = null; }
      else { name = "Tela-dark"; package = pkgs.tela-icon-theme; };
    qogir    = { name = "Qogir-dark";    package = pkgs.qogir-icon-theme; };
    whitesur = { name = "WhiteSur-dark"; package = pkgs.whitesur-icon-theme; };
    colloid  = { name = "Colloid-dark";  package = pkgs.colloid-icon-theme; };
  };

  # Anything not in the curated set above is a name roudix-switcher's scan
  # found already on disk (nixpkgs package added by hand in
  # modules/home/local.nix, or dropped into ~/.icons) — just set the name,
  # no package to install. An unknown/mistyped name can't break a rebuild
  # this way: worst case it silently falls back to hicolor at runtime.
  chosenIcon = iconThemes.${iconThemeChoice} or { name = iconThemeChoice; package = null; };

  themeName  = "adw-gtk3-dark";
  cursorName = "capitaine-cursors-white";
  cursorSize = 24;
in
{
  config = lib.mkIf needsGtkTheme {
    # Writes ~/.config/gtk-3.0/settings.ini and gtk-4.0/settings.ini —
    # what most native GTK apps (and some Chromium builds) check directly.
    gtk = {
      enable = true;
      theme = {
        name    = themeName;
        package = pkgs.adw-gtk3;
      };
      iconTheme = {
        name    = chosenIcon.name;
        package = chosenIcon.package;
      };
      cursorTheme = {
        name    = cursorName;
        package = pkgs.capitaine-cursors;
        size    = cursorSize;
      };
    };

    home.pointerCursor = {
      name    = cursorName;
      package = pkgs.capitaine-cursors;
      size    = cursorSize;
      gtk.enable = true;
    };

    # Chromium-family browsers (Helium, Brave, Chromium itself) read the
    # theme via GSettings/dconf, not settings.ini — this is the piece that
    # was entirely missing outside GNOME. Requires
    # modules/system/desktop-integration.nix's
    # `programs.dconf.enable` to actually be on.
    dconf.settings."org/gnome/desktop/interface" = {
      color-scheme = "prefer-dark";
      gtk-theme    = themeName;
      icon-theme   = chosenIcon.name;
      cursor-theme = cursorName;
      cursor-size  = cursorSize;
    };

    # Belt-and-suspenders fallback: some Chromium builds (Helium included,
    # depending on how it's built) only ever check $GTK_THEME and ignore
    # GSettings on non-GNOME sessions.
    home.sessionVariables.GTK_THEME = themeName;
  };
}

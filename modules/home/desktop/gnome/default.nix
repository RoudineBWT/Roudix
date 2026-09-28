{ ... }:
{
  imports = [
    ../../theming/mangohud.nix
    ../../theming/papirus-folders.nix
    ./_extensions.nix
  ];

  # Nothing else here on purpose. GNOME's look & feel (wallpaper, theme,
  # icons, cursor, extension settings) is shipped as dconf *defaults* by
  # modules/system/desktop/gnome.nix. Setting it here through home-manager
  # (dconf.settings / home.pointerCursor) would re-apply it on every rebuild
  # and overwrite whatever the user chose in the meantime.
}

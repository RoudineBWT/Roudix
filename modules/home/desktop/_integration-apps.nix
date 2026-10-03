# Shared by niri / hyprland / mangowc / umbriel (home-manager side).
#
# Picks the GNOME or KDE flavour of the small "desktop apps" bundle based on
# roudix.desktopIntegration (modules/system/desktop/desktop-integration.nix).
#
# Swapped when integration = "kde":
#   gnome-text-editor   → kate
#   loupe               → gwenview
#   gnome-disk-utility  → KDE Partition Manager (installed system-wide through
#                         programs.partition-manager, see desktop-integration.nix,
#                         because kpmcore needs its D-Bus helper/polkit action)
#
# Deliberately KEPT in both modes (not GNOME-specific in practice):
#   adw-gtk3        — GTK3/4 apps (Discord, Helium, Steam, Spicetify...) are
#                     still themed with it by modules/home/theming/gtk-theme.nix
#   nwg-look        — GTK settings GUI
#   qt6ct / qt5ct   — QT_QPA_PLATFORMTHEME stays "qt6ct" so Noctalia/DMS keep
#                     theming Qt apps (Dolphin/Kate included)
#   gvfs            — GTK apps' trash/mounts/MTP still go through it
#   mission-center  — GTK4 but DE-agnostic task manager
{ pkgs, osConfig }:
let
  isKde = (osConfig.roudix.desktopIntegration or "gnome") == "kde";
in
{
  inherit isKde;

  desktopApps =
    if isKde then
      with pkgs.kdePackages; [ kate gwenview ]
    else
      with pkgs; [ gnome-text-editor gnome-disk-utility loupe ];

  # Used for the "spawn at startup" fallback when the shell isn't Noctalia
  # (the systemd user service in modules/system/desktop/*.nix is the primary).
  polkitAgentExe =
    if isKde
    then "${pkgs.kdePackages.polkit-kde-agent-1}/libexec/polkit-kde-authentication-agent-1"
    else "/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1";
}

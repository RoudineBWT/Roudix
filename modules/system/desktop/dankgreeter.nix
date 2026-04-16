{ config, pkgs, roudixBranding, username, ... }:
let
  desktopType = config.roudix.desktop.type;
  compositor  = if desktopType == "niri" then "niri" else "hyprland";
in
{
  services.displayManager.dms-greeter = {
    enable          = true;
    compositor.name = compositor;
  };

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.dms-greeter.enableGnomeKeyring = true;

  environment.etc."greetd/dms-greeter/session.json".text = builtins.toJSON {
    wallpaperPath     = "${roudixBranding}/share/backgrounds/roudix/roudix-dark.png";
    wallpaperFillMode = "PreserveAspectCrop";
  };
  systemd.tmpfiles.rules = [
    "d /var/cache/dms-greeter 0755 greeter greeter -"
  ];

  system.activationScripts.dms-greeter-sync = {
       text = ''
         HOME=/home/${username}
         if [ -d "$HOME/.config/DankMaterialShell" ]; then
           chgrp -R greeter $HOME/.config/DankMaterialShell
           chmod -R g+rX $HOME/.config/DankMaterialShell
         fi
         if [ -d "$HOME/.local/state/DankMaterialShell" ]; then
           chgrp -R greeter $HOME/.local/state/DankMaterialShell
           chmod -R g+rX $HOME/.local/state/DankMaterialShell
         fi
         if [ -d "$HOME/.cache/quickshell" ]; then
           chgrp -R greeter $HOME/.cache/quickshell
           chmod -R g+rX $HOME/.cache/quickshell
         fi
         ln -sf $HOME/.config/DankMaterialShell/settings.json /var/cache/dms-greeter/settings.json
         ln -sf $HOME/.local/state/DankMaterialShell/session.json /var/cache/dms-greeter/session.json
         ln -sf $HOME/.cache/quickshell/dankshell/dms-colors.json /var/cache/dms-greeter/colors.json
       '';
       deps = [ "users" ];
     };
}

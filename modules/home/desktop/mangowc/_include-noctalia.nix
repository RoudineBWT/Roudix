{ config, ... }:
{
  wayland.windowManager.mango.extraConfig = ''
    source-optional=${config.home.homeDirectory}/.config/mango/noctalia.conf
  '';
}

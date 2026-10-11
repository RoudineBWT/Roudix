{ config, ... }:
{
  wayland.windowManager.mango.extraConfig = ''
    source_optional=${config.home.homeDirectory}/.config/mango/noctalia.conf
  '';
}

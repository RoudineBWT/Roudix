{ config, pkgs, lib, ...}:

{programs.appimage.enable = true;
programs.appimage.binfmt = true;
}

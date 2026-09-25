{ ... }:
{
  # App-format/runtime support, not "apps" themselves.
  imports = [
    ./appimage.nix
    ./flatpak.nix
  ];
}

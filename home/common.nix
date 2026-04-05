{ pkgs, inputs, username, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  imports = [
    ../modules/fastfetch.nix
    ../modules/fish.nix
    ../modules/bash.nix
    ../modules/git.nix
    ../modules/ssh.nix
    ../modules/spicetify.nix
  ];

  home.packages = with pkgs; [
    # Common apps
    ghostty
    brave
    zed-editor
    btop
    ffmpeg
    nh
    nvd
    capitaine-cursors
  ];

  # ── Cursor ───────────────────────────────────────────────────────────────
  home.pointerCursor = {
    gtk.enable = true;
    x11.enable = true;
    package = pkgs.capitaine-cursors;
    name = "Capitaine Cursors White";
    size = 32;
  };

  programs.home-manager.enable = true;
}

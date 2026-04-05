{ pkgs, inputs, username, lib, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "25.11";

  imports = [
    ./common.nix
    ../modules/fastfetch.nix
    ../modules/gaming-home.nix
    ../modules/mangohud.nix
    ../modules/fish.nix
    ../modules/bash.nix
    ../modules/git.nix
    ../modules/ssh.nix
    ../modules/spicetify.nix
    ../modules/papirus-folders.nix
  ];

  # ── Packages ─────────────────────────────────────────────────────────────
  home.packages = with pkgs; [
    adw-gtk3
    clapper
    gnome-tweaks
    loupe

    # Flake packages
    inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default

    # GNOME Extensions
    gnomeExtensions.caffeine
    gnomeExtensions.gsconnect
    gnomeExtensions.appindicator
    gnomeExtensions.dash-to-dock
    gnomeExtensions.bing-wallpaper-changer
    gnomeExtensions.quick-settings-audio-panel
    gnomeExtensions.blur-my-shell
    gnomeExtensions.burn-my-windows
    gnomeExtensions.tiling-shell
    gnomeExtensions.vitals
    gnomeExtensions.rounded-window-corners-reborn
    gnomeExtensions.dash-to-panel
    gnomeExtensions.open-bar
    gnomeExtensions.arcmenu
    gnomeExtensions.bluetooth-battery-meter
  ];
  # Aliases
  programs.fish.shellAliases = lib.mkForce {
    rebuild = "nh os switch --accept-flake-config $NH_FLAKE#roudix-gnome";
    update = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config $NH_FLAKE#roudix-gnome";
  };

  programs.bash.shellAliases = lib.mkForce {
      rebuild = "nh os switch /home/${username}/.config/roudix#roudix-gnome";
      update = "sudo nix flake update --flake /home/${username}/.config/roudix && nh os switch /home/${username}/.config/roudix#roudix-gnome";
  };
}

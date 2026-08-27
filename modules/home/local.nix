{ pkgs, lib, config, osConfig, roudixSwitch, dotfiles, ... }:
{
  roudix.gitwatch = {
    enable = true;
    branch = "testing"; # ou "dev"
    repoPath = "${config.home.homeDirectory}/.config/roudix";
  };

  roudix.fastfetch.useNix = false;  # false = your fastfetch config in ~/.config/fastfetch

  programs.zen-browser.profiles.default.path = "gws77oal.Roudine";

 # ── Personal Home Manager overrides ─────────────────────────────────────
  # This file is gitignored and never touched by git pull.
  # Copy this file to home/local.nix and add your personal overrides here.

  # Examples:

  # Add personal packages
  # home.packages = with pkgs; [
  #   vlc
  #   telegram-desktop
  # ];

  # Override dotfiles source
  # xdg.configFile."hypr" = {
  #   source = "${dotfiles}/perso/hyprland";
  #   recursive = true;
  # };

  # Custom shell aliases
  # programs.fish.shellAliases = {
  #   myalias = "echo hello";
  # };

  # ── Niri user overrides ──────────────────────────────────────────────────
  # Included at the end of config.kdl — put your outputs, keybinds,
  # and any personal tweaks here. Overrides anything set by the dotfiles.
  # Only active when roudix.desktop.type = "niri".
  #
  # To get info for your monitors type on the terminal : niri msg outputs
  #
   xdg.configFile."niri/user.kdl" = lib.mkIf (osConfig.roudix.desktop.type == "niri") (lib.mkForce {
   text = ''
  // ── Outputs ─────────────────────────────────────────────────────────
     output "DP-1" {
       mode "2560x1440@240.000"
       position x=0 y=0
     }
     output "DP-3" {
       mode "1920x1080@165.000"
       position x=2560 y=0
     }
   '';
   });

  # ── Add personal packages ────────────────────────────────────────────────
   home.packages = with pkgs; [
  #   vlc
     telegram-desktop
     opencode-desktop
     qbittorrent
     tela-icon-theme
   ];

  # ── Custom shell aliases ─────────────────────────────────────────────────
  # programs.fish.shellAliases = {
  #   myalias = "echo hello";
  # };

  # ── Fastfetch ────────────────────────────────────────────────────────────

  # Override logo with a custom image (kitty terminal required)
  # programs.fastfetch.settings.logo = lib.mkForce {
  #   type = "kitty-direct";
  #   source = "${dotfiles}/perso/fastfetch/roudix-logo-tokyonight.png";
  #   padding = { top = 1; left = 3; };
  #   width = 38;
  # };

  # Override logo with a custom ASCII file
  # programs.fastfetch.settings.logo = lib.mkForce {
  #   type = "file";
  #   source = "${dotfiles}/perso/fastfetch/roudix-ascii.txt";
  #   padding = { top = 1; left = 3; };
  #   width = 38;
  # };

  # Override display color (ANSI color code)
  # programs.fastfetch.settings.display.color = "35"; # purple

  # Override entire fastfetch config (overwrites everything)
  # programs.fastfetch.settings = lib.mkForce {
  #   "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  #   logo = {
  #     type = "kitty-direct";
  #     source = "/home/youruser/Pictures/my-logo.png";
  #     padding = { top = 1; left = 3; };
  #     width = 38;
  #   };
  #   display = {
  #     separator = "  ";
  #     color = "33";
  #   };
  #   modules = [
  #     { type = "os"; key = "󱄅 OS"; keyColor = "33"; }
  #     { type = "kernel"; key = " Kernel"; keyColor = "33"; }
  #   ];
  # };

  # ── KDE overrides ────────────────────────────────────────────────────────

  # Override wallpaper
  # programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/my-wallpaper.jpg";

  # Override color scheme
  # programs.plasma.colorscheme = lib.mkForce "Catppuccin-Mocha";

  # Override Kickoff icon
  # programs.plasma.panels = lib.mkForce [{ ... }];

  # ── GNOME overrides ──────────────────────────────────────────────────────

  # Override light wallpaper
  # dconf.settings."org/gnome/desktop/background".picture-uri =
  #   lib.mkForce "file:///home/youruser/Pictures/my-wallpaper.png";

  # Override dark wallpaper
  # dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  #   lib.mkForce "file:///home/youruser/Pictures/my-wallpaper-dark.png";

  # Override screensaver wallpaper
  # dconf.settings."org/gnome/desktop/screensaver".picture-uri =
  #   lib.mkForce "file:///home/youruser/Pictures/my-wallpaper-dark.png";

  # Override light/dark mode
  # dconf.settings."org/gnome/desktop/interface".color-scheme =
  #   lib.mkForce "prefer-light"; # or "prefer-dark"

  # Override GTK theme
  # dconf.settings."org/gnome/desktop/interface".gtk-theme =
  #   lib.mkForce "adw-gtk3";

  # Override icon theme
  # dconf.settings."org/gnome/desktop/interface".icon-theme =
  #   lib.mkForce "Papirus";

  # Override cursor theme
  # dconf.settings."org/gnome/desktop/interface".cursor-theme =
  #   lib.mkForce "capitaine-cursors";
  # dconf.settings."org/gnome/desktop/interface".cursor-size =
  #   lib.mkForce 32;

  # Override system font
  # dconf.settings."org/gnome/desktop/interface".font-name =
  #   lib.mkForce "Inter 11";
}

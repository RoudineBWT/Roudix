{ pkgs, inputs, lib, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
  isDms      = shellType == "dms";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  # ⚠ Do NOT import `inputs.niri.homeModules.niri` here: it's already
  # imported automatically at the system level (the niri NixOS module
  # registers it for home-manager-as-module). Importing it a 2nd time here
  # triggers `error: The option 'programs.niri.finalConfig' ... is
  # already declared`.
  #
  # The _general/_animation/etc. files set programs.niri.settings.*
  # directly (no lib.mkIf inside), so they're only imported when niri is
  # the active compositor, to avoid touching niri settings on a host
  # using a different desktop.
  imports = [
    ../../mangohud.nix
    ../../papirus-icon.nix
    ../../tela-icon.nix
  ]
  ++ lib.optionals (osConfig.roudix.desktop.type == "niri") ([
    ./_general.nix
    ./_animation.nix
    ./_input.nix
    ./_layout.nix
    ./_output.nix
    ./_rules-common.nix
  ]
  ++ lib.optionals isNoctalia [
    ./_binds-noctalia.nix
    ./_rules-noctalia.nix
    ./_include-noctalia.nix
  ]
  ++ lib.optionals isDms [
    ./_binds-dms.nix
    ./_rules-dms.nix
    ./_include-dms.nix
  ]);

  config = lib.mkIf (osConfig.roudix.desktop.type == "niri") {

    # ── Noctalia (shell) ─────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    # ── Terminal / browser / files resolved from roudix.* ──────────
    # These binds are ALREADY defined by _binds-noctalia.nix / _binds-dms.nix;
    # since it's the same key (attrsOf, merges per bind), lib.mkForce is
    # needed for the value below to win — same principle as a local.nix
    # override.
    programs.niri.settings.binds = {
      "Mod+Return" = lib.mkForce {
        hotkey-overlay.title = "Open Terminal: ${terminalCmd}";
        action.spawn = [ terminalCmd ];
      };
      "Mod+E" = lib.mkForce {
        hotkey-overlay.title = "File Manager: ${fileManagerCmd}";
        action.spawn = [ fileManagerCmd ];
      };
    }
    // lib.optionalAttrs (browserCmd != null) {
      "Mod+B" = lib.mkForce {
        hotkey-overlay.title = "Open Browser: ${browserCmd}";
        action.spawn = [ browserCmd ];
      };
    }
    // (lib.listToAttrs (lib.imap1 (i: b: {
      name = "Mod+Ctrl+Alt+${toString i}";
      value = {
        hotkey-overlay.title = "Open Browser: ${b.name}";
        action.spawn = [ b.command ];
      };
    }) extraBrowsers));

    # ── Packages ─────────────────────────────────────────────────────────
    home.packages = with pkgs; [
      awww
      xwayland-satellite
      playerctl
      wl-clipboard
      pwvucontrol
      kdePackages.qtmultimedia
      mpvpaper

      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      gpu-screen-recorder

      nwg-look
      adw-gtk3
      papirus-icon-theme
      papirus-folders

      qt6Packages.qt6ct
      libsForQt5.qt5ct

      gvfs
      cava
    ]
    ++ lib.optionals isNoctalia [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}

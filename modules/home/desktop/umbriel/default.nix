{ lib, pkgs, inputs, osConfig, ... }:
let
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";

  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  imports = [
    inputs.umbriel.homeModules.default
    ../../mangohud.nix
    ../../papirus-icon.nix
    ../../tela-icon.nix
  ]
  # The _foo.nix files set programs.umbriel.settings.* directly (no
  # lib.mkIf), so they're only imported when umbriel is the active
  # compositor, to avoid touching umbriel settings on a host using a
  # different desktop. LISTS (window_rule/layer_rule) and the include
  # merge automatically across these files via the module system — no
  # manual merging needed here.
  ++ lib.optionals (osConfig.roudix.desktop.type == "umbriel") [
    ./_general.nix
    ./_appearance.nix
    ./_animation.nix
    ./_input.nix
    ./_layout.nix
    ./_output.nix
    ./_binds.nix
    ./_rules.nix
  ]
  ++ lib.optionals (osConfig.roudix.desktop.type == "umbriel" && isNoctalia) [
    ./_include-noctalia.nix
  ];

  config = lib.mkIf (osConfig.roudix.desktop.type == "umbriel") {

    # ── Noctalia (shell) ─────────────────────────────────────────────────
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    programs.umbriel = {
      enable = true;
    };

    # ── Terminal / browser / files resolved from roudix.* ──────────
    # Same key ("Mod+Return" etc.) as in _binds.nix: attrsOf merges per
    # bind, so lib.mkForce makes this value win (same principle as a
    # local.nix override).
    programs.umbriel.settings.keybinds = {
      "Mod+Return" = lib.mkForce "spawn:${terminalCmd}";
      "Mod+E" = lib.mkForce "spawn:${fileManagerCmd}";
    }
    // lib.optionalAttrs (browserCmd != null) {
      "Mod+B" = lib.mkForce "spawn:${browserCmd}";
    }
    // (lib.listToAttrs (lib.imap1 (i: b: {
      name = "Mod+Ctrl+Alt+${toString i}";
      value = "spawn:${b.command}";
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

      grim
      slurp

      gnome-text-editor
      gnome-disk-utility
      mission-center
      loupe
      clapper
      clapper-enhancers
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

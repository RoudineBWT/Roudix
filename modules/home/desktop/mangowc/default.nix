{ pkgs, inputs, config, lib, osConfig, ... }:
let
  isMango = osConfig.roudix.desktop.type == "mangowc";
  shellType = osConfig.roudix.desktop.shell or "noctalia";
  isNoctalia = shellType == "noctalia";
  isDms = shellType == "dms";
in
{
  imports = [
    inputs.mango.hmModules.mango
    ../../theming/mangohud.nix
    ../../theming/papirus-icon.nix
    ../../theming/tela-icon.nix
  ]
  ++ lib.optionals isMango [
    ./_general.nix
    ./_appearance.nix
    ./_animation.nix
    ./_layout.nix
    ./_output.nix
    ./_env.nix
    ./_binds-common.nix
    ./_rules-common.nix
    ./_rules-apps.nix
    ./_rules-gaming.nix
    ./_autostart.nix
  ]
  ++ lib.optionals (isMango && isNoctalia) [ ./_binds-noctalia.nix ]
  ++ lib.optionals (isMango && isDms) [ ./_binds-dms.nix ];

  config = lib.mkIf isMango {
    programs.noctalia = lib.mkIf isNoctalia {
      enable = true;
      package = null;
    };

    wayland.windowManager.mango = {
      enable = true;
      package = inputs.mango.packages.${pkgs.stdenv.hostPlatform.system}.mango;

      systemd = {
        enable = true;
        variables = [
          "DISPLAY"
          "WAYLAND_DISPLAY"
          "XDG_CURRENT_DESKTOP"
          "XDG_SESSION_TYPE"
          "NIXOS_OZONE_WL"
          "XCURSOR_THEME"
          "XCURSOR_SIZE"
        ];
      };

      # DMS writes these files dynamically. Keep them real, writable files
      # while the rest of Mango remains declarative in Nix.
      extraConfig = lib.optionalString isDms ''
        source=~/.config/mango/dms/colors.conf
        source=~/.config/mango/dms/layout.conf
        source=~/.config/mango/dms/outputs.conf
      '';

      autostart_sh = "";
    };

    home.activation.mangoDmsFiles = lib.mkIf isDms (lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "$HOME/.config/mango/dms"
      touch "$HOME/.config/mango/dms/colors.conf"
      touch "$HOME/.config/mango/dms/layout.conf"
      touch "$HOME/.config/mango/dms/outputs.conf"
    '');

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
    ] ++ lib.optionals isNoctalia [
      inputs.noctalia.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}

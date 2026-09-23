{ config, lib, pkgs, inputs, username, ... }:
let
  isUmbriel  = config.roudix.desktop.type == "umbriel";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
in
{
  imports = [ inputs.umbriel.nixosModules.default ];

  # ── User-facing options ────────────────────────────────────────────────
  options.roudix.umbriel = {
    scratchpadApps = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Umbriel only. When true, chat apps (Discord/Telegram) and Spotify
        live in named scratchpads (hidden by default, shown/hidden with a
        shortcut, can be sent back in) instead of being pinned to a fixed
        output/workspace/position. When false (default), they stay tiled
        exactly as before — set this in local.nix if you want the
        scratchpad workflow instead.
      '';
    };
  };

  config = lib.mkIf isUmbriel {
    # ── Compositor ────────────────────────────────────────────────────
    # inputs.umbriel = { url = "github:noctalia-dev/umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    # inputs.umbriel-portal = { url = "github:noctalia-dev/xdg-desktop-portal-umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    nixpkgs.overlays = [
      inputs.umbriel.overlays.default
    ];

    programs.umbriel.enable = true;
    # programs.umbriel.package already defaults to
    # inputs.umbriel.packages.${system}.default via the module.
    #
    # Umbriel's README documents a dedicated portal option: it configures
    # xdg.portal AND installs the ScreenCast/Screenshot config on its own
    # (instead of doing it by hand via xdg.portal.config.umbriel below).
    programs.umbriel.portalPackage =
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default;

    # ── DMS greeter (when shell != noctalia) ───────────────────────────────
    programs.dms-greeter = lib.mkIf (!isNoctalia) {
      enable = true;
      compositor.name = "umbriel";
      configHome = "/home/${username}";
    };

    # ── DMS (shell) ─────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
    };

    # ── Noctalia greeter (when shell == noctalia) ──────────────────────────
    services.displayManager.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "start-umbriel";
      settings = {
        keyboard = {
          layout  = config.roudix.keyboardLayout;
          variant = config.roudix.keyboardVariant;
        };
      };
    };

    # ── Portals ──────────────────────────────────────────────────────────
    # The umbriel backend + its config (ScreenCast/Screenshot) are now
    # wired by programs.umbriel.portalPackage above. This only keeps the
    # fallback portals for GTK/GNOME file pickers.
    # ⚠ Not thoroughly tested — verify in a real session that portalPackage
    # is sufficient and doesn't conflict with gtk/gnome for the default
    # portal. Docs: https://github.com/noctalia-dev/xdg-desktop-portal-umbriel
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs;
        if isKdeIntegration
        then [ kdePackages.xdg-desktop-portal-kde ]
        else [ xdg-desktop-portal-gtk xdg-desktop-portal-gnome ];
    };

    # ── Polkit ────────────────────────────────────────────────────────────
    systemd.user.services.polkit-agent = {
      description =
        if isKdeIntegration
        then "KDE Polkit authentication agent"
        else "GNOME Polkit authentication agent";
      wantedBy = [ "graphical-session.target" ];
      after    = [ "graphical-session.target" ];
      partOf   = [ "graphical-session.target" ];
      serviceConfig = {
        Type       = "simple";
        ExecStart  =
          if isKdeIntegration
          then "${pkgs.kdePackages.polkit-kde-agent-1}/libexec/polkit-kde-authentication-agent-1"
          else "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart    = "on-failure";
        RestartSec = "1s";
      };
    };

    # ── Keyring ───────────────────────────────────────────────────────────
    # ⚠ kde branch not tested in a real session. Known caveat: the
    # "greetd" PAM service doesn't substack "login" (nixpkgs#357201),
    # which has already broken kwallet auto-unlock for other greetd users
    # — see discourse.nixos.org "Auto-Unlock kwallet with greetd
    # login-manager". If the wallet stays locked after login, greetd's PAM
    # text will likely need "login" substacked by hand (as gdm.nix/
    # lightdm.nix already do for this case).
    services.gnome.gnome-keyring.enable = !isKdeIntegration;
    security.pam.services.greetd.enableGnomeKeyring = !isKdeIntegration;
    security.pam.services.greetd.kwallet.enable = isKdeIntegration;

    environment.systemPackages = with pkgs;
      lib.optional (!isKdeIntegration) polkit_gnome
      ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
  };
}

{ config, lib, pkgs, ... }:
let
  isMango     = config.roudix.desktop.type == "mangowc";
  shellType   = config.roudix.desktop.shell or "noctalia";
  isDms       = shellType == "dms";
  isNoctalia  = shellType == "noctalia";
  needsPolkit = !isDms;
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
in
{
  imports = [ ./ly.nix ];

  config = lib.mkIf isMango {
    programs.mango = {
          enable = true;
        };

        xdg.portal = {
          enable = true;
          wlr.enable = true;
          extraPortals = with pkgs;
            [ (if isKdeIntegration then kdePackages.xdg-desktop-portal-kde else xdg-desktop-portal-gtk) ];
          config.common.default = "wlr";
          # Explicitly set screencast to wlr to avoid gtk taking over
          config.common."org.freedesktop.impl.portal.ScreenCast" = "wlr";

          # xdg-desktop-portal-wlr.service runs with a minimal PATH
          # (coreutils only, via its own overrides.conf), so it never
          # finds slurp/rofi/etc installed in the home-manager profile.
          # An absolute path is required for the chooser to work.
          wlr.settings.screencast = {
            chooser_type = "simple";
            chooser_cmd  = "${pkgs.slurp}/bin/slurp -f 'Monitor: %o' -or";
          };
        };

    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
    };

    # ── Noctalia greeter (replaces ly when shell == noctalia) ────────────
    programs.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "--session mangowc";
      settings = {
        keyboard = {
          layout  = config.roudix.keyboardLayout;
          variant = config.roudix.keyboardVariant;
        };
      };
    };

    systemd.user.services.polkit-agent = lib.mkIf needsPolkit {
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

    # ⚠ kde branch not tested in a real session. The "ly" sub-case (shell
    # != noctalia) should be reliable — ly is a classic display manager.
    # The "greetd" sub-case (shell == noctalia) has a known caveat: the
    # "greetd" PAM service doesn't substack "login" (nixpkgs#357201),
    # which has already broken kwallet auto-unlock for other greetd users
    # — see discourse.nixos.org "Auto-Unlock kwallet with greetd
    # login-manager". Verify after a rebuild.
    services.gnome.gnome-keyring.enable = !isKdeIntegration;
    services.dbus.enable = true;
    security.pam.services.ly.enableGnomeKeyring     = lib.mkIf (!isNoctalia && !isKdeIntegration) true;
    security.pam.services.greetd.enableGnomeKeyring = lib.mkIf (isNoctalia && !isKdeIntegration) true;
    security.pam.services.ly.kwallet.enable          = lib.mkIf (!isNoctalia && isKdeIntegration) true;
    security.pam.services.greetd.kwallet.enable      = lib.mkIf (isNoctalia && isKdeIntegration) true;

    environment.systemPackages = lib.optionals needsPolkit [
      (if isKdeIntegration then pkgs.kdePackages.polkit-kde-agent-1 else pkgs.polkit_gnome)
    ];
  };
}

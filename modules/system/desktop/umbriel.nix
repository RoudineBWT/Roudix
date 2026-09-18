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
    # ── Compositeur ────────────────────────────────────────────────────
    # inputs.umbriel = { url = "github:noctalia-dev/umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    # inputs.umbriel-portal = { url = "github:noctalia-dev/xdg-desktop-portal-umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    nixpkgs.overlays = [
      inputs.umbriel.overlays.default
    ];

    programs.umbriel.enable = true;
    # programs.umbriel.package est déjà réglé par défaut par le module sur
    # inputs.umbriel.packages.${system}.default
    #
    # Le README d'Umbriel documente une option dédiée pour le portail :
    # elle configure xdg.portal ET installe la conf nécessaire au
    # ScreenCast/Screenshot toute seule (au lieu de le faire à la main
    # via xdg.portal.config.umbriel plus bas).
    programs.umbriel.portalPackage =
      inputs.xdg-desktop-portal-umbriel.packages.${pkgs.stdenv.hostPlatform.system}.default;

    # ── Greeter DMS (si shell != noctalia) ───────────────────────────────
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

    # ── Greeter Noctalia (si shell == noctalia) ──────────────────────────
    programs.noctalia-greeter = lib.mkIf isNoctalia {
      enable = true;
      greeter-args = "start-umbriel";
      settings = {
        keyboard = {
          layout  = config.roudix.keyboardLayout;
          variant = config.roudix.keyboardVariant;
        };
      };
    };

    # ── Portails ──────────────────────────────────────────────────────────
    # Le backend umbriel + sa conf (ScreenCast/Screenshot) sont maintenant
    # câblés par programs.umbriel.portalPackage ci-dessus. Ici on ne garde
    # que les portails de secours pour les file pickers GTK/GNOME.
    # ⚠ Pas testé en profondeur — à vérifier une fois en session que
    # portalPackage suffit bien et qu'il n'entre pas en conflit avec gtk/
    # gnome pour le default portal. Doc: https://github.com/noctalia-dev/xdg-desktop-portal-umbriel
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
    # ⚠ Branche kde pas testée en session réelle. Point de vigilance connu :
    # le service PAM "greetd" ne substack pas "login" (nixpkgs#357201), ce
    # qui a déjà cassé l'auto-unlock kwallet pour d'autres utilisateurs de
    # greetd — cf. discourse.nixos.org "Auto-Unlock kwallet with greetd
    # login-manager". Si le wallet reste verrouillé après un login, il
    # faudra probablement substack "login" à la main dans le texte PAM de
    # greetd (comme le font déjà gdm.nix/lightdm.nix pour ce cas).
    services.gnome.gnome-keyring.enable = !isKdeIntegration;
    security.pam.services.greetd.enableGnomeKeyring = !isKdeIntegration;
    security.pam.services.greetd.kwallet.enable = isKdeIntegration;

    environment.systemPackages = with pkgs;
      lib.optional (!isKdeIntegration) polkit_gnome
      ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
  };
}

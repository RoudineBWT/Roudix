{ config, lib, pkgs, inputs, username, ... }:
let
  isHyprland  = config.roudix.desktop.type == "hyprland";
  shellType   = config.roudix.desktop.shell or "noctalia";
  needsPolkit = shellType != "dms";
  isDms       = shellType == "dms";
  isNoctalia  = shellType == "noctalia";
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
in
{
config = lib.mkIf isHyprland {

  # ── Greeter DMS (si shell == dms ou caelestia, donc !isNoctalia) ─────────
  programs.dms-greeter = lib.mkIf (!isNoctalia) {
    enable = true;
    compositor.name = "hyprland";
    configHome = "/home/${username}";
  };

  # ── DMS (shell) ─────────────────────────────────────────────────────────
  programs.dank-material-shell = lib.mkIf isDms {
    enable = true;
    systemd.enable = true;
  };

  # ── Greeter Noctalia (si shell == noctalia) ──────────────────────────────
  programs.noctalia-greeter = lib.mkIf isNoctalia {
    enable = true;
    # "hyprland" tout court bypass UWSM (pas de graphical-session.target
    # atteint → xdg-desktop-portal.service échoue en dépendance). Il faut
    # la session générée par withUWSM = true : hyprland-uwsm.desktop.
    greeter-args = "--session hyprland-uwsm";
    settings = {
      keyboard = {
        layout  = "us";
        variant = "intl";
      };
    };
  };

  programs.hyprland = {
    enable = true;
    withUWSM = true;
    xwayland.enable = true;
  };

  programs.uwsm.enable = true;

  xdg.portal = {
    enable = true;
    # xdg-desktop-portal-hyprland reste toujours prioritaire (ScreenCast) —
    # seul le portail "de secours" (file pickers, etc.) suit
    # roudix.desktopIntegration.
    extraPortals = with pkgs;
      [ xdg-desktop-portal-hyprland ]
      ++ (if isKdeIntegration then [ kdePackages.xdg-desktop-portal-kde ] else [ xdg-desktop-portal-gtk ]);
    # "*" laisse l'arbitrage D-Bus décider tout seul entre hyprland/gtk pour
    # chaque interface — non-déterministe, ça peut casser au hasard d'une
    # update (cf. discourse.nixos.org, fil "Portals don't work on Hyprland
    # after update to 0.55.2"). On fixe explicitement l'ordre de priorité,
    # comme recommandé par le wiki Hyprland (hyprland;gtk), et on épingle
    # ScreenCast pour être sûr que ça reste hyprland même si gtk/kde changeait
    # d'ordre d'enregistrement.
    config.common = {
      default = [ "hyprland" (if isKdeIntegration then "kde" else "gtk") ];
      "org.freedesktop.impl.portal.ScreenCast" = [ "hyprland" ];
    };
  };

  # ── Polkit agent ────────────────────────────────────────────────────────
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

  programs.nautilus-open-any-terminal = {
    enable = true;
    terminal = "ghostty";
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


  environment.systemPackages = with pkgs; [
    awww
    grimblast
    playerctl
  ]
  ++ lib.optionals needsPolkit [ hyprpolkitagent ]
  ++ lib.optional (!isKdeIntegration) polkit_gnome
  ++ lib.optional isKdeIntegration kdePackages.polkit-kde-agent-1;
 };
}

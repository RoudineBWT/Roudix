{ config, lib, pkgs, inputs, username, ... }:
let
  isUmbriel  = config.roudix.desktop.type == "umbriel";
  shellType  = config.roudix.desktop.shell or "noctalia";
  isDms      = shellType == "dms";
  isNoctalia = shellType == "noctalia";
  isKdeIntegration = config.roudix.desktopIntegration == "kde";
  dp = import ../../desktop-pkgs.nix {
    inherit pkgs inputs;
    latest = config.roudix.desktop.latest;
  };
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

    effects = lib.mkOption {
      type = lib.types.enum [ "roudix" "roudix-plus" "roudix-plus-mocha" "roudix-vine" "roudix-vine-mocha" "roudix-wobbly" "roudix-wobbly-mocha" "roudix-logo" "roudix-logo-wobbly" "roudix-orbit" "roudix-orbit-mocha" "roudix-full" "sakura-overdrive" "sakura-roudix" ];
      default = "roudix";
      description = ''
        Umbriel only. Shader/animation setup:
          "roudix"           : subtle window in/out + scratchpad shaders (default).
          "roudix-plus"      : "roudix" + accent border, cursor halo and subtle
                               workspace/layer/focus transitions (original
                               shaders, light on the GPU). Follows the
                               Noctalia palette.
          "roudix-plus-mocha": same as "roudix-plus" with Catppuccin Mocha +
                               Peach colors (fixed, independent of Noctalia).
          "roudix-vine"      : "roudix-plus" + Sakura-style woven vine border where
                               flowers are the Roudix logo and leaves its chevron.
                               Follows the Noctalia palette.
          "roudix-vine-mocha": same with Catppuccin Mocha + Peach colors.
          "roudix-wobbly"    : "roudix-plus" + light jelly wobble on window
                               move/re-tile + spring physics while dragging.
          "roudix-wobbly-mocha": same with Catppuccin Mocha + Peach colors.
          "roudix-logo"      : "roudix-plus" + windows open/close through the
                               Roudix logo shape (Mocha Peach/Maroon, fixed).
          "roudix-logo-wobbly": same + jelly wobble on move + drag physics.
          "roudix-orbit"     : "roudix-plus" with a "snowflake braid" border (two
                               interlaced strands, glints, comet + flare, inner
                               glow, light spill) + focus sweep.
          "roudix-orbit-mocha": same with Catppuccin Mocha + Peach colors.
          "roudix-full"      : everything — logo open/close, jelly wobble, logo
                               vine border (Mocha Peach/Maroon, fixed).
          "sakura-overdrive" : Ly-sec's full sakura/magical-girl suite — animated
                               border, screen and cursor effects and shader
                               animations on every event. Colors come from the
                               Noctalia palette, so use it with the Noctalia shell.
          "sakura-roudix"    : the same suite with Catppuccin Mocha + Peach colors
                               (fixed, independent of the wallpaper/Noctalia).
      '';
    };
  };

  config = lib.mkIf isUmbriel {
    # ── Compositor ────────────────────────────────────────────────────
    # inputs.umbriel = { url = "github:noctalia-dev/umbriel"; inputs.nixpkgs.follows = "nixpkgs"; };
    # The flake overlay + the module's own default package (flake build).
    nixpkgs.overlays = [ inputs.umbriel.overlays.default ];

    programs.umbriel.enable = true;
    #
    # The portal (xdg-desktop-portal-umbriel) now ships with Umbriel's own
    # NixOS module: programs.umbriel.portalPackage defaults to the portal
    # flake pinned by the umbriel input, and the module configures xdg.portal
    # and the ScreenCast/Screenshot config by itself. Nothing to set here (and
    # no separate flake input) — it always matches the umbriel revision in
    # flake.lock. Override programs.umbriel.portalPackage only to pin another.

    # ── DMS (shell) ─────────────────────────────────────────────────────
    programs.dank-material-shell = lib.mkIf isDms {
      enable = true;
      systemd.enable = true;
    };

    # ── Greeter ──────────────────────────────────────────────────────────
    # dms-greeter's compositor.name enum (niri, hyprland, sway, labwc, mango,
    # scroll, miracle, aqueous) has no "umbriel", so the DMS greeter can't be
    # used here. noctalia-greeter is a generic greetd greeter: use it for every
    # shell. It only understands `--session NAME` (.desktop Name= or filename);
    # check the exact name with `noctalia-greeter sessions`.
    services.displayManager.noctalia-greeter = {
      enable = true;
      greeter-args = "--session Umbriel";
      settings = {
        keyboard = {
          layout  = config.roudix.keyboardLayout;
          variant = config.roudix.keyboardVariant;
        };
      };
    };

    # ── Portals ──────────────────────────────────────────────────────────
    # The umbriel backend + its config (ScreenCast/Screenshot) are wired by
    # Umbriel's own module (see above). This only keeps the fallback portals
    # for GTK/GNOME file pickers.
    # ⚠ Not thoroughly tested — verify in a real session that the module's
    # portal is sufficient and doesn't conflict with gtk/gnome for the
    # default portal. Docs: https://github.com/noctalia-dev/xdg-desktop-portal-umbriel
    xdg.portal = {
      enable = true;
      extraPortals = with pkgs;
        if isKdeIntegration
        then [ kdePackages.xdg-desktop-portal-kde xdg-desktop-portal-gtk ]
        else [ xdg-desktop-portal-gtk xdg-desktop-portal-gnome ];
      # programs.umbriel.portalPackage only sets default = [ umbriel gtk ]
      # (mkDefault). In kde mode, the fallback is kde and FileChooser is
      # pinned to it explicitly.
      config.umbriel = lib.mkIf isKdeIntegration {
        default = [ "umbriel" "kde" ];
        "org.freedesktop.impl.portal.FileChooser" = [ "kde" ];
        # gtk portal only for Settings: dark/light follows dconf
        # (color-scheme) instead of the KDE portal's kdeglobals (= light).
        "org.freedesktop.impl.portal.Settings" = [ "gtk" ];
      };
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

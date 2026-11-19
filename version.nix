{ lib, config, pkgs, ... }:

with lib;
let
  DISTRO_NAME = "Roudix";
  DISTRO_ID   = "roudix";

  # ── Édition affichée selon le desktop choisi (roudix.desktop.type) ──────
  # Pas de numéro de version dans le nom visible : nixos-unstable est une
  # rolling release, le numéro ne veut rien dire. VERSION_ID / BUILD_ID
  # restent dans os-release comme métadonnées (invisibles pour l'utilisateur).
  editions = {
    niri     = "Niri";
    gnome    = "GNOME";
    kde      = "KDE Plasma";
    cinnamon = "Cinnamon";
    cosmic   = "COSMIC";
    hyprland = "Hyprland";
    mangowc  = "MangoWC";
    umbriel  = "Umbriel";
  };
  de        = config.roudix.desktop.type;
  edition   = editions.${de} or de;          # repli : le nom brut du desktop
  variant   = "${edition} Edition";
  prettyName = "${DISTRO_NAME} ${variant}";  # ex. "Roudix GNOME Edition"

  cfg = config.system.nixos;
  needsEscaping = s: null != builtins.match "[a-zA-Z0-9]+" s;
  escapeIfNeccessary = s: if needsEscaping s then s else ''"${escape [ "\$" "\"" "\\" "\`" ] s}"'';
  attrsToText =
    attrs:
    concatStringsSep "\n" (mapAttrsToList (n: v: ''${n}=${escapeIfNeccessary (toString v)}'') attrs)
    + "\n";

  osReleaseContents = {
    NAME              = DISTRO_NAME;
    ID                = DISTRO_ID;
    ID_LIKE           = "nixos";
    VERSION           = "${cfg.release} (${cfg.codeName})";
    VERSION_CODENAME  = cfg.codeName;
    VERSION_ID        = cfg.release;
    BUILD_ID          = cfg.version;
    VARIANT           = variant;
    VARIANT_ID        = de;
    PRETTY_NAME       = prettyName;
    LOGO              = "roudix-logo";
    DOCUMENTATION_URL = "";
    SUPPORT_URL       = "";
    BUG_REPORT_URL    = "";
  };

  initrdReleaseContents = osReleaseContents // {
    PRETTY_NAME = "${osReleaseContents.PRETTY_NAME} (Initrd)";
  };
  initrdRelease = pkgs.writeText "initrd-release" (attrsToText initrdReleaseContents);
in
{
  options.roudix.version.enable = mkOption {
    description = "Enable Roudix version configurations.";
    type        = types.bool;
    default     = true;
  };

  config = mkIf config.roudix.version.enable {
    environment.etc."os-release".text  = mkForce (attrsToText osReleaseContents);
    environment.etc."lsb-release".text = mkForce (attrsToText {
      LSB_VERSION         = "${cfg.release} (${cfg.codeName})";
      DISTRIB_ID          = DISTRO_ID;
      DISTRIB_RELEASE     = cfg.release;
      DISTRIB_CODENAME    = toLower cfg.codeName;
      DISTRIB_DESCRIPTION = prettyName;
    });
    boot.initrd.systemd.contents."/etc/os-release".source     = mkForce initrdRelease;
    boot.initrd.systemd.contents."/etc/initrd-release".source = mkForce initrdRelease;
    system.nixos.distroName = DISTRO_NAME;
    system.nixos.distroId   = DISTRO_ID;
  };
}

{ lib, config, pkgs, ... }:

with lib;
let
  DISTRO_NAME = "Roudix";
  DISTRO_ID   = "roudix";

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
    PRETTY_NAME       = "${DISTRO_NAME} ${cfg.version}";
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
      DISTRIB_DESCRIPTION = "${DISTRO_NAME} ${cfg.release} (${cfg.codeName})";
    });
    boot.initrd.systemd.contents."/etc/os-release".source     = mkForce initrdRelease;
    boot.initrd.systemd.contents."/etc/initrd-release".source = mkForce initrdRelease;
    system.nixos.distroName = DISTRO_NAME;
    system.nixos.distroId   = DISTRO_ID;
  };
}

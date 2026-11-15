{ config, lib, ... }:
let
  cfg = config.roudix.security.mitigations;
  forced = m: builtins.elem m config.boot.kernelModules;
in
{
  options.roudix.security.mitigations = {
    enable = lib.mkOption {
      description = "Kernel CVE mitigations by blacklisting rarely used vulnerable modules (recommended).";
      type = lib.types.bool;
      default = true;
    };

    blacklistDirtyFrag = lib.mkOption {
      description = ''
        Blacklist the modules hit by "Dirty Frag" (esp4/esp6 and rxrpc).
        Turn off ONLY if you use IPsec (strongSwan, libreswan, ...) or
        AFS/Kerberos over rxrpc.
      '';
      type = lib.types.bool;
      default = true;
    };

    blacklistCopyFail = lib.mkOption {
      description = ''
        Blacklist algif_aead (AF_ALG AEAD socket API) as defense in depth
        against "Copy Fail". Applications use libcrypto directly, not this API.
      '';
      type = lib.types.bool;
      default = true;
    };
  };

  config = lib.mkIf cfg.enable {
    boot.blacklistedKernelModules =
      lib.optionals cfg.blacklistDirtyFrag [ "esp4" "esp6" "rxrpc" ]
      ++ lib.optional cfg.blacklistCopyFail "algif_aead";

    # Deliberately NOT setting user.max_user_namespaces=0: it would break
    # Flatpak, browser sandboxes, the Steam runtime and bubblewrap.

    assertions = [
      {
        assertion = cfg.blacklistDirtyFrag -> !(forced "esp4" || forced "esp6" || forced "rxrpc");
        message = ''
          roudix.security.mitigations.blacklistDirtyFrag is on, but esp4/esp6/rxrpc
          is forced through boot.kernelModules. Turn blacklistDirtyFrag off if you need it.
        '';
      }
      {
        assertion = cfg.blacklistCopyFail -> !(forced "algif_aead");
        message = ''
          roudix.security.mitigations.blacklistCopyFail is on, but algif_aead is
          forced through boot.kernelModules. Turn blacklistCopyFail off if you need it.
        '';
      }
    ];
  };
}

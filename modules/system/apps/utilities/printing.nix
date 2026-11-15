{ config, lib, pkgs, username, ... }:
{
  options.roudix.printing.scanners.enable = lib.mkOption {
    description = ''
      Scanner support (SANE): network scanners through sane-airscan (eSCL /
      AirScan, driverless), HP scanners through HPLIP, and the `scanner` group
      for the primary user. Independent from printing: a standalone scanner
      works without CUPS. Brother (brscan4/5) and Epson legacy backends are
      not included — add them to hardware.sane.extraBackends in local.nix.
    '';
    type = lib.types.bool;
    default = false;
  };

  options.roudix.printing.enable = lib.mkOption {
    description = ''
      Printing support: CUPS with the common free drivers (Gutenprint, HPLIP,
      Brother brlaser, foomatic), plus Avahi/mDNS so network printers are
      found by themselves, and system-config-printer for setups whose
      desktop has no printer settings (bare compositors). Off by default:
      it starts the CUPS service and opens the mDNS port (UDP 5353).
    '';
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkMerge [
    (lib.mkIf config.roudix.printing.enable {
      services.printing = {
        enable = true;
        drivers = with pkgs; [
          brlaser
          foomatic-db
          foomatic-db-engine
          gutenprint
          hplip
        ];
      };

      services.avahi = {
        enable = true;
        nssmdns4 = true;
        openFirewall = true; # UDP 5353: network printers answer here
        wideArea = false;    # CVE-2024-52615
      };

      environment.systemPackages = [ pkgs.system-config-printer ];
    })

    (lib.mkIf config.roudix.printing.scanners.enable {
      hardware.sane = {
        enable = true;
        extraBackends = [ pkgs.sane-airscan pkgs.hplip ];
      };
      users.users.${username}.extraGroups = [ "scanner" "lp" ];
    })
  ];
}

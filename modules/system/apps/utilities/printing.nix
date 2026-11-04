{ config, lib, pkgs, ... }:
{
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

  config = lib.mkIf config.roudix.printing.enable {
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
  };
}

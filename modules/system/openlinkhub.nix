{ config, pkgs, lib, inputs, ... }:

let
  openlinkhub-bin = inputs.roudix-caches.packages.x86_64-linux.openlinkhub;
in {
  # Règles udev pour que le service ait accès aux USB Corsair
  services.udev.extraRules = ''
    SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", MODE="0660", GROUP="openlinkhub"
  '';

  # Groupe dédié
  users.groups.openlinkhub = {};

  # Service systemd
  systemd.services.openlinkhub = {
    description = "OpenLinkHub";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];
    serviceConfig = {
      ExecStartPre = "${openlinkhub-bin}/lib/systemd/openlinkhub-setup";
      ExecStart    = "${openlinkhub-bin}/bin/OpenLinkHub";
      Restart      = "on-failure";
      WorkingDirectory = "/var/lib/openlinkhub";
      StateDirectory   = "openlinkhub";
    };
  };
}

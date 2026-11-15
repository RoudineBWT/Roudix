{ config, lib, pkgs, ... }:
{
  # NetworkManager already handles WireGuard natively; OpenVPN needs a plugin.
  options.roudix.vpn.openvpn.enable = lib.mkOption {
    description = "Add the NetworkManager OpenVPN plugin, to import .ovpn files in the network settings.";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkIf config.roudix.vpn.openvpn.enable {
    networking.networkmanager.plugins = [ pkgs.networkmanager-openvpn ];
  };
}

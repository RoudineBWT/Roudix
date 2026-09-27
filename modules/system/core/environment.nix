{ config, lib, pkgs, username, roudixSwitcher, ... }:
{
  environment.etc."polkit-1/actions/io.roudix.switcher.policy".source =
    "${roudixSwitcher}/share/polkit-1/actions/io.roudix.switcher.policy";
}

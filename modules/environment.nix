{config, lib, pkgs, username, ...}:

{
  environment.etc."polkit-1/actions/io.roudix.switcher.policy" = {
  source = ../pkgs/roudix-switcher/io.roudix.switcher.policy;
};
}

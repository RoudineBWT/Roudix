{ config, pkgs, lib, username, ... }:
{
  options.roudix.podman.enable = lib.mkOption {
    description = "Enable Podman (rootless, Docker-CLI-compatible container engine)";
    type = lib.types.bool;
    default = false;
  };

  options.roudix.distrobox.enable = lib.mkOption {
    description = "Enable Distrobox (run any Linux distro in a container, integrated with the host)";
    type = lib.types.bool;
    default = false;
  };

  config = lib.mkMerge [
    (lib.mkIf config.roudix.podman.enable {
      virtualisation.podman = {
        enable = true;
        dockerCompat = true;
        defaultNetwork.settings.dns_enabled = true;
      };
    })

    # Distrobox needs a container backend. If roudix.podman.enable wasn't
    # separately turned on, still enable Podman under the hood (mkDefault
    # so an explicit roudix.podman.enable = false; from the user wins).
    (lib.mkIf config.roudix.distrobox.enable {
      environment.systemPackages = [ pkgs.distrobox ];
      virtualisation.podman.enable = lib.mkDefault true;
    })
  ];
}

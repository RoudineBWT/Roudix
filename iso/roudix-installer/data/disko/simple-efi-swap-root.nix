## Reference layout — what disko_gen.py produces for "mode: simple",
## filesystem: ext4, swap disabled (zram covers that role by default).
{
  disko.devices = {
    disk = {
      main = {
        type = "disk";
        device = "/dev/nvme0n1"; # overwritten at install time
        content = {
          type = "gpt";
          partitions = {
            ESP = {
              size = "4G"; # CachyOS kernels + plusieurs générations Limine remplissent vite un /boot de 512M
              type = "EF00";
              content = {
                type = "filesystem";
                format = "vfat";
                mountpoint = "/boot";
                mountOptions = [ "umask=0077" ];
              };
            };
            root = {
              size = "100%";
              content = {
                type = "filesystem";
                format = "ext4";
                mountpoint = "/";
              };
            };
          };
        };
      };
    };
  };
}

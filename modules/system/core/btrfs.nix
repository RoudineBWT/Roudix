{ config, lib, pkgs, ... }:
let
  cfg = config.roudix.btrfs;

  # One mount point per btrfs filesystem (several subvolumes of the same
  # device share one scrub: services.btrfs.autoScrub would otherwise scrub
  # the same device once per mounted subvolume).
  btrfsMounts = lib.filter (fs: fs.fsType == "btrfs") (lib.attrValues config.fileSystems);
  byDevice = lib.groupBy (fs: toString fs.device) btrfsMounts;
  scrubTargets = lib.mapAttrsToList
    (_: fss: (lib.head (lib.sort (a: b: a.mountPoint < b.mountPoint) fss)).mountPoint)
    byDevice;

  scrubMaybeCancel = pkgs.writeShellScript "btrfs-scrub-maybe-cancel" ''
    ${pkgs.btrfs-progs}/bin/btrfs scrub cancel "$1" || [ $? -eq 2 ]
  '';
in
{
  options.roudix.btrfs.autoScrub = lib.mkOption {
    description = ''
      Monthly btrfs scrub (reads everything and verifies checksums, so silent
      corruption is found while it can still be repaired). Does nothing on a
      machine without a btrfs filesystem. The scrub runs with idle I/O priority.
    '';
    type = lib.types.bool;
    default = true;
  };

  config = lib.mkIf (cfg.autoScrub && scrubTargets != [ ]) {
    services.btrfs.autoScrub = {
      enable = true;
      interval = "monthly";
      fileSystems = scrubTargets;
    };

    # The stock unit runs `btrfs scrub cancel` on stop, which exits non-zero
    # when no scrub is running (it already finished) and marks the unit as
    # failed. Accept that case (exit code 2).
    systemd.services."btrfs-scrub@".serviceConfig.ExecStop =
      lib.mkForce "${scrubMaybeCancel} %f";
  };
}

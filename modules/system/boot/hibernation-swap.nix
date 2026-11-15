# Pure resume-device selection policy, shared by hibernation.nix and
# tests/hibernation-swap.nix. Builtins only, on purpose: the test evaluates
# without nixpkgs or network (`nix-instantiate --eval --strict`).
let
  isZram = device: builtins.match ".*zram.*" device != null;

  # resume= wants a block device. A swapfile is a file path that the kernel can
  # only read back with an extra resume_offset, so it cannot carry
  # boot.resumeDevice on its own.
  isBlockDevice = device: builtins.substring 0 5 device == "/dev/";

  declared = swaps: builtins.filter (s: s ? device && s.device != null) swaps;

  onDisk = swaps: builtins.filter (s: !(isZram s.device)) (declared swaps);
in
{
  # First on-disk swap backed by a block device, or null.
  resumeDevice =
    swaps:
    let
      candidates = builtins.filter (s: isBlockDevice s.device) (onDisk swaps);
    in
    if candidates == [ ] then null else (builtins.head candidates).device;

  # True when there is an on-disk swap but none is a block device: the user
  # must then set resumeDevice and resume_offset for the swapfile themselves.
  onlySwapFile =
    swaps:
    let
      disk = onDisk swaps;
    in
    disk != [ ] && builtins.filter (s: isBlockDevice s.device) disk == [ ];

  # True when nothing but zram is available to hold the hibernation image.
  noDiskSwap = swaps: onDisk swaps == [ ];
}

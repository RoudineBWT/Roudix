# Offline test of modules/system/boot/hibernation-swap.nix.
#   nix-instantiate --eval --strict tests/hibernation-swap.nix   # prints true
let
  swap = import ../modules/system/boot/hibernation-swap.nix;
  ok = name: cond: if cond then true else throw "FAIL: ${name}";

  part = { device = "/dev/disk/by-uuid/aaaa"; };
  part2 = { device = "/dev/nvme0n1p3"; };
  file = { device = "/swap/swapfile"; };
  zram = { device = "/dev/zram0"; };
in
builtins.all (x: x) [
  (ok "no swap at all" (swap.noDiskSwap [ ] && swap.resumeDevice [ ] == null && !swap.onlySwapFile [ ]))
  (ok "zram only is not a resume target" (swap.noDiskSwap [ zram ] && swap.resumeDevice [ zram ] == null))
  (ok "partition is picked" (swap.resumeDevice [ part ] == part.device && !swap.noDiskSwap [ part ]))
  (ok "zram is skipped before a partition" (swap.resumeDevice [ zram part ] == part.device))
  (ok "first partition wins" (swap.resumeDevice [ part part2 ] == part.device))
  (ok "swapfile alone needs manual resume" (swap.onlySwapFile [ file ] && swap.resumeDevice [ file ] == null))
  (ok "swapfile + partition uses the partition" (swap.resumeDevice [ file part ] == part.device && !swap.onlySwapFile [ file part ]))
  (ok "entries without a device are ignored" (swap.noDiskSwap [ { label = "x"; } { device = null; } ]))
]

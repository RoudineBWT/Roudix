# ── boot.local.nix ──────────────────────────────────────────────────────────
# Personal boot entries — gitignored, never overwritten by git pull.
# Copy: cp modules/system/boot.local.nix.example modules/system/boot.local.nix
# ────────────────────────────────────────────────────────────────────────────
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Roudora
      protocol: efi
      path: uuid(eb1ff8fc-4b5e-40fc-8184-04f69096b2a2):/EFI/BOOT/BOOTX64.EFI
  '';
}

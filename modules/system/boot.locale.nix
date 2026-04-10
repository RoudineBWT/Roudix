# ── boot.local.nix ──────────────────────────────────────────────────────────
# Personal boot entries — gitignored, never overwritten by git pull.
# Copy: cp modules/system/boot.local.nix.example modules/system/boot.local.nix
# ────────────────────────────────────────────────────────────────────────────
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Windows
      protocol: efi
      path: uuid(ff4a714e-8ba8-4b3b-bf24-27ab1d7c4364):/EFI/Microsoft/Boot/bootmgfw.efi
  '';
}

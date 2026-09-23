{ ... }:
{
  # boot.local.nix / boot.local.nix.example are NOT imported here — they're
  # plain data files (an attrset with `extraEntries`), read directly via
  # `import ./boot.local.nix` from inside boot.nix, not NixOS modules.
  imports = [
    ./boot.nix
    ./kernel.nix
    ./cpu.nix
  ];
}

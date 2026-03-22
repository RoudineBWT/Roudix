{ pkgs, username, ... }:
{
  # ── Fish ─────────────────────────────────────────────────────────────────
  programs.fish = {
    enable = true;
    shellAliases = {
      update = "sudo nix flake update --flake $NH_FLAKE && nh os switch $NH_FLAKE";
      rebuild = "nh os switch $NH_FLAKE";
      cleanup = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
    };
  };

  programs.starship = {
    enable = true;
    enableFishIntegration = true;
  };
}

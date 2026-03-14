{ pkgs, ... }:
{
  # ── Fish ─────────────────────────────────────────────────────────────────
  programs.fish = {
    enable = true;
    shellAliases = {
      update  = "sudo nix flake update";
      rebuild = "sudo nixos-rebuild switch --flake /home/roudine/.config/roudix#roudix";
      cleanup = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
    };
  };

  programs.starship = {
      enable = true;
      enableFishIntegration = true;
    };
}

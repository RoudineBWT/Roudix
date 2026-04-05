{ pkgs, username, ... }:
{
  # ── Fish ─────────────────────────────────────────────────────────────────
  programs.fish = {
    enable = true;
    shellAliases = {
      update = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config $NH_FLAKE";
      rebuild = "nh os switch --accept-flake-config $NH_FLAKE";
      cleanup = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
      noctalia-reload = "pkill quickshell; sleep 1; noctalia-shell --no-duplicate & disown";
    };
  };

  programs.starship = {
    enable = true;
    enableFishIntegration = true;
  };
}

{ username, ... }:
{
  programs.bash = {
    enable = true;
    shellAliases = {
      rebuild = "nh os switch /home/${username}/.config/roudix";
      update = "sudo nix flake update --flake /home/${username}/.config/roudix && nh os switch /home/${username}/.config/roudix";
      cleanup = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
    };
  };
}

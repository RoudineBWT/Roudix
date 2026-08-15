{ ... }:
{
  services.ssh-agent.enable = true;

  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    settings = {
      "*" = {
        addKeysToAgent = "yes";
      };
      "github.com" = {
        hostname = "github.com";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "codeberg.org" = {
        hostname = "codeberg.org";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "minecraft-server" = {
        hostname = "192.168.1.44";
          user = "admin";
          identityFile = "~/.ssh/minecraft-server";
        };
    };
  };
}

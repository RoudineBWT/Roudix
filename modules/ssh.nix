{ ... }:
{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    matchBlocks = {
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
    };
  };
}

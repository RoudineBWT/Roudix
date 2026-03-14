{ ... }:
{
  programs.git = {
    enable = true;
    userName = "roudinebwt";
    userEmail = "roudinebwt@proton.me";
    extraConfig = {
      init.defaultBranch = "main";
      pull.rebase = false;
    };
  };
}

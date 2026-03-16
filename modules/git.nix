{ ... }:
{
  programs.git = {
    enable = true;
    settings = {
      user.name = "roudinebwt";
      user.email = "roudinebwt@proton.me";
      init.defaultBranch = "main";
      pull.rebase = false;
    };
  };
}

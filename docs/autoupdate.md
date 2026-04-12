# Auto-update

When `roudix.autoupdate.enable = true`, the system checks GitHub every hour (and 5 min after boot).
If new commits are detected on `main`, it pulls and runs `nh os boot path:...` — the new config applies on next reboot.
Your `local.nix` files, `username.nix`, `hardware-configuration.nix` and everything under `dotfiles/perso/` are gitignored and never touched by the pull.

To configure the interval or branch, override in `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;
  roudix.autoupdate.interval = "6h";   # check every 6 hours instead of 1h
  roudix.autoupdate.branch   = "main"; # branch to track
}
```

Check the last run:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

To manually trigger an update at any time:

```fish
update
```

*[Version française](autoupdate.fr.md)*

# Auto-update

When `roudix.autoupdate.enable = true`, the system checks GitHub every hour (and 5 min after boot).
If new commits are detected on the tracked branch (`main` by default), it pulls and runs `nh os boot path:...` — the new config applies on next reboot.
Your `local.nix` files, `username.nix`, `hardware-configuration.nix`, the optional `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix` and everything under `dotfiles/perso/` are gitignored and never touched by the pull.

To configure the interval or branch, override in `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # if you set false at this one, config.roudix.autoupdate will take the relai to update but not git pulled
  roudix.autoupdate.interval = "6h";   # check every 6 hours instead of 1h
  roudix.autoupdate.branch   = "main"; # branch to track: "main" (stable), "testing" or "dev" — set by the installer
}
```

The branch is chosen in the installer (both the script and the graphical ISO installer). You can change it later from **Roudix Switcher → System → Update branch**, which also switches your local `~/.config/roudix` checkout to that branch before rebuilding.

Auto-update only ever fast-forwards: if your machine has local commits that are not on GitHub (or has diverged), it does not touch them and notifies you instead.

Check the last run:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

To manually trigger an update at any time:

```fish
update
```

It does the same pull (same branch, same fast-forward-only rule, same lock so it never overlaps a running auto-update), then rebuilds and updates your Flatpaks. See [`update`](aliases.md#update) for its options.

The build may take up to 2 hours before systemd gives up. If the run is killed or stops unexpectedly (timeout, crash), a notification is sent; a plain error already notifies on its own. After an auto-update, `update --changes` shows what will be applied at the next boot.

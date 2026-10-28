**English** · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · [Português (Brasil)](autoupdate.pt_BR.md) · [Русский](autoupdate.ru.md) · [简体中文](autoupdate.zh_CN.md) · [हिन्दी](autoupdate.hi.md) · [العربية](autoupdate.ar.md)

# Auto-update

When `roudix.autoupdate.enable = true`, the system checks GitHub every hour (and 5 min after boot).
If new commits are detected on the tracked branch (`main` by default), it pulls and runs `nixos-rebuild boot --flake path:...` (as root, no `nh`) — the new config applies on next reboot.
Your `local.nix` files, `username.nix`, `hardware-configuration.nix`, the optional `modules/home/niri-custom.nix` / `modules/home/umbriel-custom.nix` / `modules/home/mango-custom.nix` and everything under `dotfiles/perso/` are gitignored and never touched by the pull.

To configure the interval or branch, override in `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # false = no timer, no automatic pull (use `update` manually)
  roudix.autoupdate.interval = "6h";   # check every 6 hours instead of 1h
  roudix.autoupdate.branch   = "main"; # branch to track: "main" (stable), "testing" or "dev" — set by the installer
  roudix.autoupdate.onBootDelay = "5min"; # delay before the first check after boot
  roudix.autoupdate.minFreeSpaceGB = 5;   # skip (and notify) if /nix/store has less free space
  roudix.autoupdate.configPath = "/home/<user>/.config/roudix"; # repository to update
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

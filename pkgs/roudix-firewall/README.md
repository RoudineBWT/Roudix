<p align="center"><img src="io.roudix.firewall.svg" width="96" alt="Roudix Firewall"></p>

# roudix-firewall

GTK4/Adwaita app to manage the NixOS firewall on Roudix: turn it on or off, open ports
(TCP / UDP, single ports and ranges), and choose trusted interfaces (`docker0`, `virbr0`,
`tailscale0`…). Python take on GLF-OS's
[nix-firewall-mngt](https://framagit.org/gaming-linux-fr/glf-os/app-glf-os/nix-firewall-mngt)
(Rust); same idea, written from scratch for Roudix's flake layout.

## Where the options live

Everything the app changes is written to **one file per host**:

```
hosts/<host>/firewall.local.nix
```

- It is **gitignored** (`hosts/*/firewall.local.nix`, backup `*.bak` too), like `local.nix`.
  `git pull` and `roudix-autoupdate` (`git merge --ff-only`) never overwrite it, and it can
  never make a fast-forward fail on a "local modification".
- `hosts/<host>/configuration.nix` imports it when it exists
  (`lib.optional (builtins.pathExists ./firewall.local.nix) …`), the same way as `local.nix`.
  Roudix builds with `path:` flake references, which is why a gitignored file is visible to Nix.
- It is a separate file rather than a block inside `local.nix`, so the app never has to edit
  a file you maintain by hand. `networking.firewall.*` lines you already have in `local.nix`
  keep working: lists are merged with the app's, and a banner tells you they are there.

`<host>` is the machine's hostname (override with `ROUDIX_HOST=<name>`); the flake path is
`~/.config/roudix` (override with `NH_FLAKE`).

### What the file looks like

```nix
# roudix-firewall:v1 {"enabled": true, "rules": [...], "sha256": "…"}
{ lib, ... }:
{
  networking.firewall = {
    enable = lib.mkForce true;
    allowedTCPPorts = [ 22 80 443 ];
    allowedUDPPortRanges = [
      { from = 27015; to = 27030; }
    ];
    trustedInterfaces = [ "docker0" ];
  };
}
```

- `enable` uses `lib.mkForce`: `modules/system/nix/common.nix` already sets
  `networking.firewall.enable = true`, so a plain `false` would be a conflict.
- The JSON comment keeps what Nix cannot: rule names and **disabled** rules (they stay in
  the app, they are just not emitted). The SHA-256 is of the Nix below it: if you edit the
  Nix by hand, the hash no longer matches and the app reads the Nix itself instead (names are
  kept for rules that still exist), so a manual edit is never silently ignored.

## What it does

1. Reads `hosts/<host>/firewall.local.nix` (nothing yet = firewall on with the defaults of `modules/system/nix/common.nix`, i.e. port 443 open).
2. You edit rules, presets and interfaces. Nothing is written until you press a button.
3. **Save** writes the file (atomically, previous version kept as `firewall.local.nix.bak`);
   it takes effect at the next rebuild, including the auto-update's.
4. **Save & apply** also runs
   `nh os switch --elevation-strategy pkexec --accept-flake-config path:~/.config/roudix`
   and shows its output. **If the rebuild fails, the previous file is put back**: a firewall
   file that does not build would otherwise also break the auto-update.
5. Turning the firewall **off** asks for confirmation.

Ports are validated (1–65535, `from <= to`), interface names too (Linux limit of 15
characters), so what ends up in the Nix is always well-formed.

## Presets

SSH, HTTP/HTTPS, DNS, Steam game server, Sunshine (TCP and UDP ports), Minecraft Java /
Bedrock, KDE Connect / GSConnect, Syncthing, Samba, LocalSend. Interface suggestions:
Docker, Podman, Libvirt, bridge, Tailscale, WireGuard.

## Files

| File | Role |
|------|------|
| `roudix-firewall.py` | The GTK4/Adwaita app |
| `roudix_firewall_core.py` | Model, presets, Nix generation/parsing, atomic write, rollback. No GTK |
| `tests/test_core.py` | Unit tests for the core (`python3 pkgs/roudix-firewall/tests/test_core.py`) |
| `io.roudix.firewall.svg` / `-light.svg` | App icon (dark / light) |
| `po/` | Translations (`scripts/i18n.sh update firewall`) |
| `default.nix` | Package and `.desktop` entry |

## Run

```bash
roudix-firewall
```

Logs: `~/.local/share/roudix-firewall/firewall.log`.

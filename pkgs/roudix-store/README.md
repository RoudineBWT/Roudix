# roudix-store

Software center for Roudix. UI and AppStream catalog code derived from
Nobara's [dnf-app-center](https://github.com/Nobara-Project/dnf-app-center)
(GPL-2.0, see `COPYING`); the libdnf5 backend is replaced by `nix_backend.py`.

- Catalog / icons: `nixos-appstream-data` (flake input), via libappstream.
- Search beyond AppStream apps: nixpkgs `packages.json.br`, cached 7 days.
- Install/remove: edits a managed block in `local.nix`
  (`roudix.store.packages` → modules/home, `roudix.store.systemPackages` → hosts/<host>),
  then `nh os switch`. A failed rebuild restores both files.
- Flatpak tab (Nix | Flatpak switch in the sidebar): Flathub and Flathub Beta metadata come from what `flatpak`
  already downloaded (`flatpak update --appstream`), read remote by remote from the system and user installations.
  Beta builds are listed next to the stable ones, suffixed "(Beta)". The "Install system-wide" switch picks the target,
  like for Nix: off = user installation, on = system installation. Installs are recorded in `local.nix` (gitignored)
  and handed to nix-flatpak on the next switch:

  | remote        | system (`hosts/<host>/local.nix`) | user (`modules/home/local.nix`)     |
  |---------------|-----------------------------------|-------------------------------------|
  | flathub       | `roudix.store.flatpaks`           | `roudix.store.flatpaksUser`         |
  | flathub-beta  | `roudix.store.flatpaksBeta`       | `roudix.store.flatpaksUserBeta`     |

  Requires `roudix.flatpak.enable = true` (user installs use nix-flatpak's Home Manager module).
- Not supported (by design): updates page, repositories, RPM drops — updates come from the flake.

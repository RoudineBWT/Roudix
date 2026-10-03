# roudix-store

Software center for Roudix. UI and AppStream catalog code derived from
Nobara's [dnf-app-center](https://github.com/Nobara-Project/dnf-app-center)
(GPL-2.0, see `COPYING`); the libdnf5 backend is replaced by `nix_backend.py`.

- Catalog / icons: `nixos-appstream-data` (flake input), via libappstream.
- Search beyond AppStream apps: nixpkgs `packages.json.br`, cached 7 days.
- Install/remove: edits a managed block in `local.nix`
  (`roudix.store.packages` → modules/home, `roudix.store.systemPackages` → hosts/<host>),
  then `nh os switch`. A failed rebuild restores both files.
- Flatpak tab (Nix | Flatpak switch in the sidebar): Flathub metadata comes from what `flatpak` already
  downloaded (`flatpak update --appstream`); installs go to `roudix.store.flatpaks` in `hosts/<host>/local.nix`
  (gitignored), handed to nix-flatpak on the next switch. Requires `roudix.flatpak.enable = true`.
- Not supported (by design): updates page, repositories, RPM drops — updates come from the flake.

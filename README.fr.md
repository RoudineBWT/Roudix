[English](README.md) · **Français** · [Español](README.es.md) · [Português (Brasil)](README.pt_BR.md) · [Русский](README.ru.md) · [简体中文](README.zh_CN.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### Configuration NixOS (Unstable) — Plusieurs compositeurs Wayland (hyprland, niri, mangowc et umbriel) · Gnome et KDE · Kernel CachyOS

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| Aperçu |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Diaporama d'aperçu de Roudix : Umbriel, GNOME et KDE Plasma" width="900"/> |

<sub>Personnalisation perso — la vôtre sera différente selon votre configuration 👀</sub><br/>
<sub>Les compositeurs Wayland sont laissés à votre personnalisation : Roudix ne fournit que la config par défaut de Noctalia, DankMaterialShell et (Hyprland uniquement) Caelestia.</sub>

</div>

---

## Matériel

| Composant | Modèle |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## Stack

| Couche | Choix |
|-------|--------|
| OS | Roudix (NixOS unstable) |
| Kernel | CachyOS (choisissez votre variante dans [Fonctionnalités](docs/features.fr.md) ou dans [Installation](docs/installation.fr.md)) |
| Bootloader | Limine (par défaut) · systemd-boot |
| Compositeur | Niri (tiling scrollable) · Hyprland (tiling dynamique) · MangoWC · Umbriel (tiling scrollable, natif Noctalia) |
| Shell graphique | Noctalia · DankMaterialShell · Caelestia |
| Environnement de bureau | KDE Plasma · GNOME · Cinnamon · COSMIC |
| Gestionnaire de connexion | Noctalia Greeter (Noctalia) · DMS Greeter (DMS) · Ly (Hyprland/MangoWC sans Noctalia) · plasma-login-manager (KDE) · GDM (GNOME) · LightDM (Cinnamon) · cosmic-greeter (COSMIC) |
| Terminal | Configurable (Ghostty, Kitty, Alacritty, Foot, WezTerm, Konsole, Ptyxis) |
| Shell | Fish · Bash |
| Navigateur | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Ungoogled Chromium, Chrome, Edge — Zen via `roudix.zen`) |
| Gestionnaire de fichiers | Configurable (Nautilus, Thunar, Dolphin, Nemo) |
| Éditeur | Configurable (Zed, VS Code, Neovim, aucun) |
| Chat | Discord (Vencord · vanilla · aucun) + Matrix (Element · Cinny · aucun) |
| Musique | Configurable (Spotify + Spicetify, YouTube Music Desktop, Sonora, aucun) |

---

## Documentation

| | |
|-|-|
| 🖥️ [Bureau & shells](docs/desktop.fr.md) | Changer de compositeur et de shell graphique, surcharges personnelles (Niri, Hyprland, GNOME, KDE) |
| ⚡ [Alias & fonctions](docs/aliases.fr.md) | Tous les alias et fonctions shell — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [Installation](docs/installation.fr.md) | Guide d'installation automatisée et manuelle |
| ✨ [Fonctionnalités](docs/features.fr.md)  | Liste complète des fonctionnalités par environnement de bureau |
| 🔄 [Mise à jour automatique](docs/autoupdate.fr.md) | Configuration du git pull + rebuild automatique |

---

## Structure

```
roudix/
├── roudix-installer.sh              # Installeur en Bash
├── flake.nix / flake.lock           # Entrées & sorties (une entrée nixosConfigurations par hosts/<nom>/)
├── version.nix / branding.nix       # Branding Roudix OS (os-release, distroName)
├── Justfile                         # Tâches de dev (`just ci`)
├── docs/                            # Documentation
│   └── desktop / aliases / installation / features / autoupdate (.md + .<lang>.md) · secure-boot-eac.md
│
├── hosts/                           # Un dossier par machine — chacun devient nixosConfigurations.<nom>
│   ├── roudix/ · nixie/             # DE choisi via roudix.desktop.type
│   │   ├── configuration.nix
│   │   ├── username.nix             # ignoré par git — votre nom d'utilisateur (voir installation)
│   │   ├── local.nix                # ignoré par git — vos surcharges système personnelles
│   │   ├── local.nix.example        # copiez-le en local.nix pour démarrer
│   │   ├── firewall.local.nix       # ignoré par git — écrit par roudix-firewall
│   │   └── hardware-configuration.nix  # ignoré par git
│
├── dotfiles/                        # Fichiers de config bruts gérés par Home Manager
│   ├── easyeffects/ · fastfetch/    # Presets EasyEffects, logo fastfetch (roudix-ascii.txt)
│   ├── hyprland/                    # Config Hyprland (Lua) — un seul arbre pour tous les shells graphiques
│   │   ├── hyprland.lua             # Point d'entrée : charge les modules de config/
│   │   └── config/                  # shell.lua, shells/, binds/, rules/, ws.lua, monitors.lua… (nix-plugins.lua / nix-apps.lua sont générés par Nix)
│   └── perso/                       # Config personnelle (ignorée par git)
│
├── iso/                             # ISO live + installeur graphique
│   └── roudix-installer/            # Installeur GTK4/libadwaita (disko, mode « NixOS existant », traductions gettext)
├── scripts/                         # CI / outillage (i18n.sh, release.sh, check-path-refs.py, ai-commit.py…)
│
├── pkgs/
│   ├── roudix-branding / roudix-config / roudix-welcome
│   ├── roudix-switcher/             # GUI Roudix Customizer/Settings (bureau, gaming, éditeur, terminal, navigateur, shell, gestionnaire de fichiers, chat, système, intégration)
│   ├── roudix-kernel-switcher / roudix-scheduler-switcher / roudix-hw-sync
│   ├── roudix-firewall/             # GUI pare-feu (ports, interfaces de confiance → hosts/<hôte>/firewall.local.nix)
│   ├── roudix-disk/ · roudix-store/ # Outil disque · logithèque (Nix + Flatpak)
│   └── nemo-terminal/
│
└── modules/
    ├── desktop-pkgs.nix             # Sélection des paquets niri/mango/umbriel/shell (nixpkgs ou flake)
    ├── system/                      # Modules NixOS au niveau système
    │   ├── desktop/                 # Un module par DE + réglages de bureau partagés
    │   │   ├── default.nix          # roudix.desktop.type / .shell / .latest
    │   │   ├── niri / hyprland / mangowc / umbriel / gnome / kde / cinnamon / cosmic .nix
    │   │   └── ly.nix · keyboard.nix · icon-theme.nix · desktop-integration.nix
    │   ├── boot/                    # Bootloader, kernel & CPU
    │   │   └── boot.nix · secure-boot.nix · boot.local.nix (ignoré par git) · kernel.nix · cpu.nix · bootloader/
    │   ├── apps/                    # Modules de sélection d'app (une option roudix.* chacun)
    │   │   └── browser/ communication/ creation/ media/ utilities/ apps.nix
    │   ├── packaging/               # appimage.nix · flatpak.nix · store.nix
    │   ├── nix/                     # Réglages Nix, caches, auto-update, commande `update`
    │   │   └── autoupdate.nix · binary-caches.nix · common.nix · update.nix · roudix-update.{nix,sh} · completions/
    │   ├── core/                    # environment, fstrim, shell par défaut, tuning (ZRAM/sysctl)
    │   ├── audio/                   # pipewire.nix
    │   ├── gaming/                  # Steam, Gamescope, session Gaming Mode, SCX, fix hosts GTA
    │   ├── gpu/                     # AMD / NVIDIA / Intel / VM + mesa-git, undervolt
    │   ├── rgb/                     # roudix.rgb (openlinkhub / openrgb / none)
    │   ├── power/                   # laptop.nix
    │   └── virtualization/          # QEMU/KVM, conteneurs, invité VM, Waydroid
    │
    └── home/                        # Modules Home Manager au niveau utilisateur
        ├── common.nix               # Config home partagée
        ├── local.nix                # ignoré par git
        ├── niri-custom.nix / umbriel-custom.nix / mango-custom.nix  # ignoré par git (surcharges personnelles du compositeur)
        ├── shell/                   # bash/fish/fastfetch + roudix-switch / -kernel-switch / -shell-switch
        ├── dev/                     # git, ssh, gitwatch (git.nix / ssh.nix sont ignorés par git — copiez le .example)
        ├── apps/                    # Config des apps côté home (browser/zen, media/spicetify, store…)
        ├── theming/                 # GTK, icônes (Papirus/Tela), palette, MangoHud, thème de terminal
        ├── gaming/                  # gaming-home.nix
        └── desktop/                 # Un dossier par DE, miroir de modules/system/desktop/
            ├── default.nix          # Importe les huit (chacun protégé par lib.mkIf)
            └── niri / hyprland / mangowc / umbriel / gnome / kde / cinnamon / cosmic
```

---

## Entrées de la flake

| Entrée | Source |
|-------|--------|
| nixpkgs | [nixos-unstable](https://github.com/NixOS/nixpkgs/tree/nixos-unstable) |
| nixpkgs-stable | [nixos-26.05](https://github.com/NixOS/nixpkgs/tree/nixos-26.05) |
| niri | [epireyn/niri-flake](https://github.com/epireyn/niri-flake) |
| home-manager | [nix-community/home-manager](https://github.com/nix-community/home-manager) |
| noctalia | [noctalia-dev/noctalia](https://github.com/noctalia-dev/noctalia) |
| umbriel | [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) |
| caelestia-shell | [caelestia-dots/shell](https://github.com/caelestia-dots/shell) |
| dms | [AvengeMedia/DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) |
| nix-cachyos-kernel | [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel) |
| chaotic | [chaotic-cx/nyx](https://github.com/chaotic-cx/nyx) |
| zen-browser | [0xc000022070/zen-browser-flake](https://github.com/0xc000022070/zen-browser-flake) |
| spicetify-nix | [Gerg-L/spicetify-nix](https://github.com/Gerg-L/spicetify-nix) |
| millennium | [SteamClientHomebrew/Millennium](https://github.com/SteamClientHomebrew/Millennium) |
| helium | [x13-me/helium-nix](https://github.com/x13-me/helium-nix) |
| nix-flatpak | [gmodena/nix-flatpak](https://github.com/gmodena/nix-flatpak) |
| plasma-manager | [nix-community/plasma-manager](https://github.com/nix-community/plasma-manager) |
| brave-previews | [roudinebwt/brave-preview](https://github.com/roudinebwt/brave-preview) |
| roudix-caches | [RoudineBWT/Roudix-caches](https://github.com/RoudineBWT/Roudix-caches) |
| nix-gaming-edge | [powerofthe69/nix-gaming-edge](https://github.com/powerofthe69/nix-gaming-edge) |
| betterbird-nix | [TheAnachronism/betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) |
| nixpkgs-master / nixpkgs-staging-next | [NixOS/nixpkgs](https://github.com/NixOS/nixpkgs) — uniquement pour les kernels nixpkgs (`hardware.myKernelSource`) |
| mango | [mangowm/mango](https://github.com/mangowm/mango) |
| noctalia-greeter | [noctalia-dev/noctalia-greeter](https://github.com/noctalia-dev/noctalia-greeter) |
| dank-greeter | [AvengeMedia/dank-greeter](https://github.com/AvengeMedia/dank-greeter) |
| jovian | [Jovian-Experiments/Jovian-NixOS](https://github.com/Jovian-Experiments/Jovian-NixOS) — Decky Loader uniquement |
| nixos-appstream-data | [vlinkz/nixos-appstream-data](https://github.com/vlinkz/nixos-appstream-data) — catalogue du Roudix Store |
| sonora | [sonorahq/sonora](https://github.com/sonorahq/sonora) |
| eacnix | [samos667/eacnix](https://github.com/samos667/eacnix) — commit épinglé, utilisé seulement avec `roudix.boot.eac.enable` |

---

## Voir aussi

| Projet | Description |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | Distro gaming basée sur NixOS, par Gaming Linux FR |

---

## Dotfiles personnels

Les fichiers de config personnels vivent dans `dotfiles/perso/` — ils sont ignorés par git (sauf `dotfiles/perso/README.md`) et ne sont jamais touchés par `git pull` ou l'auto-updater.

Voir [`dotfiles/perso/README.md`](dotfiles/perso/README.md) pour la structure et l'usage.

Pour les surcharges au niveau du compositeur (écrans, raccourcis, espacements…), utilisez plutôt les fichiers de surcharge utilisateur générés — ils sont gérés par home-manager et à l'abri de `git pull`. Voir [Bureau & shells](docs/desktop.fr.md#surcharges-personnelles-du-compositeur) pour plus de détails.


## Développement

```bash
nix develop     # shell de dev : just, ruff, statix, deadnix, shellcheck, gettext
just            # liste les tâches
just ci         # tout ce que vérifie la CI (évalue chaque hôte, lint, Python, traductions)
```

L'installeur est traduit avec gettext — voir [Installeur › Traductions](iso/roudix-installer/README.md#traductions).

## Licence
   MIT — Voir [LICENSE](LICENSE). Le Roudix Store est soumis exclusivement à la licence GPL-2.0, et certains
   fichiers provenant de tiers conservent leurs propres licences : voir [THIRD_PARTY.md](THIRD_PARTY.md).

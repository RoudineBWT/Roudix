*[English version](features.md)*

# Fonctionnalités

## Kernel & Performance

- Kernel CachyOS avec NTSync activé (module `ntsync`)
- Deux fournisseurs de kernel, choisis automatiquement selon `hardware.myGpu` :
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 32 variantes (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 variantes (`hardware.myKernelChaotic`) — fournit `nvidia_cachyos`, un driver précompilé assorti à leur kernel, donc pas de recompilation locale du module Nvidia à chaque mise à jour du kernel
- Kernels nixpkgs "bruts" aussi sélectionnables sur les deux fournisseurs, complètement en dehors de l'overlay CachyOS — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline). Sur Nvidia, ceux-ci retombent sur un module Nvidia recompilé localement (pas de cache `nvidia_cachyos`)
- ZRAM activé (100% de la RAM, zstd, swappiness 150)
- zswap désactivé
- Microcode CPU auto-configuré (Intel ou AMD)
- Intel : `split_lock_detect=off` appliqué automatiquement
- ananicy-cpp activé (démon de priorité des process, règles CachyOS)
- Support du scheduler SCX — changement à chaud, sans reboot (bpfland, lavd, flash, p2dq, rusty…) via le Kernel Switcher — un seul mot de passe demandé via `scx-switch` gère l'arrêt/démarrage d'ananicy-cpp et le changement de scheduler en une fois — **note :** SCX n'est pas persistant après reboot ; après redémarrage, ananicy-cpp redémarre automatiquement et le scheduler doit être ré-appliqué via le Kernel Switcher

## Démarrage

- Bootloader Limine (par défaut) — moderne, rapide, support multi-disque — ou systemd-boot, sélectionnable via `roudix.boot.bootloader`
- Renommage automatique de l'entrée UEFI en "Roudix"
- Menu de boot multi-OS (Windows, autres distros Linux sur des ESP séparées)
- L'étiquette de boot affiche le nom Roudix + la version de la release NixOS

## Gaming

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, session désactivée par défaut)
- Variables d'environnement de capture OBS pré-configurées (`OBS_VKCAPTURE` via `environment.sessionVariables`)
- Overlay MangoHud horizontal personnalisé (étiquette "Powered By Roudix")
- Support manette (Steam Hardware + game-devices-udev-rules)
- Support 32-bit pour Wine/Steam
- Wrapper `game-performance` — bascule sur un profil `tuned-adm` dédié aux performances le temps d'une partie, suivi via un cgroup `systemd-run --user --scope` (survit au fork/détachement de Steam) et restauré à la sortie (usage : `game-performance %command%` dans les options de lancement Steam) — GameMode est désactivé volontairement (incompatible avec ananicy-cpp ici)
- `ffmpegthumbnailer` disponible dans tout le système (miniatures vidéo dans les gestionnaires de fichiers)
- `protonup-qt` sur KDE, `protonplus` sur les autres environnements
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft, ou Modrinth App en alternative — `roudix.gaming.apps.modrinth.enable`) et Vintage Story (via roudix-caches)
- Chaque app gaming activable/désactivable individuellement via `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (toutes `true` par défaut)

## Bureau (Niri)

- Compositeur Wayland en tuilage défilant Niri — fourni via [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), `niri-unstable` par défaut, avec le cache binaire `niri.cachix.org` pré-configuré
- Config native en Nix (`programs.niri.settings`), découpée par thème (général, animations, input, layout, sorties, raccourcis, règles) et validée au build via `niri validate` — une config cassée fait échouer le build plutôt que le compositeur au login
- La synchronisation de thème en direct Noctalia/DMS (couleurs générées par matugen/DMS, alt-tab, flou) est préservée en ajoutant un `include` à la config générée plutôt qu'en la figeant statiquement
- Shell moderne Noctalia (v5)
- xdg-desktop-portal-gnome + gtk (portails screencast + bureau à distance configurés)
- Curseur Bibata Modern Ice (24 px)
- adw-gtk3 + icônes Papirus + Papirus Folders
- Element Desktop avec gnome-libsecret / kwallet6 (détecté automatiquement selon l'environnement)
- Agent Polkit GNOME
- Greeter DMS (greetd)

## Bureau (MangoWC)

- Compositeur Wayland MangoWC
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Curseur Bibata Modern Ice (24 px)
- Agent Polkit GNOME
- Gestionnaire de connexion Ly
- adw-gtk3 + icônes Papirus + Papirus Folders
- Animation de zoom à l'ouverture + courbes de Bézier officielles
- VRR + tearing activés sur l'écran gaming (DP-1 1440p@240)
- Captures d'écran avec grim + slurp + satty (annotation) — 3 raccourcis
- Switcher de fenêtres rofi (Alt+Tab)
- Variables d'environnement XDG Desktop Portal pré-configurées (capture d'écran Pipewire, OBS, Discord Go Live)
- force_tearing + idleinhibit_when_focus sur toutes les apps gaming (Steam, Heroic, Minecraft, Lutris, Bottles)
- Opacité des fenêtres non focalisées (0.85)
- Vue d'ensemble Hotarea (geste souris dans le coin)
- Snap flottant + glisser-déposer tuile-à-tuile

## Bureau (Umbriel)

- Compositeur Wayland en tuilage défilant Umbriel — le compositeur natif de Noctalia, fourni via [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (Noctalia uniquement, pas de changement de shell)
- Config native en Nix (`programs.umbriel.settings`), découpée par thème (général, apparence, animation, input, layout, sorties, raccourcis, règles) et validée au build (`validateConfig = true`)
- La synchronisation de thème en direct de Noctalia (couleurs générées par matugen) est préservée via le mécanisme natif `include.files` d'Umbriel, pas de snapshot de couleurs statique
- Curseur Bibata Modern Ice (24 px)
- adw-gtk3 + icônes Papirus + Papirus Folders
- Coins actifs (vue d'ensemble en amenant la souris dans un coin) et vue d'ensemble des espaces de travail (Mod+O)
- Support du scratchpad (déplacer/basculer/restaurer une fenêtre flottante à la demande)
- Surcharges de layout par espace de travail (ex : pas d'espacement sur l'espace gaming)

## Bureau (Hyprland)

- Compositeur Wayland en tuilage dynamique Hyprland, lancé via UWSM
- Shell moderne Noctalia
- xdg-desktop-portal-hyprland + portail gtk
- Curseur Bibata Modern Ice (24 px)
- Agent Polkit GNOME (démarré via un service utilisateur systemd)
- Démon de fond d'écran swww
- Captures d'écran avec grim + slurp + satty (annotation) — 3 raccourcis

## Bureau (GNOME)

- GNOME 50.x (suit la branche nixos-unstable)
- Ensemble d'extensions sélectionné (flou, tuilage, vitals, arcmenu...) — activées via dconf
- ArcMenu avec le logo Roudix comme icône du bouton menu
- Débloatage via `environment.gnome.excludePackages`
- Thème d'icônes Papirus-Dark
- Thème GTK adw-gtk3-dark (mode sombre par défaut)
- Curseur Bibata Modern Ice (24 px)
- Fond d'écran Roudix (clair/sombre selon le thème système)
- `color-scheme = prefer-dark` appliqué via dconf
- Réglages d'extensions (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) pré-configurés via `gnome-extensions.nix`
- Ajouter/retirer des extensions sans toucher aux fichiers principaux via `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Fond d'écran, thème, icônes, curseur personnalisables dans `home/local.nix`

## Bureau (KDE)

- KDE Plasma 6 avec plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect activé
- xdg-desktop-portal-kde
- Thème d'icônes Papirus-Dark
- Look & feel Breeze Dark + jeu de couleurs
- Fond d'écran Roudix Dark sur l'écran de connexion et le bureau
- Paquets sélectionnés : partitionmanager, kcalc, digikam, vlc...
- Débloatage (Discover exclu)
- Fond d'écran, panneaux, thème d'icônes personnalisables dans `home/local.nix`

## Musique

- Spotify patché avec Spicetify (débrayable via `roudix.apps.spotify.enable`)
- Thème local, "colorful" par défaut (ou "comfy") — voir options ci-dessous
- Extensions adblock + masquage des podcasts

## Apps communes optionnelles

GIMP, Inkscape, SongRec et EasyEffects (+ rnnoise-plugin) sont installés par
défaut mais chacun est débrayable individuellement via
`roudix.apps.<nom>.enable` (`gimp`, `inkscape`, `songrec`, `easyeffects`) —
comme `roudix.apps.spotify.enable` ci-dessus.

Également disponibles, désactivées par défaut : mpv + yt-dlp
(`roudix.apps.mpv.enable`), qBittorrent (`roudix.apps.qbittorrent.enable`),
Telegram Desktop (`roudix.apps.telegram.enable`).

## Spicetify

- Thème : `roudix.spicetify.theme` — `"colorful"` (défaut, sanoojes/spicetify-colorful) ou `"comfy"` (thème Comfy fourni)
- Color scheme : `roudix.spicetify.colorScheme` — `null` (défaut) utilise le défaut du thème ("noctalia" pour colorful, "Comfy" pour comfy)
- Extensions débrayables individuellement : `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (activées par défaut)
- App Marketplace : `roudix.spicetify.marketplace.enable` (activée par défaut)

## Navigateur

- Liste de navigateurs configurable via l'option `roudix.browsers`
- Supporte `brave`, `helium` (via le flake helium-nix), `vivaldi` (avec les codecs ffmpeg), `firefox`, `librewolf`, `chromium`, ou `[]` pour aucun
- Zen Browser disponible séparément via `roudix.zen.enable = true` (désactivé par défaut) ; canal sélectionnable via `roudix.zen.variant` — `"twilight"` (défaut) ou `"beta"`

## Autre

- Discord sélectionnable via `roudix.discord` — `"vencord"` (client patché, défaut), `"vanilla"` (non patché) ou `"none"` (non installé)
- Éditeur de code sélectionnable via `roudix.editor` — `"zed"` (défaut), `"vscode"`, `"neovim"` ou `"none"` (gère le tien, ex : AppImage/Flatpak)
- Disposition clavier graphique (Wayland) via `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, ex : `"be"` / `"intl"`) — indépendant de `console.keyMap`, qui ne couvre que la TTY avant le lancement de la session graphique ; sans effet sur GNOME/KDE, qui gèrent leur propre disposition
- Pile trousseau + xdg-desktop-portal pour les compositeurs "bruts" (Niri, Hyprland, MangoWC, Umbriel) sélectionnable via `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, défaut) ou `"kde"` (KWallet + xdg-desktop-portal-kde) ; sans effet sur les sessions GNOME/KDE, qui gardent leur propre pile native
- `nix-ld` activé pour tout le système — exécute des binaires dynamiques non patchés sans environnement FHS (pré-configuré avec les bibliothèques courantes : glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib et plus)
- OBS Studio, activable/désactivable via `roudix.contentCreation.obs.enable` (défaut `true`), plugins activés un par un via `roudix.contentCreation.obs.plugins.<nom>.enable` (`vkcapture` + `pipewireAudioCapture` actifs par défaut ; également disponibles : `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- Éditeur vidéo sélectionnable via `roudix.contentCreation.videoEditor` — `"kdenlive"` (défaut), `"davinci-resolve"` (gratuit), `"davinci-resolve-studio"` (payant, licence requise), `"shotcut"` ou `"none"` ; DaVinci Resolve reçoit automatiquement un ICD OpenCL AMD quand `hardware.myGpu = "amd"`
- Webcam virtuelle `v4l2loopback` configurée automatiquement pour OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`, défaut `true`)
- Client de chat Twitch Chatterino2, opt-in via `roudix.contentCreation.streaming.chatterino.enable`
- Groupe content-creation entièrement activable/désactivable via `roudix.contentCreation.enable`
- GPU Screen Recorder
- Option Mesa Git pour AMD — active un Mesa expérimental/bleeding-edge via `roudix.mesa.useGit = true` dans `local.nix` (défaut : Mesa stable de nixpkgs) — ⚠️ **expérimental**, le build peut échouer selon l'état de nixpkgs
- Paramètres kernel de stabilité GPU AMD appliqués automatiquement (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — corrige les gels aléatoires et les problèmes de réveil sur RDNA2/RDNA3
- Contrôleur RGB sélectionnable via `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, mis à jour automatiquement via CI), `openrgb` (multi-marques : Razer, ASUS, MSI…), ou `none`
- Interface web OpenLinkHub disponible sur [http://127.0.0.1:27003](http://127.0.0.1:27003) une fois le service lancé
- Contrôle RGB de la RAM DDR4/DDR5 via OpenLinkHub — active avec `roudix.memory.enable = true`, configure `roudix.memory.type`, `roudix.memory.smBus`, et `roudix.memory.sku` (voir `installation.md`)
- PipeWire avec suppression de bruit stéréo rnnoise (nofail, compat LADSPA_PATH 26.05/26.11)
- Flatpak avec le remote Flathub + mise à jour automatique quotidienne (via nix-flatpak)
- Gestionnaire Bluetooth Blueman
- Client Matrix — configurable via `roudix.matrixClient` (`element`, `cinny`, ou `none`) — Element choisit automatiquement kwallet6 sur KDE, gnome-libsecret ailleurs
- Support AppImage activé via `appimage.nix`
- Waydroid (conteneur Android) — optionnel, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (optionnel)
- Module d'optimisations invité VM (partage du presse-papiers, redimensionnement auto, agent QEMU, Spice)

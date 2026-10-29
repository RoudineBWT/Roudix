[English](features.md) · **Français** · [Español](features.es.md) · [Português (Brasil)](features.pt_BR.md) · [Русский](features.ru.md) · [简体中文](features.zh_CN.md) · [हिन्दी](features.hi.md) · [العربية](features.ar.md)

# Fonctionnalités

## Kernel & Performance

- Kernel CachyOS avec NTSync activé (module `ntsync`)
- Deux fournisseurs de kernel, choisis automatiquement selon `hardware.myGpu` :
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 36 variantes (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 variantes (`hardware.myKernelChaotic`) — fournit `nvidia_cachyos`, un driver précompilé assorti à leur kernel, donc pas de recompilation locale du module Nvidia à chaque mise à jour du kernel
- Kernels nixpkgs "bruts" aussi sélectionnables sur les deux fournisseurs, complètement en dehors de l'overlay CachyOS — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline), `xanmod-lts` / `xanmod-latest` (XanMod). Sur Nvidia, ceux-ci retombent sur un module Nvidia recompilé localement (pas de cache `nvidia_cachyos`)
- `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) prend uniquement ces kernels nixpkgs depuis un nixpkgs plus récent pour des mises à jour du kernel plus rapides, sans toucher au reste du système
- ZRAM activé (100% de la RAM, zstd, swappiness 150)
- zswap désactivé
- Microcode CPU auto-configuré (Intel ou AMD)
- Intel : `split_lock_detect=off` appliqué automatiquement
- ananicy-cpp (démon de priorité des process, règles CachyOS) — optionnel, désactivé par défaut : `roudix.gaming.ananicy.enable = true`
- Support du scheduler SCX — changement à chaud, sans reboot (bpfland, lavd, flash, p2dq, rusty…) via le Kernel Switcher — un seul mot de passe demandé via `scx-switch` gère l'arrêt/démarrage d'ananicy-cpp et le changement de scheduler en une fois — **note :** SCX n'est pas persistant après reboot ; après redémarrage, ananicy-cpp redémarre automatiquement et le scheduler doit être ré-appliqué via le Kernel Switcher

## Démarrage

- Bootloader Limine (par défaut) — moderne, rapide, support multi-disque — ou systemd-boot, sélectionnable via `roudix.boot.bootloader`
- Fond d'écran de boot Limine en 4 formats (16:9, 16:10, 21:9, 4:3), choisi via `roudix.boot.wallpaperAspect` — les deux installeurs et `roudix-switcher` détectent ton écran principal (celui qui a la plus grande résolution) et proposent le bon format, pratique après un changement d'écran. Avec plusieurs écrans de tailles différentes, `roudix.boot.menuResolution` force le menu Limine à la résolution de ton écran principal (sinon Limine peut prendre le plus petit)
- Renommage automatique de l'entrée UEFI en "Roudix"
- Menu de boot multi-OS (Windows, autres distros Linux sur des ESP séparées)
- L'étiquette de boot affiche le nom Roudix + la version de la release NixOS
- Secure Boot optionnel (`roudix.boot.secureBoot.enable`, Limine signé avec sbctl) et entrée de boot « NixOS EAC » séparée pour Easy Anti-Cheat Linux v2 (`roudix.boot.eac.enable`) — tout est désactivé par défaut, voir [secure-boot-eac.md](secure-boot-eac.md) (en anglais)

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
- Client Steam modifié [Millennium](https://github.com/SteamClientHomebrew/Millennium) en option (thèmes + plugins) — désactivé par défaut, à activer avec `roudix.gaming.steam.millennium.enable = true` (ou depuis l'installeur). Mod non officiel ; le correctif de sandbox `game-performance` et les outils de compatibilité Proton continuent de fonctionner, et repasser à `false` rétablit Steam standard
- Mode Gaming façon console en option : `roudix.gaming.gamescopeSession.enable` ajoute une session « Steam (Gaming Mode) » à l'écran de connexion (Steam Big Picture dans gamescope, VRR/HDR/MangoApp, fréquence de l'écran détectée au lancement). « Passer au bureau » dans Steam ouvre ton bureau, et l'app « Return to Gaming Mode » revient au jeu sans repasser par l'écran de connexion. Basé sur GLF-OS ; niri, umbriel, GNOME, KDE, Hyprland et MangoWC
- Decky Loader (plugins Steam) en option via `roudix.gaming.gamescopeSession.decky.enable`, récupéré via l'input flake Jovian-NixOS (`nix flake update jovian` pour le mettre à jour, aucun sha à maintenir à la main) ; aucun cache binaire, donc compilé localement au premier rebuild

## Bureau (Niri)

- Compositeur Wayland en tuilage défilant Niri — fourni via [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), `niri-unstable` par défaut, avec le cache binaire `niri-epireyn.cachix.org` pré-configuré
- Config native en Nix (`programs.niri.settings`), découpée par thème (général, animations, input, layout, sorties, raccourcis, règles) et validée au build via `niri validate` — une config cassée fait échouer le build plutôt que le compositeur au login
- La synchronisation de thème en direct Noctalia/DMS (couleurs générées par matugen/DMS, alt-tab, flou) est préservée en ajoutant un `include` à la config générée plutôt qu'en la figeant statiquement
- Shell moderne Noctalia (v5)
- xdg-desktop-portal-gnome + gtk (portails screencast + bureau à distance configurés)
- Curseur Bibata Modern Ice (24 px)
- adw-gtk3 + icônes Papirus + Papirus Folders
- Element Desktop avec gnome-libsecret / kwallet6 (détecté automatiquement selon l'environnement)
- Agent Polkit GNOME
- Écran de connexion : Noctalia Greeter (shell par défaut) ou Greeter DMS (greetd) avec le shell DMS

## Bureau (MangoWC)

- Compositeur Wayland MangoWC
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Curseur Bibata Modern Ice (24 px)
- Agent Polkit GNOME
- Écran de connexion : Noctalia Greeter avec Noctalia, Ly avec les autres shells
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
- Support du scratchpad : un pool générique pour n'importe quelle fenêtre
  (déplacer/basculer/restaurer), plus un scratchpad nommé par app
  (Discord/Element/Telegram/Spotify), activable via
  `roudix.mangowc.scratchpadApps` — chacun avec sa propre touche

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
- Démon de fond d'écran awww
- Captures d'écran avec grim + slurp + satty (annotation) — 3 raccourcis

## Bureau (GNOME)

- GNOME (suit la branche nixos-unstable)
- Ensemble d'extensions sélectionné (flou, tuilage, vitals, arcmenu...) — activées via dconf
- ArcMenu avec le logo Roudix comme icône du bouton menu
- Débloatage via `environment.gnome.excludePackages`
- Thème d'icônes Papirus-Roudix (Papirus-Dark avec dossiers aux couleurs de Roudix — voir `roudix.iconTheme`)
- Thème GTK adw-gtk3-dark (mode sombre par défaut)
- Curseur Bibata Modern Ice (24 px)
- Fond d'écran Roudix (clair/sombre selon le thème système)
- `color-scheme = prefer-dark` appliqué via dconf
- Réglages d'extensions (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) pré-configurés via `modules/home/desktop/gnome/_extensions.nix`
- Ajouter/retirer des extensions sans toucher aux fichiers principaux via `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Fond d'écran, thème, icônes, curseur personnalisables dans `modules/home/local.nix`

## Bureau (KDE)

- KDE Plasma 6 avec plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect activé
- xdg-desktop-portal-kde
- Thème d'icônes Papirus-Roudix (Papirus-Dark avec dossiers aux couleurs de Roudix — voir `roudix.iconTheme`)
- Look & feel Breeze Dark + jeu de couleurs
- Fond d'écran Roudix Dark sur l'écran de connexion et le bureau
- Paquets sélectionnés : partitionmanager, kcalc, digikam, vlc...
- Débloatage (Discover exclu)
- Fond d'écran, panneaux, thème d'icônes personnalisables dans `modules/home/local.nix`

## Bureau (Cinnamon)

- Cinnamon avec session X11 + LightDM (slick-greeter) — bureau classique, adapté aux machines anciennes
- Fond d'écran Roudix Kitsune sur le bureau et l'écran de connexion (modifiable avec `roudix-lightdm-wallpaper`)
- Logo Roudix comme icône de menu ; navigateur par défaut, Nemo, Roudix Store et Paramètres épinglés dans le panneau (`roudix.desktop.cinnamon.pinnedApps`)
- Icônes Papirus-Roudix, thème sombre pour les apps GTK4/libadwaita
- Ce sont des valeurs par défaut : elles n'écrasent jamais vos changements

## Bureau (COSMIC)

- COSMIC (System76) avec cosmic-comp + cosmic-greeter, fond d'écran Roudix Kitsune
- Palette Roudix comme thème natif de COSMIC (`assets/cosmic/`, générée depuis `assets/palette/Roudix.json`)
- Dock avec vos navigateurs, COSMIC Files, terminal, Roudix Store et Paramètres ; apps Roudix regroupées dans un dossier **Roudix** de la bibliothèque d'apps
- Disposition clavier reprise de `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions`
- COSMIC Store non installé (Roudix Store le remplace) ; `system76-scheduler` désactivé par défaut (SCX)

## Musique

À choisir via `roudix.musicPlayer` — `"spotify"` (défaut), `"ytmdesktop"`,
`"sonora"` ou `"none"`.

- `"spotify"` — Spotify patché avec Spicetify. Thème local, "colorful" par
  défaut (ou "comfy"), plus extensions adblock + masquage des podcasts —
  voir options ci-dessous.
- `"ytmdesktop"` — YouTube Music Desktop App (client YouTube Music non
  officiel, basé sur Electron).
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora), un client natif
  (Rust/GPUI) pour Spotify, YouTube Music, Apple Music, Deezer et
  Subsonic dans une seule app. L'option `roudix.sonora.provider` choisit le
  fournisseur sur lequel il démarre (`"youtube"` = YouTube Music). Il ne
  contourne pas les abonnements : si un service en exige un, Sonora aussi.

## Apps communes optionnelles

GIMP, Inkscape, SongRec et EasyEffects (+ rnnoise-plugin) sont installés par
défaut mais chacun est débrayable individuellement via
`roudix.apps.<nom>.enable` (`gimp`, `inkscape`, `songrec`, `easyeffects`).

Signal et ZapZap (client WhatsApp non officiel, à l'allure native) n'ont pas
de véritable alternative entre lesquelles switcher : ce sont de simples
booléens opt-in, désactivés par défaut — `roudix.apps.signal.enable` et
`roudix.apps.zapzap.enable`.

Fluxer, une alternative auto-hébergeable à Discord, est le même genre de
booléen opt-in : `roudix.apps.fluxer.enable`. Il n'est pas encore dans
nixpkgs, donc il vient directement du paquet prébuilt `fluxer-desktop` de
l'input flake `nix-gaming-edge`. Volontairement indépendant de
`roudix.discord` et de `roudix.gaming.enable` — rien n'empêche de vouloir
Discord et Fluxer en même temps, ou Fluxer sans setup gaming du tout.

Un client mail et un gestionnaire de mots de passe sont aussi disponibles,
opt-in (désactivés par défaut) : `roudix.mailClient` — `"thunderbird"`
(complet), `"betterbird"` (fork de Thunderbird peaufiné, tiré de l'input
flake [betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) —
pas encore dans nixpkgs) ou `"geary"` (client léger GNOME) ;
`roudix.passwordManager` —
`"bitwarden"` (synchronisé), `"keepassxc"` (coffre local, hors-ligne) ou
`"protonpass"` (synchronisé, compte Proton).

Également disponible, désactivé par défaut : un client torrent via
`roudix.torrentClient` — `"qbittorrent"` (complet, basé sur Qt),
`"fragments"` (client GNOME/libadwaita minimaliste), `"deluge"`
(basé sur des plugins) ou `"none"` (défaut).

## Spicetify

- Thème : `roudix.spicetify.theme` — `"colorful"` (défaut, sanoojes/spicetify-colorful) ou `"comfy"` (thème Comfy fourni)
- Color scheme : `roudix.spicetify.colorScheme` — `null` (défaut) utilise le défaut du thème ("noctalia" pour colorful, "Comfy" pour comfy)
- Extensions débrayables individuellement : `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (activées par défaut)
- App Marketplace : `roudix.spicetify.marketplace.enable` (activée par défaut)

## Navigateur

- Liste de navigateurs configurable via l'option `roudix.browsers` (aussi `brave-beta`, `brave-nightly`, `brave-origin*`, `ungoogled-chromium`, `google-chrome`, `microsoft-edge`)
- Supporte `brave`, `helium` (via x13-me/helium-nix, avec le patch DRM — la lecture Widevine est branchée automatiquement via `modules/home/apps/browser/helium-widevine.nix` quand `helium` est sélectionné), `vivaldi` (avec les codecs ffmpeg), `firefox`, `librewolf`, `chromium`, ou `[]` pour aucun
- Zen Browser disponible séparément via `roudix.zen.enable = true` (désactivé par défaut) ; canal sélectionnable via `roudix.zen.variant` — `"twilight"` (défaut) ou `"beta"`

## Autre

- Discord sélectionnable via `roudix.discord` — `"vencord"` (client patché, défaut), `"vanilla"` (non patché) ou `"none"` (non installé)
- Telegram sélectionnable via `roudix.telegram` — `"telegram"` (client officiel Telegram Desktop), `"ayugram"` (fork non-officiel : mode fantôme, anti-suppression, historique local des messages...) ou `"none"` (défaut, non installé)
- Éditeur de code sélectionnable via `roudix.editor` — `"zed"` (défaut), `"vscode"`, `"neovim"` ou `"none"` (gère le tien, ex : AppImage/Flatpak)
- Disposition clavier graphique (Wayland) via `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, ex : `"be"` / `"intl"`) — indépendant de `console.keyMap`, qui ne couvre que la TTY avant le lancement de la session graphique ; sans effet sur GNOME/KDE, qui gèrent leur propre disposition
- Pile trousseau + xdg-desktop-portal pour les compositeurs "bruts" (Niri, Hyprland, MangoWC, Umbriel) sélectionnable via `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, défaut) ou `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent, et les apps GNOME remplacées par Kate / Gwenview / KDE Partition Manager / Dolphin ; adw-gtk3, nwg-look, qt6ct et gvfs sont conservés pour que les apps GTK restent thémées) ; sans effet sur les sessions GNOME/KDE, qui gardent leur propre pile native
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
- Lecteur vidéo sélectionnable via `roudix.videoPlayer` — `"vlc"` (support de formats le plus large, défaut), `"clapper"` (lecteur GTK4 moderne), `"mpv"` (+ yt-dlp, minimaliste/streaming), `"celluloid"` (interface GTK pour mpv) ou `"none"` ; s'applique sur tous les bureaux (auparavant Clapper était codé en dur sur les compositeurs bruts uniquement, avec un toggle mpv séparé indépendant du DE)
- Support AppImage activé via `modules/system/packaging/appimage.nix`
- Roudix Firewall (`roudix-firewall`) : ports, plages et interfaces de confiance, écrits dans `hosts/<hôte>/firewall.local.nix` (ignoré par git)
- Waydroid (conteneur Android) — optionnel, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (optionnel, `roudix.virtualization.enable`)
- vm-curator (optionnel, `roudix.virtualization.vmCurator.enable`) — TUI Rust alternative à virt-manager, pilote QEMU directement (sans libvirt), avec accélération 3D et GPU passthrough ; activable indépendamment ou en plus de la stack libvirt
- Module d'optimisations invité VM (partage du presse-papiers, redimensionnement auto, agent QEMU, Spice)

## Autres options

D'autres options `roudix.*` utilisables dans `local.nix` (voir leur description dans `modules/`) : `roudix.zen.tweaks.*` et `roudix.firefox.tweaks.*` (préférences vie privée/performance, profil optionnel), `roudix.umbriel.effects` (effets shader), `roudix.gaming.gamescopeSession.hdr.enable`, `roudix.laptop`, `roudix.undervolt.only-amd.enable`, `roudix.tuning`, `roudix.palette`, `roudix.gitwatch`, `roudix.distrobox.enable`, `roudix.podman.enable`, `roudix.terminal` (`ghostty`, `kitty`, `alacritty`, `foot`, `wezterm`, `ptyxis`, `konsole`) et `roudix.fileManager`.

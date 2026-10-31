[English](README.md) · [Français](README.fr.md) · **Español** · [Português (Brasil)](README.pt_BR.md) · [Русский](README.ru.md) · [简体中文](README.zh_CN.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### Configuración de NixOS (Unstable) — Varios compositores Wayland (hyprland, niri, mangowc y umbriel) · Gnome y KDE · Kernel CachyOS

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| Vista previa |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Presentación de Roudix: Umbriel, GNOME y KDE Plasma" width="900"/> |

<sub>Personalización propia — la tuya se verá distinta según tu configuración 👀</sub><br/>
<sub>Los compositores Wayland quedan a tu criterio para personalizarlos: Roudix solo incluye la configuración por defecto de Noctalia, Dux Shell y (solo Hyprland) Caelestia.</sub>

</div>

---

## Hardware

| Componente | Modelo |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## Stack

| Capa | Elección |
|-------|--------|
| SO | Roudix (NixOS unstable) |
| Kernel | CachyOS (elige tu variante en [Funcionalidades](docs/features.md) o en [Instalación](docs/installation.es.md)) |
| Bootloader | Limine (por defecto) · systemd-boot |
| Compositor | Niri (mosaico con desplazamiento) · Hyprland (mosaico dinámico) · MangoWC · Umbriel (mosaico con desplazamiento, nativo de Noctalia) |
| Shell gráfico | Noctalia · Dux Shell · Caelestia |
| Entorno de escritorio | KDE Plasma · Gnome |
| Gestor de inicio de sesión | DMS Greeter (solo Dms) · Noctalia Greeter (solo noctalia) · plasma-login-manager (solo KDE) · GDM (solo Gnome) |
| Terminal | Configurable (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| Shell | Fish · Bash |
| Navegador | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| Gestor de archivos | Configurable (Nautilus, Thunar, Dolphin, Nemo) |
| Editor | Configurable (Zed, VS Code, Neovim, ninguno) |
| Chat | Discord (Vencord · vanilla · ninguno) + Matrix (Element · Cinny · ninguno) |
| Música | Configurable (Spotify + Spicetify, YouTube Music Desktop, ninguno) |

---

## Documentación

| | |
|-|-|
| 🖥️ [Escritorio y shells](docs/desktop.md) | Cambia de compositor y de shell gráfico, ajustes personales (Niri, Hyprland, GNOME, KDE) |
| ⚡ [Alias y funciones](docs/aliases.es.md) | Todos los alias y funciones de shell — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [Instalación](docs/installation.es.md) | Guía de instalación automatizada y manual |
| ✨ [Funcionalidades](docs/features.md) | Lista completa de funcionalidades por entorno de escritorio |
| 🔄 [Actualización automática](docs/autoupdate.es.md) | Configuración del git pull + reconstrucción automáticos |

---

## Estructura

```
roudix/
├── roudix-installer.sh              # Instalador basado en Bash
├── flake.nix                        # Inputs y outputs
├── flake.lock
├── docs/                            # Documentación
│   ├── desktop.md                   # Entornos de escritorio y shells gráficos
│   ├── aliases.md                   # Alias y funciones de shell
│   ├── installation.md              # Guía de instalación
│   ├── features.md                  # Lista de funcionalidades
│   ├── features.fr.md               # Lista de funcionalidades (francés)
│   └── autoupdate.md                # Configuración de la actualización automática
│
├── hosts/
│   └── roudix/                      # Un solo host — el DE se elige con roudix.desktop.type
│       ├── configuration.nix
│       ├── username.nix             # en gitignore — tu nombre de usuario (ver instalación)
│       ├── local.nix                # en gitignore — tus ajustes personales del sistema
│       ├── local.nix.example        # cópialo a local.nix para empezar
│       └── hardware-configuration.nix
│
├── dotfiles/                        # Archivos de configuración en bruto gestionados por Home Manager
│   ├── easyeffects/                 # Presets de EasyEffects
│   ├── fastfetch/
│   │   └── roudix.txt               # Logo ASCII de Roudix por defecto para fastfetch
│   # niri/, niri-dms/ eliminados — la config de niri es ahora totalmente
│   # nativa de Nix (ver modules/home/desktop/niri/ más abajo).
│   ├── hyprland/                    # Config de Hyprland (Lua) — un solo árbol para todos los shells gráficos
│   │   ├── hyprland.lua             # Punto de entrada: carga los módulos de config/
│   │   └── config/
│   │       ├── shell.lua            # Elige el shell (noctalia / dms / caelestia) según ROUDIX_HYPR_SHELL
│   │       ├── shells/              # Atajos e integración por shell (noctalia.lua, dms.lua, caelestia.lua)
│   │       ├── binds/common.lua     # Atajos compartidos por todos los shells
│   │       ├── rules/               # Reglas de ventanas (common.lua, apps.lua, gaming.lua)
│   │       ├── ws.lua               # Tabla de workspaces compartida (usada por workspaces, binds y reglas)
│   │       ├── workspaces.lua       # Reglas de workspaces
│   │       ├── monitors.lua / input.lua / layout.lua / decorations.lua / animations.lua
│   │       ├── defaults.lua / colors.lua / environment.lua / autostart.lua / misc.lua
│   │       └── nix-noctalia.lua     # Carga el tema en vivo de Noctalia (generado por matugen)
│   │   # config/nix-plugins.lua y config/nix-apps.lua los genera Nix (no están en el repo)
│   └── perso/                       # Configuración personal (en gitignore)
│
├── pkgs/
│   ├── roudix-branding              # Paquete de branding de Roudix
│   ├── roudix-kernel-switcher       # Paquete de la GUI Roudix Kernel Switcher
│   ├── roudix-switcher/             # GUI de ajustes de Roudix (escritorio, gaming, editor, terminal, navegador, shell, gestor de archivos, chat, sistema, integración)
│   └──   roudix-scheduler-switcher    # Paquete de la GUI Scheduler Switcher
│
└── modules/
    ├── system/                      # Módulos de NixOS a nivel de sistema
    │   ├── desktop/                 # Módulos de entorno de escritorio (nivel NixOS)
    │   │   ├── default.nix          # Opciones de escritorio (roudix.desktop.type + roudix.desktop.shell)
    │   │   └── niri.nix / hyprland.nix / gnome.nix / kde.nix / mangowc.nix / umbriel.nix
    │   │
    │   ├── boot/                    # Bootloader, kernel y CPU
    │   │   ├── boot.nix             # Limine/systemd-boot + entradas multi-SO
    │   │   ├── boot.local.nix       # en gitignore — tus entradas de arranque personales
    │   │   ├── boot.local.nix.example
    │   │   ├── kernel.nix           # Selección de variante de kernel — variantes de CachyOS + nixpkgs simple
    │   │   ├── cpu.nix              # Microcódigo Intel/AMD + módulos i2c
    │   │   └── bootloader/          # Recurso de fondo de pantalla de Limine
    │   │
    │   ├── apps/                    # Módulos de selección de apps (una opción roudix.* cada uno)
    │   │   ├── apps.nix / appimage.nix / flatpak.nix / browser.nix / discord.nix
    │   │   ├── telegram.nix / matrix.nix / mail-client.nix / music-player.nix
    │   │   ├── video-player.nix / torrent-client.nix / password-manager.nix
    │   │   └── filemanager.nix / editor.nix / terminal.nix / spicetify.nix / content-creation.nix
    │   │
    │   ├── virtualization/          # QEMU/KVM, contenedores, ajustes de invitado VM, Waydroid
    │   │   └── virtualization.nix / containers.nix / vm-guest.nix / waydroid.nix
    │   │
    │   ├── rgb/                     # Enrutado del controlador RGB
    │   │   ├── default.nix          # Opción roudix.rgb (openlinkhub / openrgb / none)
    │   │   └── openlinkhub.nix / openrgb.nix
    │   │
    │   ├── gaming/                  # Steam, Gamescope, ananicy-cpp, tuned-adm, planificadores SCX
    │   │   └── gaming.nix / scx.nix
    │   │
    │   ├── gpu/                     # Configuración de GPU (AMD/NVIDIA/Intel/VM + mesa-git)
    │   │
    │   ├── autoupdate.nix       # Git pull automático + reconstrucción al cambiar la configuración
    │   ├── binary-caches.nix    # Cachés binarias de Nix (substituters + claves de confianza)
    │   ├── common.nix           # Configuración de sistema compartida (todos los hosts)
    │   ├── desktop-integration.nix  # Llavero + stack xdg-desktop-portal para compositores sin entorno
    │   ├── environment.nix      # Variables de entorno
    │   ├── fstrim.nix           # fstrim para SSD/NVMe
    │   ├── hosts-gta.nix        # Bloqueo de hosts de BattlEye (arreglo de GTA, opcional)
    │   ├── icon-theme.nix       # Selección del tema de iconos a nivel de sistema
    │   ├── keyboard.nix         # Distribución/variante de teclado gráfica (Wayland)
    │   ├── pipewire.nix         # Audio PipeWire + supresión de ruido con rnnoise
    │   ├── shell.nix            # Shell por defecto (fish/bash)
    │   ├── update.nix           # Configuración de actualización del flake
    │   ├── roudix-update.nix    # Comando `update` (pull + reconstrucción + Flatpaks), script en roudix-update.sh, completado de shell en completions/
    │   └── version.nix          # Branding del SO Roudix (os-release, distroName)
    │   # terminal/gestor de archivos: elige tu favorito mediante local.nix en hosts/roudix/
    │
    └── home/                        # Módulos de Home Manager a nivel de usuario
        ├── common.nix               # Config de home compartida (todos los usuarios y DE)
        ├── bash.nix                 # Config del shell Bash + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + inicio automático en fish
        ├── fish.nix                 # Shell Fish + alias + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # Paquetes de gaming del usuario (proton, mangohud...)
        ├── git.nix                  # Configuración de Git
        ├── mangohud.nix             # Overlay MangoHud (compartido entre DE)
        ├── papirus-icon.nix         # Tema de iconos Papirus (compartido entre DE)
        ├── papirus-folders.nix      # Configuración del color de carpetas de Papirus (compartida)
        ├── tela-icon.nix            # Tema de iconos Tela (compartido entre DE)
        ├── spicetify.nix            # Spotify + Spicetify (tema Comfy)
        ├── ssh.nix                  # SSH + GitHub
        ├── shell-modules.nix        # Imports de módulos de shell compartidos (noctalia, dms, caelestia)
        └── desktop/                 # Una carpeta por DE — lado Home Manager, replica modules/system/desktop/
            ├── default.nix          # Importa los seis incondicionalmente (cada uno está protegido internamente con lib.mkIf)
            ├── gnome/
            │   ├── default.nix      # Fondo de pantalla, tema, iconos, cursor
            │   └── _extensions.nix  # Extensiones de GNOME — paquetes, UUID activados, ajustes de dconf
            ├── kde/default.nix      # Config de plasma-manager (fondo, paneles, pantalla de bloqueo)
            ├── hyprland/default.nix # Según el shell (noctalia/dms/caelestia), plugins, paquetes
            ├── mangowc/default.nix  # config.conf/apps.conf de mango generados, paquetes
            ├── niri/                # programs.niri.settings, dividido por tema, según el shell
            │   ├── default.nix      # ensambla los ajustes, include del tema en vivo, paquetes
            │   ├── _general.nix     # entorno, autoarranque, cursor (según el shell)
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # salidas + workspaces con nombre
            │   ├── _ws.nix          # constantes de glifos de iconos de workspace compartidas
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # añade el `include` del tema en vivo a la config renderizada de niri-flake
            └── umbriel/             # programs.umbriel.settings, dividido por tema (solo Noctalia)
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # carga noctalia.toml (el include de tema en vivo nativo de Umbriel)
```

---

## Inputs del flake

| Input | Origen |
|-------|--------|
| nixpkgs | [nixos-unstable](https://github.com/NixOS/nixpkgs/tree/nixos-unstable) |
| nixpkgs-stable | [nixos-26.05](https://github.com/NixOS/nixpkgs/tree/nixos-26.05) |
| niri | [epireyn/niri-flake](https://github.com/epireyn/niri-flake) |
| home-manager | [nix-community/home-manager](https://github.com/nix-community/home-manager) |
| noctalia | [noctalia-dev/noctalia](https://github.com/noctalia-dev/noctalia) |
| umbriel | [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) |
| caelestia-shell | [caelestia-dots/shell](https://github.com/caelestia-dots/shell) |
| dms | [duxlabs-dev/dux-shell](https://github.com/duxlabs-dev/dux-shell) |
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
---

## Ver también

| Proyecto | Descripción |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | Distro gaming basada en NixOS de Gaming Linux FR |

---

## Dotfiles personales

Los archivos de configuración personales viven en `dotfiles/perso/` — están en el gitignore (salvo `dotfiles/perso/README.md`) y ni `git pull` ni la actualización automática los tocan nunca.

Consulta [`dotfiles/perso/README.md`](dotfiles/perso/README.md) para ver la estructura y el uso.

Para ajustes a nivel de compositor (monitores, atajos, espaciados…), usa en su lugar los archivos de ajustes de usuario generados: los gestiona home-manager y están a salvo de `git pull`. Consulta [Escritorio y shells](docs/desktop.md#personal-compositor-overrides) para más detalles.

## Desarrollo

```bash
nix develop     # shell de desarrollo: just, ruff, statix, deadnix, shellcheck, gettext
just            # lista las tareas
just ci         # todo lo que comprueba la CI (evalúa cada host, lint, Python, traducciones)
```

El instalador se traduce con gettext — consulta [Instalador › Traducciones](iso/roudix-installer/README.md#traductions).

## Licencia
   MIT — ver [LICENSE](LICENSE). La Roudix Store es GPL-2.0-only y algunos
   archivos de terceros conservan sus propias licencias: ver [THIRD_PARTY.md](THIRD_PARTY.md).

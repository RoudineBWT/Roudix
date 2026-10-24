[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português (Brasil)](README.pt_BR.md) · **Русский** · [简体中文](README.zh_CN.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### Конфигурация NixOS (Unstable) — несколько Wayland-композиторов (hyprland, niri, mangowc и umbriel) · Gnome и KDE · ядро CachyOS

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| Превью |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Слайд-шоу Roudix: Umbriel, GNOME и KDE Plasma" width="900"/> |

<sub>Личная настройка — у вас всё будет выглядеть иначе, в зависимости от вашей конфигурации 👀</sub><br/>
<sub>Настройка Wayland-композиторов остаётся за вами: Roudix поставляет только конфигурацию по умолчанию для Noctalia, DankMaterialShell и (только Hyprland) Caelestia.</sub>

</div>

---

## Оборудование

| Компонент | Модель |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## Стек

| Слой | Выбор |
|-------|--------|
| ОС | Roudix (NixOS unstable) |
| Kernel | CachyOS (выберите вариант ядра в разделе [Возможности](docs/features.md) или [Установка](docs/installation.ru.md)) |
| Bootloader | Limine (по умолчанию) · systemd-boot |
| Compositor | Niri (прокручиваемая мозаика) · Hyprland (динамическая мозаика) · MangoWC · Umbriel (прокручиваемая мозаика, нативный для Noctalia) |
| Графическая оболочка | Noctalia · DankMaterialShell · Caelestia |
| Окружение рабочего стола | KDE Plasma · Gnome |
| Менеджер входа | DMS Greeter (только Dms) · Noctalia Greeter (только noctalia) · plasma-login-manager (только KDE) · GDM (только Gnome) |
| Терминал | Настраивается (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| Оболочка | Fish · Bash |
| Браузер | Настраивается (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| Файловый менеджер | Настраивается (Nautilus, Thunar, Dolphin, Nemo) |
| Редактор | Настраивается (Zed, VS Code, Neovim, нет) |
| Chat | Discord (Vencord · vanilla · нет) + Matrix (Element · Cinny · нет) |
| Музыка | Настраивается (Spotify + Spicetify, YouTube Music Desktop, нет) |

---

## Документация

| | |
|-|-|
| 🖥️ [Рабочий стол и оболочки](docs/desktop.md) | Смена композиторов и графических оболочек, личные настройки (Niri, Hyprland, GNOME, KDE) |
| ⚡ [Алиасы и функции](docs/aliases.ru.md) | Все алиасы и функции оболочки — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [Установка](docs/installation.ru.md) | Руководство по автоматической и ручной установке |
| ✨ [Возможности](docs/features.md) | Полный список возможностей по окружениям рабочего стола |
| 🔄 [Автообновление](docs/autoupdate.ru.md) | Настройка автоматического git pull + пересборки |

---

## Структура

```
roudix/
├── roudix-installer.sh              # Установщик на Bash
├── flake.nix                        # Входы и выходы
├── flake.lock
├── docs/                            # Документация
│   ├── desktop.md                   # Окружения рабочего стола и графические оболочки
│   ├── aliases.md                   # Алиасы и функции оболочки
│   ├── installation.md              # Руководство по установке
│   ├── features.md                  # Список возможностей
│   ├── features.fr.md               # Список возможностей (на французском)
│   └── autoupdate.md                # Настройка автообновления
│
├── hosts/
│   └── roudix/                      # Один хост — окружение выбирается через roudix.desktop.type
│       ├── configuration.nix
│       ├── username.nix             # в gitignore — ваше имя пользователя (см. установку)
│       ├── local.nix                # в gitignore — ваши личные настройки системы
│       ├── local.nix.example        # скопируйте в local.nix, чтобы начать
│       └── hardware-configuration.nix
│
├── dotfiles/                        # Исходные конфигурационные файлы под управлением Home Manager
│   ├── easyeffects/                 # Пресеты EasyEffects
│   ├── fastfetch/
│   │   └── roudix.txt               # ASCII-логотип Roudix по умолчанию для fastfetch
│   # niri/, niri-dms/ удалены — конфигурация niri теперь полностью
│   # написана на Nix (см. modules/home/desktop/niri/ ниже).
│   ├── hyprland/                    # Конфигурация Hyprland (Lua) — одно дерево для всех графических оболочек
│   │   ├── hyprland.lua             # Точка входа: загружает модули из config/
│   │   └── config/
│   │       ├── shell.lua            # Выбирает оболочку (noctalia / dms / caelestia) по ROUDIX_HYPR_SHELL
│   │       ├── shells/              # Привязки и интеграция для каждой оболочки (noctalia.lua, dms.lua, caelestia.lua)
│   │       ├── binds/common.lua     # Привязки, общие для всех оболочек
│   │       ├── rules/               # Правила окон (common.lua, apps.lua, gaming.lua)
│   │       ├── ws.lua               # Общая таблица рабочих пространств (используется workspaces, binds и rules)
│   │       ├── workspaces.lua       # Правила рабочих пространств
│   │       ├── monitors.lua / input.lua / layout.lua / decorations.lua / animations.lua
│   │       ├── defaults.lua / colors.lua / environment.lua / autostart.lua / misc.lua
│   │       └── nix-noctalia.lua     # Загружает живую тему Noctalia (создаётся matugen)
│   │   # config/nix-plugins.lua и config/nix-apps.lua создаются Nix (в репозитории их нет)
│   └── perso/                       # Личная конфигурация (в gitignore)
│
├── pkgs/
│   ├── roudix-branding              # Пакет брендинга Roudix
│   ├── roudix-kernel-switcher       # Пакет GUI Roudix Kernel Switcher
│   ├── roudix-switcher/             # GUI настроек Roudix (рабочий стол, игры, редактор, терминал, браузер, оболочка, файловый менеджер, чат, система, интеграция)
│   └──   roudix-scheduler-switcher    # Пакет GUI Scheduler Switcher
│
└── modules/
    ├── system/                      # Модули NixOS уровня системы
    │   ├── desktop/                 # Модули окружений рабочего стола (уровень NixOS)
    │   │   ├── default.nix          # Параметры рабочего стола (roudix.desktop.type + roudix.desktop.shell)
    │   │   └── niri.nix / hyprland.nix / gnome.nix / kde.nix / mangowc.nix / umbriel.nix
    │   │
    │   ├── boot/                    # Загрузчик, ядро и CPU
    │   │   ├── boot.nix             # Limine/systemd-boot + записи для нескольких ОС
    │   │   ├── boot.local.nix       # в gitignore — ваши личные записи загрузки
    │   │   ├── boot.local.nix.example
    │   │   ├── kernel.nix           # Выбор варианта ядра — варианты CachyOS + обычное ядро nixpkgs
    │   │   ├── cpu.nix              # Микрокод Intel/AMD + модули i2c
    │   │   └── bootloader/          # Ресурс обоев Limine
    │   │
    │   ├── apps/                    # Модули выбора приложений (по одному параметру roudix.* на каждый)
    │   │   ├── apps.nix / appimage.nix / flatpak.nix / browser.nix / discord.nix
    │   │   ├── telegram.nix / matrix.nix / mail-client.nix / music-player.nix
    │   │   ├── video-player.nix / torrent-client.nix / password-manager.nix
    │   │   └── filemanager.nix / editor.nix / terminal.nix / spicetify.nix / content-creation.nix
    │   │
    │   ├── virtualization/          # QEMU/KVM, контейнеры, настройки гостя ВМ, Waydroid
    │   │   └── virtualization.nix / containers.nix / vm-guest.nix / waydroid.nix
    │   │
    │   ├── rgb/                     # Маршрутизация RGB-контроллера
    │   │   ├── default.nix          # Параметр roudix.rgb (openlinkhub / openrgb / none)
    │   │   └── openlinkhub.nix / openrgb.nix
    │   │
    │   ├── gaming/                  # Steam, Gamescope, ananicy-cpp, tuned-adm, планировщики SCX
    │   │   └── gaming.nix / scx.nix
    │   │
    │   ├── gpu/                     # Конфигурация GPU (AMD/NVIDIA/Intel/VM + mesa-git)
    │   │
    │   ├── autoupdate.nix       # Автоматический git pull + пересборка при изменении конфигурации
    │   ├── binary-caches.nix    # Бинарные кэши Nix (substituters + доверенные ключи)
    │   ├── common.nix           # Общая конфигурация системы (все хосты)
    │   ├── desktop-integration.nix  # Связка ключей + стек xdg-desktop-portal для «голых» композиторов
    │   ├── environment.nix      # Переменные окружения
    │   ├── fstrim.nix           # fstrim для SSD/NVMe
    │   ├── hosts-gta.nix        # Блокировка хостов BattlEye (исправление GTA, по желанию)
    │   ├── icon-theme.nix       # Выбор темы значков для всей системы
    │   ├── keyboard.nix         # Раскладка/вариант графической клавиатуры (Wayland)
    │   ├── pipewire.nix         # Звук PipeWire + шумоподавление rnnoise
    │   ├── shell.nix            # Оболочка по умолчанию (fish/bash)
    │   ├── update.nix           # Настройка обновления flake
    │   ├── roudix-update.nix    # Команда `update` (pull + пересборка + Flatpak), скрипт в roudix-update.sh, автодополнения оболочки в completions/
    │   └── version.nix          # Брендинг ОС Roudix (os-release, distroName)
    │   # терминал/файловый менеджер: выберите любимый через local.nix в hosts/roudix/
    │
    └── home/                        # Модули Home Manager уровня пользователя
        ├── common.nix               # Общая конфигурация home (все пользователи и окружения)
        ├── bash.nix                 # Конфигурация оболочки Bash + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + автозапуск в fish
        ├── fish.nix                 # Оболочка Fish + алиасы + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # Игровые пакеты пользователя (proton, mangohud...)
        ├── git.nix                  # Конфигурация Git
        ├── mangohud.nix             # Оверлей MangoHud (общий для всех окружений)
        ├── papirus-icon.nix         # Тема значков Papirus (общая для всех окружений)
        ├── papirus-folders.nix      # Настройка цвета папок Papirus (общая)
        ├── tela-icon.nix            # Тема значков Tela (общая для всех окружений)
        ├── spicetify.nix            # Spotify + Spicetify (тема Comfy)
        ├── ssh.nix                  # SSH + GitHub
        ├── shell-modules.nix        # Импорты общих модулей оболочек (noctalia, dms, caelestia)
        └── desktop/                 # Одна папка на окружение — сторона Home Manager, повторяет modules/system/desktop/
            ├── default.nix          # Импортирует все шесть безусловно (каждый внутри защищён lib.mkIf)
            ├── gnome/
            │   ├── default.nix      # Обои, тема, значки, курсор
            │   └── _extensions.nix  # Расширения GNOME — пакеты, включённые UUID, настройки dconf
            ├── kde/default.nix      # Конфигурация plasma-manager (обои, панели, экран блокировки)
            ├── hyprland/default.nix # С учётом оболочки (noctalia/dms/caelestia), плагины, пакеты
            ├── mangowc/default.nix  # Сгенерированные config.conf/apps.conf для mango, пакеты
            ├── niri/                # programs.niri.settings, разбит по темам, с учётом оболочки
            │   ├── default.nix      # собирает настройки, include живой темы, пакеты
            │   ├── _general.nix     # окружение, автозапуск, курсор (с учётом оболочки)
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # выводы + именованные рабочие пространства
            │   ├── _ws.nix          # общие константы глифов значков рабочих пространств
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # добавляет `include` живой темы в конфигурацию, сгенерированную niri-flake
            └── umbriel/             # programs.umbriel.settings, разбит по темам (только Noctalia)
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # загружает noctalia.toml (нативный include живой темы Umbriel)
```

---

## Входы flake

| Вход | Источник |
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
---

## См. также

| Проект | Описание |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | Игровой дистрибутив на базе NixOS от Gaming Linux FR |

---

## Личные dotfiles

Личные конфигурационные файлы лежат в `dotfiles/perso/` — они внесены в gitignore (кроме `dotfiles/perso/README.md`), и `git pull` и автообновление их никогда не затрагивают.

Структуру и использование см. в [`dotfiles/perso/README.md`](dotfiles/perso/README.md).

Для настроек на уровне композитора (мониторы, сочетания клавиш, отступы…) используйте вместо этого сгенерированные пользовательские файлы переопределений — ими управляет home-manager, и они защищены от `git pull`. Подробности см. в [Рабочий стол и оболочки](docs/desktop.md#personal-compositor-overrides).

## Разработка

```bash
nix develop     # dev shell: just, ruff, statix, deadnix, shellcheck, gettext
just            # список задач
just ci         # всё, что проверяет CI (оценка каждого хоста, lint, Python, переводы)
```

Установщик переведён через gettext — см. [Установщик › Переводы](iso/roudix-installer/README.md#traductions).

## Лицензия
   MIT — см. [LICENSE](LICENSE). Roudix Store распространяется под GPL-2.0-only, а некоторые
   сторонние файлы сохраняют собственные лицензии: см. [THIRD_PARTY.md](THIRD_PARTY.md).

[English](installation.md) · [Français](installation.fr.md) · [Español](installation.es.md) · [Português (Brasil)](installation.pt_BR.md) · **Русский** · [简体中文](installation.zh_CN.md) · [हिन्दी](installation.hi.md) · [العربية](installation.ar.md)

# Установка

Запустить Roudix можно тремя способами, в зависимости от вашей отправной точки:

| Ситуация | Что использовать |
|-----------|-----|
| Новая машина, ничего ещё не установлено | **ISO Roudix** — сразу загружается в графический установщик (включая разметку диска) |
| NixOS уже установлена (официальный ISO, установка NixOS из другого дистрибутива, ВМ…) | **`roudix-installer.sh`** — разворачивает flake Roudix поверх вашей существующей установки |
| Вы хотите контролировать каждый шаг, или скрипт не подходит для вашего случая | **Ручная установка** (ниже) |

## Вариант A — ISO Roudix (рекомендуется для чистой установки)

ISO содержит наш собственный графический установщик на GTK4/libadwaita (`roudix-installer`), работающий поверх живой сессии GNOME, и сам занимается разметкой диска через [disko](https://github.com/nix-community/disko) — устанавливать NixOS заранее не нужно.

1. Скачайте свежий ISO: откройте вкладку **Actions** репозитория → workflow **💿 Build Roudix ISO** → запустите его (`workflow_dispatch`), если в списке нет недавней сборки, затем откройте запуск и возьмите ссылку на скачивание из сводки задания (ISO размещён на Cloudflare R2, а не как артефакт GitHub).
2. Запишите его на USB-накопитель (например, `dd`, Ventoy, Rufus…) и загрузитесь с него.
3. Окно установщика открывается автоматически при входе (оно перезапускается через `sudo`: живой сессии нужен root для disko/`nixos-install`). Пройдите страницы: выбор диска, ядро, рабочий стол, браузер, редактор, Discord, игровые приложения, локаль, часовой пояс, раскладка клавиатуры, RGB-контроллер и необязательные модули.
4. После подтверждения он размечает диск (disko), копирует flake Roudix, встроенный в ISO, в `/mnt/etc/nixos` и запускает `nixos-install --flake /mnt/etc/nixos#roudix`.

> **Примечание:** в меню загрузки также есть специализации раскладки клавиатуры (US/BE/FR/DE/CH/UK) — на случай, если клавиатура живой сессии не совпадает с физической; выберите нужную до запуска установщика.

Этот путь полностью заменяет два шага ниже (`roudix-installer.sh` и ручные шаги не нужны) — после перезагрузки переходите к тому, что идёт после установки.

## Вариант B — NixOS уже установлена

Если NixOS уже установлена (через официальный стабильный/unstable ISO или любым другим способом) и вы просто хотите поставить Roudix поверх неё, есть два установщика: графический (из сессии рабочего стола) и bash-скрипт (работает из чистого TTY).

> **Примечание:** сначала установите NixOS с ISO [stable](https://nixos.org/download/) или [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165), затем запустите один из установщиков ниже или выполните ручную установку.

### B1 — Графический установщик (рекомендуется на рабочем столе)

Тот же мастер, что и в ISO, но без страницы выбора диска. Запускайте его из учётной записи, которую хотите сохранить:

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **Ничего не стирается.** Конфигурация попадает в `~/.config/roudix` (существующая папка откладывается в сторону, но никогда не удаляется), затем `nixos-rebuild boot` собирает Roudix и назначает его на следующую загрузку. Ваша текущая система остаётся в меню загрузки.
- **Ваш `/etc/nixos` копируется** в `/var/backups/roudix/nixos-<date>/` вместе с файлом `RESTORE.txt` (предыдущее поколение, загрузчик, `stateVersion` и точные команды для возврата). `hardware-configuration.nix` используется как есть и никогда не перезаписывается.
- **Сначала симуляция.** Кнопка *Симуляция* на странице сводки создаёт конфигурацию во временной папке, проверяет, что каждый параметр записан, и заставляет Nix вычислить всю систему. На вашей машине ничего не изменяется.
- Предупреждения перед началом: мало свободного места в `/boot` (EFI-раздел на 512 МБ быстро заполняется), смена загрузчика, более старый `system.stateVersion`.
- Запрашивает пароль администратора через диалог polkit (нужен агент polkit, то есть любая обычная сессия рабочего стола).

**Как вернуться:** выберите предыдущее поколение в меню загрузки, затем выполните `sudo nixos-rebuild switch --rollback`. Если машина вообще не загружается, `RESTORE.txt` объясняет, как восстановить прежнюю конфигурацию с live-USB.

### B2 — Bash-скрипт (TTY / без графической сессии)

**Скачайте скрипт roudix-installer**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

Установщик всё делает в интерактивном режиме:
- Спрашивает, какую ветку установить и отслеживать (`main` = стабильная, `testing`, `dev`), клонирует её, создаёт `hardware-configuration.nix` и все локальные конфигурационные файлы
- **Автоматически обнаруживает другие ОС** через EFI NVRAM (`efibootmgr`) — искать PARTUUID вручную не нужно
- **Автоматически определяет GPU и CPU** (`lspci` / `/proc/cpuinfo`) — предварительно выбирает их и просит подтверждения
- **Определяет, запущен ли он в ВМ** (`systemd-detect-virt`) — заранее включает режим гостя ВМ и предупреждает, что определение GPU/CPU может быть неточным
- Спрашивает про ядро, рабочий стол, браузер, редактор, Discord, игровые приложения, локаль, часовой пояс, раскладку, RGB-контроллер и необязательные модули
- Собирает и применяет конфигурацию

---

## Вариант C — Ручная установка

> ⚠️ **Внимательно выполните каждый шаг, прежде чем пересобирать.**

### 1. Клонируйте репозиторий

> **Если `git` не установлен** (чистая установка NixOS):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **В остальных случаях:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Задайте имя пользователя

Создайте файл `username.nix` с вашим именем пользователя:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> Этот файл внесён в gitignore — `git pull` никогда его не перезапишет.

### 3. Замените hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Создайте локальные конфигурации

**Никогда не редактируйте `configuration.nix` и `modules/home/common.nix` напрямую** — они перезаписываются при `git pull`.
Вместо этого создайте свои локальные файлы переопределений (все они в gitignore):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp modules/home/local.nix.example modules/home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

Отредактируйте `hosts/roudix/local.nix` под своё оборудование:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "mangowc", "umbriel", "gnome" или "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" или "intel"
  hardware.myCpu      = "intel";              # "intel" или "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # ядро xddxdd — используется при hardware.myGpu != "nvidia"
  hardware.myKernelChaotic = "cachyos";            # ядро Chaotic-Nyx — используется только при hardware.myGpu == "nvidia"
  roudix.boot.bootloader = "limine";          # "limine" или "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" или []
  roudix.zen.enable   = false;                # поставьте true, чтобы дополнительно установить Zen Browser (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub", "openrgb" или "none" — см. ниже
  roudix.mesa.useGit  = false;                # true = mesa-git (экспериментально, сборка может не удаться), false = стабильный nixpkgs
  roudix.matrixClient = "none";               # "element", "cinny" или "none"
  roudix.discord      = "vencord";            # "vencord", "vanilla" или "none"
  roudix.editor       = "zed";                # "zed", "vscode", "neovim" или "none"

  # ── Игровые приложения (по умолчанию все true — отключите ненужные) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── Интеграция с «голым» композитором (только niri/hyprland/mangowc/umbriel) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" или "kde" — связка ключей + стек xdg-desktop-portal; на сессии gnome/kde не влияет

  # ── Локаль / Часовой пояс ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # см. https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # должен совпадать с time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # системная локаль
  console.keyMap                  = "us";              # раскладка клавиатуры консоли — только TTY, до запуска графической сессии

  # ── Раскладка графической клавиатуры (Wayland) — не зависит от console.keyMap ─
  # Не влияет на GNOME/KDE: они управляют раскладкой через собственные службы настроек.
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl", "nodeadkeys", "bepo", "dvorak", "colemak", "" (нет)
}
```

**Варианты RGB-контроллера:**

| Значение | Описание |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — полная поддержка Corsair (iCUE Link, Commander...) |
| `openrgb` | OpenRGB — разные бренды (Razer, ASUS, MSI...) |
| `none` | Без управления RGB |

**RGB-подсветка ОЗУ (только OpenLinkHub):**

Если вы выбрали `openlinkhub`, можно также включить управление RGB для ОЗУ Corsair DDR4/DDR5. Добавьте эти строки в `hosts/roudix/local.nix`:

```nix
roudix.memory.enable = true;                  # включить RGB-подсветку ОЗУ через SMBus
roudix.memory.type   = "ddr5";                # "ddr4" или "ddr5"
roudix.memory.smBus  = "i2c-9";              # узнайте командой: sudo i2cdetect -l (ищите «SMBus»)
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # узнайте командой: sudo dmidecode -t memory | grep 'Part Number'
```

Чтобы найти правильные значения перед их заданием:

```bash
# Установите нужные утилиты, если их нет (чистая установка NixOS)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# Найдите свой SMBus (строка с "SMBus", "i801", "piix4" или "nforce")
sudo i2cdetect -l

# Найдите партномер своей ОЗУ
sudo dmidecode -t memory | grep 'Part Number'
```

> **Примечание:** `roudix.memory.enable` автоматически добавляет `acpi_enforce_resources=lax` в параметры ядра и вносит `spd5118` (DDR5) или `ee1004` (DDR4) в чёрный список, чтобы освободить SMBus. `config.json` OpenLinkHub автоматически исправляется при активации.

**Часто используемые часовые пояса:**

| Часовой пояс | Регион |
|----------|--------|
| `Europe/Brussels` | Бельгия |
| `Europe/Paris` | Франция |
| `Europe/London` | Великобритания |
| `Europe/Berlin` | Германия |
| `Europe/Amsterdam` | Нидерланды |
| `America/New_York` | США (восток) |
| `America/Los_Angeles` | США (запад) |
| `Asia/Tokyo` | Япония |
| `UTC` | Универсальный |

**Часто используемые локали:**

| Локаль | Язык |
|--------|----------|
| `en_US.UTF-8` | English (US) |
| `en_GB.UTF-8` | English (UK) |
| `fr_BE.UTF-8` | Français (Belgique) |
| `fr_FR.UTF-8` | Français (France) |
| `de_DE.UTF-8` | Deutsch |
| `nl_BE.UTF-8` | Nederlands (België) |
| `nl_NL.UTF-8` | Nederlands |
| `es_ES.UTF-8` | Español |
| `pt_BR.UTF-8` | Português (Brasil) |
| `it_IT.UTF-8` | Italiano |
| `ru_RU.UTF-8` | Русский |
| `ja_JP.UTF-8` | 日本語 |
| `zh_CN.UTF-8` | 中文 (简体) |
| `ko_KR.UTF-8` | 한국어 |

**Часто используемые раскладки консоли:**

| Keymap | Раскладка |
|--------|--------|
| `us` | English (US) QWERTY |
| `us-acentos` | English (US) International |
| `uk` | English (UK) QWERTY |
| `be-latin1` | Belge AZERTY |
| `fr` | Français AZERTY |
| `de` | Allemand QWERTZ |
| `nl` | Néerlandais QWERTY |
| `es` | Espagnol QWERTY |
| `dvorak` | Dvorak (US) |
| `colemak` | Colemak |

> **Примечание:** `environment.sessionVariables.TZ` всегда должен совпадать с `time.timeZone` — оба управляют часовым поясом, один на уровне системы, другой на уровне сессии.

Отредактируйте `modules/home/local.nix` для личных переопределений home-manager (дополнительные пакеты, dotfiles, алиасы, fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> См. `modules/home/local.nix.example` — там все доступные варианты переопределения, включая настройку fastfetch.

### 5. Настройте ядро

Roudix использует **двух разных поставщиков ядра** в зависимости от вашей GPU:

- **`hardware.myGpu != "nvidia"`** (AMD или Intel) → ядро из [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), выбирается через `hardware.myKernel`. Модуль Nvidia не нужно учитывать, поэтому доступен полный набор из 36 вариантов.
- **`hardware.myGpu == "nvidia"`** → ядро из **Chaotic-Nyx**, выбирается через `hardware.myKernelChaotic`. Это нужно, чтобы получить **`nvidia_cachyos`** — предсобранный драйвер Nvidia, соответствующий их ядру; иначе модуль ядра Nvidia пересобирается локально при каждом обновлении ядра. Набор вариантов здесь намеренно меньше (Chaotic-Nyx не публикует столько вариантов, а варианты `-lto` чаще ломают внешние модули вроде модуля Nvidia).

Обе опции также принимают несколько **обычных ядер nixpkgs**, полностью вне соответствующего оверлея CachyOS — удобно, если вам нужно обычное ядро без патчей CachyOS: `zen`, `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing`, `xanmod-lts`, `xanmod-latest`. На пути Nvidia они обходят кэш `nvidia_cachyos` и пересобирают модуль Nvidia локально (см. `nvidia.nix`).

**Более свежие ядра nixpkgs — `hardware.myKernelSource`:** эти ядра nixpkgs по умолчанию следуют основному входу `nixpkgs` (nixos-unstable). Задайте `hardware.myKernelSource` равным `"master"` или `"staging-next"`, чтобы брать **только ядро** (и внешние модули, собранные под него, например Nvidia) из этой ветки NixOS/nixpkgs и получать обновления ядра раньше — остальная система не затрагивается. Значения: `"nixpkgs"` (по умолчанию), `"master"`, `"staging-next"`. Оговорки: такого ядра может ещё не быть в бинарном кэше, так что ожидайте долгую локальную сборку; `staging-next` к тому же несёт изменения тулчейна «в полёте», поэтому из трёх он самый рискованный. На ядра `cachyos-*` это не влияет (выводится предупреждение). После задания выполните один раз `nix flake lock`, чтобы новый вход был зафиксирован.

**Варианты `hardware.myKernel` (xddxdd — только AMD/Intel):**

| Вариант | Описание |
|---------|-------------|
| `zen` | Обычное `linuxPackages_zen` (nixpkgs) — вне оверлея xddxdd |
| `nixpkgs-lts` | Обычное ядро LTS по умолчанию из nixpkgs — вне оверлея xddxdd |
| `nixpkgs-latest` | Обычное последнее ядро mainline из nixpkgs — вне оверлея xddxdd |
| `nixpkgs-testing` | Обычное `linux_testing` из nixpkgs (RC/mainline) — вне оверлея xddxdd |
| `xanmod-lts` | Ветка XanMod LTS (`linuxPackages_xanmod`, nixpkgs) — governor производительности, lazy preemption, BBRv3 |
| `xanmod-latest` | Основная ветка XanMod (`linuxPackages_xanmod_latest`, nixpkgs) |
| `cachyos-latest` | Стандартное последнее ядро CachyOS |
| `cachyos-latest-v2` | оптимизировано для x86_64-v2 |
| `cachyos-latest-v3` | оптимизировано для x86_64-v3 (рекомендуется для современных CPU) |
| `cachyos-latest-v4` | оптимизировано для x86_64-v4 (AVX-512, только очень новые CPU) |
| `cachyos-latest-zen4` | оптимизировано для AMD Zen 4 |
| `cachyos-latest-lto` | Сборка с LTO для лучшей производительности |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (максимальная производительность, только современные CPU) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | Ядро CachyOS с долгосрочной поддержкой |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + оптимизировано для x86_64-v3 |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (стабильность + производительность) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | Планировщик BMQ |
| `cachyos-bmq-lto` | Планировщик BMQ + LTO |
| `cachyos-bore` | Планировщик BORE (лучшая отзывчивость) |
| `cachyos-bore-lto` | Планировщик BORE + LTO |
| `cachyos-deckify` | Оптимизировано для Steam Deck |
| `cachyos-deckify-lto` | Оптимизировано для Steam Deck + LTO |
| `cachyos-eevdf` | Планировщик EEVDF |
| `cachyos-eevdf-lto` | Планировщик EEVDF + LTO |
| `cachyos-hardened` | Ядро с усиленной безопасностью |
| `cachyos-hardened-lto` | С усиленной безопасностью + LTO |
| `cachyos-rc` | Release candidate — самое свежее, возможна нестабильность |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | Реальное время + планировщик BORE |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | Оптимизировано для серверов (без настроек под десктоп) |
| `cachyos-server-lto` | Оптимизировано для серверов + LTO |

**Варианты `hardware.myKernelChaotic` (Chaotic-Nyx — только Nvidia):**

| Вариант | Описание |
|---------|-------------|
| `cachyos` | По умолчанию — LTO + планировщик BORE, поставляется с соответствующим `nvidia_cachyos` |
| `cachyos-lts` | Долгосрочная поддержка |
| `cachyos-server` | Оптимизировано для серверов (без настроек под десктоп) |
| `cachyos-hardened` | С усиленной безопасностью |
| `zen` | Обычное `linuxPackages_zen` (nixpkgs) — модуль Nvidia пересобирается локально |
| `nixpkgs-lts` | Обычное LTS из nixpkgs — модуль Nvidia пересобирается локально |
| `nixpkgs-latest` | Обычное последнее mainline из nixpkgs — модуль Nvidia пересобирается локально |
| `nixpkgs-testing` | Обычное `linux_testing` из nixpkgs (RC) — модуль Nvidia пересобирается локально |
| `xanmod-lts` | XanMod LTS (nixpkgs) — модуль Nvidia пересобирается локально |
| `xanmod-latest` | Основная ветка XanMod (nixpkgs) — модуль Nvidia пересобирается локально |

> **Примечание про NVIDIA:** поддерживаются только GTX 20xx / серия RTX и новее. Открытые драйверы включены по умолчанию для RTX 20xx+ (Turing+). GTX 10xx/16xx не поддерживаются.

> **Примечание о теме Spicetify Comfy:** после первой сборки скопируйте color.ini вручную:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/apps/media/spicetify/Comfy/color.ini
> ```
> Затем выполните `rebuild`, чтобы применить.

### 6. Обновите монтирование диска

В `hosts/roudix/local.nix` добавьте блок `lib.mkForce` со своим UUID (или пропустите, если вторичного диска нет):

```bash
lsblk -f  # узнайте UUID своего диска
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Настройте мультизагрузку Limine (необязательно)

> Пропустите этот шаг, если на машине стоит только NixOS.

Limine умеет загружать другие операционные системы с отдельных дисков. `boot.local.nix` управляет дополнительными записями — он внесён в gitignore и никогда не перезаписывается при `git pull`.

**Никогда не редактируйте `modules/system/boot/boot.nix` напрямую** — он перезаписывается при `git pull`.

#### Если вы использовали автоматический установщик

Установщик автоматически обнаружил ваши другие ОС по EFI NVRAM (`efibootmgr`) и сам записал `boot.local.nix` — ручных действий не требуется. Результат можно проверить:

```bash
cat modules/system/boot/boot.local.nix
```

#### Если вы устанавливаете вручную

**Узнайте свои PARTUUID:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Ищите разделы с типом файловой системы `vfat` и меткой `EFI system partition` — это ваши ESP.

**Отредактируйте `modules/system/boot/boot.local.nix`** и добавьте свои записи:

```nix
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Windows
      protocol: efi
      path: uuid(YOUR-WINDOWS-ESP-PARTUUID):/EFI/Microsoft/Boot/bootmgfw.efi
    //CachyOS
      protocol: efi
      path: uuid(YOUR-CACHYOS-ESP-PARTUUID):/EFI/limine/BOOTX64.EFI
  '';
}
```

> **Совет:** путь EFI после UUID зависит от загрузчика другой ОС. Типичные пути:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - Любой дистрибутив (запасной вариант): `/EFI/BOOT/BOOTX64.EFI`

Если других ОС для добавления нет, оставьте `extraEntries` пустым:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` указан в `.gitignore` — `git pull` никогда его не перезапишет.

### 8. Обновите конфигурацию git

`modules/home/dev/git.nix` внесён в gitignore (как и `local.nix`) — скопируйте версионируемый шаблон и укажите свои данные:

```bash
cp modules/home/dev/git.nix.example modules/home/dev/git.nix
```

```nix
{ ... }:
{
  programs.git = {
    enable = true;
    settings = {
      user.name = "yourname";
      user.email = "your@email.com";
      init.defaultBranch = "main";
      pull.rebase = false;
    };
  };
}
```

- `init.defaultBranch = "main"` — имя первой ветки, когда вы делаете `git init` в новом репозитории (не влияет на ветку этого репозитория, только на те, что вы создаёте сами).
- `pull.rebase = false` — что делает `git pull`, когда ваша локальная ветка и удалённая разошлись: `false` делает слияние (создаёт merge-коммит, поведение по умолчанию и самое простое), `true` переносит ваши локальные коммиты поверх удалённых (линейная история, но коммиты переписываются — избегайте, если не уверены в работе с конфликтами rebase). `false` — более безопасный выбор для личного репозитория конфигурации.

> Если файла нет, `common.nix` его просто пропускает — Home Manager не будет настраивать git, пока вы его не скопируете, но ничего не сломается.

### 9. Включение и отключение необязательных модулей

В `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + ежедневное автообновление
roudix.fstrim.enable         = true;   # рекомендуется для SSD/NVMe
roudix.virtualization.enable = false;  # включите для QEMU/KVM
roudix.vmGuest.enable        = true;   # включайте только внутри ВМ
roudix.hosts.gtaFix.enable   = true;   # блокировка телеметрии BattlEye (исправление для GTA)
roudix.autoupdate.enable     = true;   # автоматический git pull + nh os boot при изменениях
roudix.zen.enable            = false;  # установить Zen Browser (по умолчанию отключено)
roudix.mesa.useGit           = false;  # true = mesa-git (экспериментально, самое новое — сборка может не удаться), false = стабильный nixpkgs
roudix.boot.bootloader       = "limine";  # "limine" или "systemd-boot"
roudix.matrixClient          = "none"; # "element", "cinny" или "none"
```

> **Напоминание:** если вы задали `roudix.autoupdate.enable = true`, настройте также интервал:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. Настройте fastfetch (необязательно)

По умолчанию Roudix показывает в fastfetch свой ASCII-логотип. Его можно переопределить в `modules/home/local.nix`, не трогая git:

```nix
# Использовать своё изображение (нужен терминал kitty)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Использовать свой ASCII-файл
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Переопределить всю конфигурацию fastfetch (заменяет всё)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` перезаписывает всю конфигурацию Roudix по умолчанию. Без него ваши ключи объединяются со значениями по умолчанию.
> См. `modules/home/local.nix.example` — там больше примеров.

### 11. Сборка

> **Если flakes и nix-command ещё не включены** (чистая установка NixOS):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **В остальных случаях:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

После сборки используйте алиасы fish для всех дальнейших операций.

> Все три файла `local.nix` и `boot.local.nix` указаны в `.gitignore` — `git pull` никогда их не перезапишет.

[English](features.md) · [Français](features.fr.md) · [Español](features.es.md) · [Português (Brasil)](features.pt_BR.md) · **Русский** · [简体中文](features.zh_CN.md) · [हिन्दी](features.hi.md) · [العربية](features.ar.md)

# Возможности

## Ядро и производительность

- Ядро CachyOS с включённым NTSync (модуль `ntsync`)
- Два поставщика ядер, выбираемые автоматически по `hardware.myGpu`:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 32 варианта (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 варианта (`hardware.myKernelChaotic`) — поставляет `nvidia_cachyos`, предсобранный драйвер, подогнанный под их ядро, поэтому модуль Nvidia не пересобирается локально при каждом обновлении ядра
- «Чистые» ядра из nixpkgs тоже можно выбрать у обоих поставщиков, полностью вне оверлея CachyOS — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline), `xanmod-lts` / `xanmod-latest` (XanMod). На Nvidia они переходят на локально пересобираемый модуль Nvidia (без кэша `nvidia_cachyos`)
- `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) берёт только эти ядра nixpkgs из более свежего nixpkgs, чтобы раньше получать обновления ядра, не затрагивая остальную систему
- ZRAM включён (100% ОЗУ, zstd, swappiness 150)
- zswap отключён
- Микрокод процессора настраивается автоматически (Intel или AMD)
- Intel: `split_lock_detect=off` применяется автоматически
- ananicy-cpp включён (демон приоритетов процессов, правила CachyOS)
- Поддержка планировщика SCX — переключение на лету, без перезагрузки (bpfland, lavd, flash, p2dq, rusty…) через графический Kernel Switcher — один запрос пароля через `scx-switch` останавливает/запускает ananicy-cpp и переключает планировщик за один раз — **примечание:** SCX не сохраняется после перезагрузки; после перезагрузки ananicy-cpp запускается автоматически, а планировщик нужно применить заново через графический Kernel Switcher

## Загрузка

- Загрузчик Limine (по умолчанию) — современный, быстрый, с поддержкой нескольких дисков — или systemd-boot, выбирается через `roudix.boot.bootloader`
- Автоматическое переименование записи UEFI в «Roudix»
- Меню загрузки для нескольких ОС (Windows, другие дистрибутивы Linux на отдельных ESP)
- Метка загрузки показывает имя Roudix + версию релиза NixOS

## Игры

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, сессия по умолчанию отключена)
- Переменные окружения для захвата OBS предварительно настроены (`OBS_VKCAPTURE` через `environment.sessionVariables`)
- Собственный горизонтальный оверлей MangoHud (метка `Powered By Roudix`)
- Поддержка геймпадов (Steam Hardware + game-devices-udev-rules)
- Поддержка 32-битных приложений для Wine/Steam
- Обёртка `game-performance` — на время игры переключается на отдельный профиль производительности `tuned-adm`, отслеживаемый через cgroup `systemd-run --user --scope` (так что он переживает повторный fork/отсоединение Steam) и восстанавливается при выходе (использование: `game-performance %command%` в параметрах запуска Steam) — GameMode намеренно отключён (здесь несовместим с ananicy-cpp)
- `ffmpegthumbnailer` доступен во всей системе (миниатюры видео в файловых менеджерах)
- `protonup-qt` в KDE, `protonplus` в остальных окружениях рабочего стола
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft или Modrinth App как альтернатива — `roudix.gaming.apps.modrinth.enable`) и Vintage Story (через roudix-caches)
- Каждое игровое приложение можно включать/отключать по отдельности через `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (по умолчанию все `true`)
- Необязательный модифицированный клиент Steam [Millennium](https://github.com/SteamClientHomebrew/Millennium) (темы + плагины) — по умолчанию отключён, включается через `roudix.gaming.steam.millennium.enable = true` (или из установщика). Неофициальный мод; правка песочницы `game-performance` и инструменты совместимости Proton продолжают работать, а возврат к `false` восстанавливает стандартный Steam
- Необязательный консольный игровой режим: `roudix.gaming.gamescopeSession.enable` добавляет на экран входа сессию «Steam (Gaming Mode)» (Steam Big Picture внутри gamescope, VRR/HDR/MangoApp, частота обновления определяется при запуске). «Переключиться на рабочий стол» в Steam открывает ваш рабочий стол, а приложение «Return to Gaming Mode» возвращает в игру, минуя экран входа. Основано на GLF-OS; поддерживает niri, umbriel, GNOME, KDE, Hyprland и MangoWC
- Необязательный Decky Loader (плагины Steam) через `roudix.gaming.gamescopeSession.decky.enable`, берётся из flake input Jovian-NixOS (`nix flake update jovian` для обновления, никакого sha вручную поддерживать не нужно); бинарного кэша нет, поэтому при первой пересборке он компилируется локально

## Рабочий стол (Niri)

- Niri — прокручиваемый тайловый композитор Wayland — поставляется через [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), по умолчанию используется `niri-unstable`, бинарный кэш `niri.cachix.org` предварительно настроен
- Конфигурация нативная для Nix (`programs.niri.settings`), разбита по темам (general, animations, input, layout, outputs, binds, rules) и проверяется при сборке через `niri validate` — сломанная конфигурация приводит к сбою сборки, а не композитора при входе
- Живая синхронизация темы Noctalia/DMS (цвета, сгенерированные matugen/DMS, alt-tab, размытие) сохраняется за счёт добавления `include` в сгенерированную конфигурацию вместо статического вшивания
- Современная оболочка Noctalia (v5)
- xdg-desktop-portal-gnome + gtk (порталы screencast и удалённого рабочего стола настроены)
- Курсор Bibata Modern Ice (24 px)
- adw-gtk3 + значки Papirus + Papirus Folders
- Element Desktop с gnome-libsecret / kwallet6 (определяется автоматически для каждого окружения рабочего стола)
- Агент Polkit от GNOME
- DMS Greeter (greetd)

## Рабочий стол (MangoWC)

- Композитор Wayland MangoWC
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Курсор Bibata Modern Ice (24 px)
- Агент Polkit от GNOME
- Менеджер входа Ly
- adw-gtk3 + значки Papirus + Papirus Folders
- Анимация открытия с зумом + официальные кривые Безье
- VRR + tearing включены на игровом мониторе (DP-1 1440p@240)
- Скриншоты через grim + slurp + satty (аннотации) — 3 сочетания клавиш
- Переключатель окон на rofi (Alt+Tab)
- Переменные окружения XDG Desktop Portal предварительно настроены (захват экрана через Pipewire, OBS, Discord Go Live)
- force_tearing + idleinhibit_when_focus для всех игровых приложений (Steam, Heroic, Minecraft, Lutris, Bottles)
- Прозрачность окон без фокуса (0.85)
- Hotarea overview (жест мышью в углу экрана)
- Плавающий snap + перетаскивание из тайла в тайл
- Поддержка scratchpad: общий пул для любых окон (переместить/переключить/восстановить),
  а также необязательный (`roudix.mangowc.scratchpadApps`) именованный scratchpad для
  каждого приложения — Discord/Element/Telegram/Spotify — у каждого своя клавиша переключения

## Рабочий стол (Umbriel)

- Umbriel — прокручиваемый тайловый композитор Wayland — собственный нативный композитор Noctalia, поставляется через [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (только с Noctalia, без смены оболочки)
- Конфигурация нативная для Nix (`programs.umbriel.settings`), разбита по темам (general, appearance, animation, input, layout, outputs, binds, rules) и проверяется при сборке (`validateConfig = true`)
- Живая синхронизация темы Noctalia (цвета, сгенерированные matugen) сохраняется через нативный механизм Umbriel `include.files`, без статического снимка цветов
- Курсор Bibata Modern Ice (24 px)
- adw-gtk3 + значки Papirus + Papirus Folders
- Hot corners (overview при наведении мыши в угол) и обзор рабочих пространств (Mod+O)
- Поддержка scratchpad (переместить/переключить/восстановить плавающее окно по требованию)
- Переопределение раскладки для отдельных рабочих пространств (например, без отступов на игровом рабочем пространстве)

## Рабочий стол (Hyprland)

- Hyprland — динамический тайловый композитор Wayland, запускается через UWSM
- Современная оболочка Noctalia
- xdg-desktop-portal-hyprland + портал gtk
- Курсор Bibata Modern Ice (24 px)
- Агент Polkit от GNOME (запускается как пользовательская служба systemd)
- Демон обоев swww
- Скриншоты через grim + slurp + satty (аннотации) — 3 сочетания клавиш

## Рабочий стол (GNOME)

- GNOME 50.x (следует за веткой nixos-unstable)
- Тщательно подобранный набор расширений (blur, tiling, vitals, arcmenu...) — включаются через dconf
- ArcMenu с логотипом Roudix в качестве значка кнопки меню
- Лишний софт удалён через `environment.gnome.excludePackages`
- Тема значков Papirus-Dark
- Тема GTK adw-gtk3-dark (по умолчанию тёмный режим)
- Курсор Bibata Modern Ice (24 px)
- Обои Roudix (светлые/тёмные в зависимости от темы системы)
- `color-scheme = prefer-dark` применяется через dconf
- Настройки расширений (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) предварительно заданы через `gnome-extensions.nix`
- Добавляйте и убирайте расширения, не редактируя основные файлы, через `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Переопределяйте обои, тему, значки и курсор в `home/local.nix`

## Рабочий стол (KDE)

- KDE Plasma 6 с plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect включён
- xdg-desktop-portal-kde
- Тема значков Papirus-Dark
- Оформление и цветовая схема Breeze Dark
- Обои Roudix Dark на экране входа и на рабочем столе
- Подобранные пакеты: partitionmanager, kcalc, digikam, vlc...
- Лишний софт удалён (Discover исключён)
- Переопределяйте обои, панели и тему значков в `home/local.nix`

## Музыка

Выберите один вариант через `roudix.musicPlayer` — `"spotify"` (по умолчанию), `"ytmdesktop"`,
`"sonora"` или `"none"`.

- `"spotify"` — Spotify, пропатченный Spicetify. Локальная тема, по умолчанию
  «colorful» (или «comfy»), плюс расширения для блокировки рекламы и скрытия подкастов — см.
  переключатели ниже.
- `"ytmdesktop"` — YouTube Music Desktop App (неофициальный клиент YouTube Music
  на Electron).
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora), нативный
  (Rust/GPUI) клиент для Spotify, YouTube Music, Apple Music, Deezer и
  Subsonic в одном приложении. Необязательная опция `roudix.sonora.provider` выбирает
  провайдера, с которого он стартует (`"youtube"` = YouTube Music). Подписки он
  не обходит: если сервис требует подписку, Sonora тоже её требует.

## Необязательные общие приложения

GIMP, Inkscape, SongRec и EasyEffects (+ rnnoise-plugin) устанавливаются по умолчанию, но
каждое можно отключить по отдельности через `roudix.apps.<name>.enable` (`gimp`,
`inkscape`, `songrec`, `easyeffects`).

У Signal и ZapZap (неофициальный десктопный клиент WhatsApp с нативным видом)
нет реальной альтернативы, между которой можно переключаться, поэтому это обычные булевы
опции opt-in, по умолчанию отключённые: `roudix.apps.signal.enable` и `roudix.apps.zapzap.enable`.

Fluxer, альтернатива Discord, которую можно развернуть у себя, — такая же булева опция
opt-in: `roudix.apps.fluxer.enable`. В nixpkgs его пока нет, поэтому он
берётся прямо из предсобранного пакета `fluxer-desktop` во flake input
`nix-gaming-edge`. Он намеренно не зависит от `roudix.discord`
и `roudix.gaming.enable` — ничто не мешает захотеть и Discord,
и Fluxer, или Fluxer без какой-либо игровой настройки.

Также доступны, opt-in (по умолчанию отключены), почтовый клиент и менеджер
паролей: `roudix.mailClient` — `"thunderbird"` (полнофункциональный),
`"betterbird"` (доработанный форк Thunderbird, берётся из flake input
[betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) — в nixpkgs
пока нет) или `"geary"` (лёгкий клиент GNOME);
`roudix.passwordManager` —
`"bitwarden"` (синхронизация через облако), `"keepassxc"` (локальное хранилище, офлайн) или
`"protonpass"` (синхронизация через облако, аккаунт Proton).

Также доступен, opt-in (по умолчанию отключён), торрент-клиент через
`roudix.torrentClient` — `"qbittorrent"` (богатый функциями, на Qt),
`"fragments"` (минималистичный клиент GNOME/libadwaita), `"deluge"` (на плагинах) или
`"none"` (по умолчанию).

## Spicetify

- Тема: `roudix.spicetify.theme` — `"colorful"` (по умолчанию, sanoojes/spicetify-colorful) или `"comfy"` (встроенная тема Comfy)
- Цветовая схема: `roudix.spicetify.colorScheme` — `null` (по умолчанию) использует схему самой темы («noctalia» для colorful, «Comfy» для comfy)
- Расширения включаются по отдельности: `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (обе по умолчанию `true`)
- Пользовательское приложение Marketplace: `roudix.spicetify.marketplace.enable` (по умолчанию `true`)

## Браузер

- Настраиваемый список браузеров через опцию `roudix.browsers`
- Поддерживаются `brave`, `helium` (через amaanq/helium-flake, включает патч DRM — воспроизведение Widevine подключается автоматически через `modules/home/apps/browser/helium-widevine.nix` при выборе `helium`), `vivaldi` (с кодеками ffmpeg), `firefox`, `librewolf`, `chromium` или `[]`, если браузеры не нужны
- Zen Browser доступен отдельно через `roudix.zen.enable = true` (по умолчанию отключён); канал выбирается через `roudix.zen.variant` — `"twilight"` (по умолчанию) или `"beta"`

## Прочее

- Discord выбирается через `roudix.discord` — `"vencord"` (пропатченный клиент, по умолчанию), `"vanilla"` (без патчей) или `"none"` (не установлен)
- Telegram выбирается через `roudix.telegram` — `"telegram"` (официальный Telegram Desktop), `"ayugram"` (неофициальный форк: режим призрака, защита от удаления сообщений, локальная история сообщений...) или `"none"` (по умолчанию, не установлен)
- Редактор кода выбирается через `roudix.editor` — `"zed"` (по умолчанию), `"vscode"`, `"neovim"` или `"none"` (управляйте своим, например AppImage/Flatpak)
- Графическая (Wayland) раскладка клавиатуры через `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, например `"be"` / `"intl"`) — не зависит от `console.keyMap`, который действует только в TTY до запуска графической сессии; на GNOME/KDE не влияет, так как они управляют своей раскладкой сами
- Связка keyring + xdg-desktop-portal для «голых» композиторов (Niri, Hyprland, MangoWC, Umbriel) выбирается через `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, по умолчанию) или `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent, а приложения GNOME заменяются на Kate / Gwenview / KDE Partition Manager / Dolphin; adw-gtk3, nwg-look, qt6ct и gvfs сохраняются, чтобы GTK-приложения оставались в теме); на сессии GNOME/KDE не влияет, они сохраняют свой родной стек
- `nix-ld` включён во всей системе — запускайте непропатченные динамические бинарники без окружения FHS (предварительно настроен с распространёнными библиотеками: glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib и другими)
- OBS Studio, включается по отдельности через `roudix.contentCreation.obs.enable` (по умолчанию `true`), плагины включаются по одному через `roudix.contentCreation.obs.plugins.<name>.enable` (`vkcapture` + `pipewireAudioCapture` включены по умолчанию; также доступны: `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- Видеоредактор выбирается через `roudix.contentCreation.videoEditor` — `"kdenlive"` (по умолчанию), `"davinci-resolve"` (бесплатный), `"davinci-resolve-studio"` (платный, нужна лицензия), `"shotcut"` или `"none"`; DaVinci Resolve автоматически получает AMD OpenCL ICD при `hardware.myGpu = "amd"`
- Виртуальная камера `v4l2loopback` настраивается автоматически для OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`, по умолчанию `true`)
- Клиент чата Twitch Chatterino2, opt-in через `roudix.contentCreation.streaming.chatterino.enable`
- Всю группу для создания контента можно включать/отключать через `roudix.contentCreation.enable`
- GPU Screen Recorder
- Опция Mesa Git для AMD — включает экспериментальную/самую свежую Mesa через `roudix.mesa.useGit = true` в `local.nix` (по умолчанию: стабильная Mesa из nixpkgs) — ⚠️ **экспериментально**, сборка может завершиться ошибкой в зависимости от состояния nixpkgs
- Параметры ядра для стабильности GPU AMD применяются автоматически (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — устраняют случайные зависания и проблемы при выходе из сна на RDNA2/RDNA3
- RGB-контроллер выбирается через `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, автоматически обновляется через CI), `openrgb` (разные бренды: Razer, ASUS, MSI…) или `none`
- Веб-интерфейс OpenLinkHub доступен по адресу [http://127.0.0.1:27003](http://127.0.0.1:27003) после запуска службы
- Управление RGB-подсветкой ОЗУ DDR4/DDR5 через OpenLinkHub — включается через `roudix.memory.enable = true`, настройте `roudix.memory.type`, `roudix.memory.smBus` и `roudix.memory.sku` (см. `installation.ru.md`)
- PipeWire со стереошумоподавлением rnnoise (nofail, совместимость LADSPA_PATH 26.05/26.11)
- Flatpak с репозиторием Flathub + ежедневное автообновление (через nix-flatpak)
- Менеджер Bluetooth Blueman
- Клиент Matrix — настраивается через `roudix.matrixClient` (`element`, `cinny` или `none`) — Element автоматически выбирает kwallet6 в KDE и gnome-libsecret в остальных случаях
- Видеоплеер выбирается через `roudix.videoPlayer` — `"vlc"` (самая широкая поддержка форматов, по умолчанию), `"clapper"` (современный плеер на GTK4), `"mpv"` (+ yt-dlp, минималистичный/для стриминга), `"celluloid"` (GTK-интерфейс для mpv) или `"none"`; действует на всех рабочих столах (раньше Clapper был жёстко задан только на «голых» композиторах, плюс отдельный переключатель mpv, не зависящий от окружения рабочего стола)
- Поддержка AppImage включена через `appimage.nix`
- Waydroid (контейнер Android) — необязательно, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (необязательно, `roudix.virtualization.enable`)
- vm-curator (необязательно, `roudix.virtualization.vmCurator.enable`) — TUI-альтернатива virt-manager на Rust, управляет QEMU напрямую (без libvirt), с 3D-ускорением и поддержкой проброса GPU; можно включить независимо или вместе со стеком libvirt
- Модуль оптимизаций для гостевых ВМ (общий буфер обмена, автоматическое изменение размера, агент QEMU, Spice)

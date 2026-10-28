[English](aliases.md) · [Français](aliases.fr.md) · [Español](aliases.es.md) · [Português (Brasil)](aliases.pt_BR.md) · **Русский** · [简体中文](aliases.zh_CN.md) · [हिन्दी](aliases.hi.md) · [العربية](aliases.ar.md)

# Алиасы и функции

## Доступны везде

| Алиас | Действие |
|-------|--------|
| `rebuild` | Немедленно применить конфигурацию |
| `update` | Забрать конфигурацию (pull), пересобрать + switch, обновить Flatpak (см. [ниже](#update)) |
| `cleanup` | Удалить старые поколения + сборка мусора |
| `noctalia-reload` | Перезапустить Noctalia без выхода из сеанса |
| `dms-reload` | Перезапустить Quickshell без выхода из сеанса |
| `caelestia-reload` | Перезапустить Quickshell без выхода из сеанса |
| `roudix-switch <de>` | Сменить окружение рабочего стола (применится при следующей перезагрузке) |
| `roudix-kernel-switch <kernel>` | Сменить вариант ядра (применится при следующей перезагрузке) |

### `update`

Ручной аналог [автообновления](autoupdate.ru.md): тот же репозиторий, та же отслеживаемая ветка, то же правило «только fast-forward» (ваши локальные коммиты никогда не затрагиваются). Работает от вашего обычного пользователя и использует `sudo` только там, где это нужно.

1. `git pull --ff-only` отслеживаемой ветки (пропускается, если вы находитесь в другой ветке, например в ветке фичи)
2. `nh os switch` (или `nh os boot` с `--boot`)
3. Обновление Flatpak — пользовательских и системных, затем удаление неиспользуемых runtime (никогда не критично)

Файл `flake.lock`, который вы получаете из git, — это тот, что CI уже собрал и проверил, поэтому обычный `update` **не** обновляет входы flake.

| Параметр | Действие |
|--------|--------|
| `-i`, `--inputs [name…]` | Дополнительно обновить входы flake локально (все или только указанные). Если сборка не удалась, `flake.lock` восстанавливается |
| `-b`, `--boot` | Применить при следующей загрузке вместо немедленного switch |
| `-c`, `--check` | Только сообщить, есть ли новые коммиты |
| `-n`, `--dry` | Пробный запуск (`nh --dry`): ничего не забирается, не обновляется, не активируется |
| `--changes` | Показать, чем система следующей загрузки отличается от работающей (удобно после автообновления) |
| `--log` | Показать журнал последнего запуска (хранится в `~/.local/state/roudix/update.log`) |
| `--no-inputs` | Пропустить обновление входов (удобно при `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | Пропустить pull / обновление Flatpak |

```fish
update                    # pull + пересборка + switch
update --inputs           # обновить все входы, затем пересобрать
update --inputs nixpkgs   # обновить только nixpkgs
```

На машине, которая следит за `dev` и всегда хочет свежие входы, задайте `roudix.update.bumpInputs = true;` в `local.nix`: тогда обычный `update` ведёт себя как `update --inputs`.

> После `update --inputs` файл `flake.lock` оказывается локально изменённым: сделайте commit и push (или `git checkout flake.lock`), иначе следующий pull автообновления может отказаться запускаться, если за это время CI изменил lock.

## Только Niri, Hyprland и MangoWC

| Алиас | Действие |
|-------|--------|
| `roudix-shell-switch <shell>` | Сменить графическую оболочку (применится при следующей перезагрузке) |

### Использование

```fish
# Сменить окружение рабочего стола
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde
roudix-switch cinnamon
roudix-switch cosmic

# Сменить вариант ядра — список зависит от hardware.myGpu, см. docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — меньший набор, нужен для бинарного кэша nvidia_cachyos):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# Обычные ядра nixpkgs — доступны на обоих путях GPU, вне оверлея CachyOS
# (на Nvidia они используют локально пересобранный модуль Nvidia, без кэша nvidia_cachyos):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# Сменить графическую оболочку (только Niri, Hyprland и MangoWC)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # только для hyprland
```

Все три команды автоматически правят `hosts/roudix/local.nix` и запускают `nh os boot` — вручную пересобирать не нужно. Изменения применяются при следующей перезагрузке.

> **Примечание:** `roudix-kernel-switch` автоматически записывает значение в `hardware.myKernel` или `hardware.myKernelChaotic` в зависимости от вашего текущего `hardware.myGpu` — передайте название варианта из списка для вашей видеокарты (см. таблицу выше).

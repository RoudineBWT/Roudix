[English](desktop.md) · [Français](desktop.fr.md) · [Español](desktop.es.md) · [Português (Brasil)](desktop.pt_BR.md) · **Русский** · [简体中文](desktop.zh_CN.md) · [हिन्दी](desktop.hi.md) · [العربية](desktop.ar.md)

# Окружения рабочего стола

Переключайте рабочий стол в любой момент командой `roudix-switch <de>` или через графический интерфейс **Roudix Customizer** (пакет `roudix-switcher`) — отдельный хост не нужен. Интерфейс вышел за рамки простого переключения рабочего стола: теперь в одном приложении собраны Рабочий стол, Игры (переключатели для отдельных приложений), Редактор, Терминал, Браузер, Оболочка входа, Файловый менеджер, Чат-клиент (Discord/Matrix) и Интеграция (стек keyring/portal).

| Значение | Рабочий стол | Примечания |
|----------|--------------|------------|
| `niri` | Niri + (Noctalia, DMS) | По умолчанию — Wayland с прокручиваемой тайловой раскладкой (scrollable tiling) |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Wayland с динамической тайловой раскладкой — запускается через UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | Композитор Wayland |
| `umbriel` | Umbriel + Noctalia | Прокручиваемая тайловая раскладка — собственный нативный композитор Noctalia, только с Noctalia (без смены оболочки) |
| `gnome` | GNOME 49.5 | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |
| `cinnamon` | Cinnamon | Сессия X11 + LightDM — классический рабочий стол, подходит для старого оборудования (GNOME 49 работает только на Wayland) |
| `cosmic` | COSMIC | Wayland-рабочий стол от System76 (cosmic-comp), cosmic-greeter |

Чтобы изменить навсегда, отредактируйте `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome", "kde", "cinnamon" или "cosmic"
```

Или воспользуйтесь функцией fish — она правит конфигурацию и пересобирает систему за один шаг:

```fish
roudix-switch kde
```

> **Примечание:** `roudix-switch` использует `nh os boot` — изменения применяются при следующей перезагрузке.

---

## Графические оболочки (только Niri, Hyprland и MangoWC)

Для Wayland-композиторов (Niri, Hyprland, MangoWC) можно менять стек оболочки/панели независимо от композитора. Для Hyprland **одно дерево конфигурации** (`dotfiles/hyprland/`) содержит общие сочетания клавиш и выбирает оболочку по значению `roudix.desktop.shell`.

| Значение | Оболочка | Hyprland |
|----------|----------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | DankMaterialShell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**Примечание:** Caelestia доступна только в Hyprland. Оболочка передаётся в сессию через `ROUDIX_HYPR_SHELL`, поэтому отдельных деревьев `hyprland-dms/` и `hyprland-caelestia/`, которые нужно синхронизировать, нет.

### Автозапуск оболочки

Запуск зависит от выбранной оболочки и композитора, причём для каждой оболочки используется ровно один механизм запуска:

- **Hyprland + Noctalia:** `noctalia` из Lua-хука `hyprland.start`.
- **Hyprland + Caelestia:** `caelestia-shell` из Lua-хука `hyprland.start`.
- **Hyprland + DMS:** пользовательская служба systemd DMS; Hyprland экспортирует окружение сессии в systemd при запуске.
- **MangoWC + Noctalia:** `noctalia` из `autostart_sh` MangoWC.
- **MangoWC + DMS:** пользовательская служба systemd DMS, запускаемая через `mango-session.target`; поэтому MangoWC не выполняет `dms run`.

DMS не должен запускаться одновременно и systemd, и композитором: официальная документация рекомендует убрать `dms run`, если используется служба systemd.

Чтобы изменить, отредактируйте `hosts/roudix/local.nix`:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" или "caelestia"
```

Затем пересоберите систему:

```fish
rebuild
```

Или воспользуйтесь функцией fish (доступна только в Niri, Hyprland и MangoWC) — она правит конфигурацию и пересобирает систему за один шаг:

```fish
roudix-shell-switch dms
```

> **Примечание:** `roudix-shell-switch` использует `nh os boot` — изменения применяются при следующей перезагрузке.

---

## nixpkgs или последняя версия (flake)

Niri, MangoWC и Umbriel всегда берутся из собственного flake. Для оболочки (и сопутствующего ей greeter) Roudix по умолчанию использует версию из **nixpkgs**. Чтобы получить самую свежую версию, собранную из flake самого проекта, включите её для нужного компонента в `local.nix` — или в `roudix-switcher` / установщике, где переключатель появляется только для выбранной оболочки:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # DankMaterialShell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (greeter DMS следует за ней)
```

У Hyprland в Roudix нет flake-версии: он всегда берётся из nixpkgs.

> **Внимание:** конфигурации Roudix пишутся **в первую очередь под flake-версии (latest)**. В версиях из nixpkgs ошибка конфигурации о том, что опция, параметр или ключ конфигурации *не существует*, — это **нормально**: он был добавлен после версии, которую поставляет nixpkgs. Дождитесь, пока nixpkgs догонит, или установите для компонента `true`.

> Если flake-модуль не предоставляет опцию `package` (возможно для DMS, MangoWC и greeter DMS), версию из nixpkgs применить нельзя: Roudix остаётся на flake-версии и выводит предупреждение во время сборки.

---

## Персональные переопределения композитора

Niri и Umbriel настраиваются нативно в Nix (`programs.niri.settings` / `programs.umbriel.settings`) — это настоящие типизированные attrset, а не генерируемый текстовый файл. Это значит, что переопределения — просто Nix: добавьте ключ, которого ещё нет, и он автоматически объединится; если вы меняете ключ, который репозиторий уже задаёт (тот же выход, то же сочетание клавиш), нужен `lib.mkForce`, иначе Nix откажется собирать систему с ошибкой «conflicting definitions».

MangoWC и Hyprland остаются текстовыми (см. ниже).

Переопределения можно писать прямо в `home/local.nix`, но если вы много настраиваете один композитор, отдельный файл удобнее — `home/local.nix` автоматически подключает `home/niri-custom.nix`, `home/umbriel-custom.nix` и `home/mango-custom.nix`, если они существуют (скопируйте соответствующий файл `*.example`, чтобы начать; они в gitignore, как и `local.nix`).

**Niri**

```nix
# Изменить монитор, который niri-flake уже задаёт (нужен lib.mkForce)
# — выполните `niri msg outputs` внутри сессии, чтобы узнать настоящее имя разъёма
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# Переназначить сочетание клавиш, которое репозиторий уже определяет (нужен lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# Добавить сочетание клавиш, которого ещё нет (mkForce не нужен)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# Добавить правило окна — списки СКЛЕИВАЮТСЯ между файлами, так что это просто
# добавляется к правилам репозитория, mkForce не нужен
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# Изменить выход (нужен lib.mkForce — выполните `umbriel outputs`, чтобы узнать настоящее имя)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# Переназначить сочетание клавиш, которое репозиторий уже определяет
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# Добавить сочетание клавиш, которого ещё нет
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# Добавить правило окна
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** по-прежнему подключает в самом конце своей конфигурации персональный файл переопределений, сгенерированный home-manager — **`git pull` его никогда не трогает**, — потому что на практике у него нет типизированной схемы Nix:

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

Поскольку это один большой текстовый блок, а не несколько строк Nix, его лучше держать в отдельном файле — см. `home/mango-custom.nix.example`.

**Hyprland теперь использует модульную Lua-конфигурацию из `dotfiles/hyprland/`.** Точка входа — `dotfiles/hyprland/hyprland.lua`, который загружает модули из `config/` для мониторов, раскладок, анимаций, сочетаний клавиш, правил окон и интеграции оболочек. Nix копирует это дерево как есть в `~/.config/hypr/`.

Текущая конфигурация рассчитана на Hyprland 0.55+ и использует нативные раскладки `dwindle`, `master` и `scrolling`. Модуль Nix генерирует небольшой загрузчик `config/nix-plugins.lua`, который выполняется до точки входа; `borders-plus-plus` включён в Roudix. Блок `dynamic_cursors` остаётся необязательным и применяется только при наличии этого плагина.

### Настройка Hyprland

Значения, специфичные для конкретной машины (выходы `DP-1`/`DP-3`, основной монитор, приложения по умолчанию, клавиатура и т. д.), находятся в `dotfiles/hyprland/config/`. Редактируйте их напрямую, если храните конфигурацию Hyprland в репозитории Roudix.

Для личных переопределений без изменения отслеживаемых файлов используйте `home/local.nix` с `xdg.configFile."hypr/..."` и `lib.mkForce`.

> После изменения Lua-конфигурации выполните `rebuild`. Для изменений оболочки или окружения может потребоваться перезапуск сессии.

> Полный список примеров см. в `home/niri-custom.nix.example`, `home/umbriel-custom.nix.example`, `home/mango-custom.nix.example` и `home/local.nix.example`.

---

## Переопределения GNOME

При `roudix.desktop.type = "gnome"` управление расширениями задаётся в `hosts/roudix/local.nix`, а переопределения внешнего вида — в `home/local.nix`.

**Добавить расширения к стандартным** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**Отключить стандартное расширение по UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**Объединить оба варианта — например, заменить ArcMenu другим лаунчером** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**Изменение внешнего вида вручную (рекомендуется)**

Roudix поставляет внешний вид GNOME (обои, тёмную тему, значки, курсор, настройки расширений) как *значения по умолчанию*. Измените что угодно в Параметрах, Tweaks или настройках расширения — и это станет вашим: пересборка никогда не вернёт старое. Обновления Roudix меняют только значения по умолчанию тех параметров, которых вы не трогали.

**Принудительное задание значения из вашей конфигурации** (`home/local.nix`)

Если вы предпочитаете закрепить значение декларативно, задайте его через home-manager. В отличие от ручного способа выше, оно применяется заново при **каждой** пересборке и перекрывает то, что вы меняете в интерфейсе:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # или "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
`lib.mkForce` не нужен: home-manager больше не задаёт эти ключи.

**Возврат значений Roudix по умолчанию** для параметра (или целого раздела)
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> Все доступные параметры переопределения GNOME см. в `hosts/roudix/local.nix.example` и `home/local.nix.example`.

---

## Переопределения KDE Plasma

При `roudix.desktop.type = "kde"`:

Roudix применяет свой внешний вид KDE **один раз**, а не при каждой пересборке, поэтому всё, что вы измените в Параметрах системы, сохраняется:

- **Тёмная тема, значки, курсор**: применяются только при первом входе, защищены файлом `~/.local/state/roudix/kde-theme-seeded`. Чтобы намеренно вернуть внешний вид Roudix: `rm ~/.local/state/roudix/kde-theme-seeded` и выйдите из сессии и войдите снова.
- **NumLock при запуске, обои экрана блокировки**: обычные значения по умолчанию KConfig в `/etc/xdg`, которые лежат ниже вашего `~/.config` и никогда его не переопределяют.
- **Обои и панель**: применяются plasma-manager при первом входе и перезапускаются только если сам Roudix изменит их определение в обновлении.

**Закрепление значений из вашей конфигурации** (`home/local.nix`)

Всё, что вы задаёте через plasma-manager, применяется заново при **каждой** пересборке, поэтому используйте это только для того, что должно быть декларативным:

**Обои**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Цветовая схема / значки / курсор**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**Панель задач / Панели**
```nix
programs.plasma.panels = lib.mkForce [
  {
    location = "bottom";
    widgets = [
      { kickoff.icon = "/path/to/your/icon.svg"; }
      "org.kde.plasma.icontasks"
      "org.kde.plasma.marginsseparator"
      "org.kde.plasma.systemtray"
      "org.kde.plasma.digitalclock"
      "org.kde.plasma.showdesktop"
    ];
  }
];
```

> `lib.mkForce` нужен только для `wallpaper` и `panels`, которые по-прежнему определены в `home/desktop/kde/default.nix`.

## Значения по умолчанию Cinnamon

Cinnamon по умолчанию поставляется с обоями Roudix Kitsune — на рабочем столе и на экране входа LightDM, использует логотип Roudix как значок меню и закрепляет на панели браузер по умолчанию (первый из `roudix.browsers`), Roudix Store и Параметры. Приложения GTK4 / libadwaita следуют тёмной теме. Это значения по умолчанию: они применяются только к тому, что пользователь не менял. Закреплённые элементы панели (браузер, Nemo, Roudix Store, Параметры) и значок меню — значения по умолчанию апплетов, поставляемые в виде пропатченных копий двух апплетов: сам Cinnamon не пересобирается.

У экрана входа (slick-greeter) нет приложения настроек. Меняйте его обои так:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # пересборка не нужна
roudix-lightdm-wallpaper --reset                    # вернуть Kitsune
```

Переопределите закреплённые приложения в `hosts/roudix/local.nix`:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## Значения по умолчанию COSMIC

COSMIC по умолчанию поставляется с обоями Roudix Kitsune и раскладкой клавиатуры из `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions`. В доке закреплены браузер(ы), выбранные в Roudix (и Zen, если включён), COSMIC Files, ваш терминал, Roudix Store и COSMIC Settings — та же идея, что и у dash в GNOME и диспетчера задач в Plasma. В библиотеке приложений все приложения Roudix (Store, Customizer, Kernel Switcher, Scheduler, Hardware Sync, Config, Welcome) сгруппированы в папке **Roudix** и больше не отображаются в разделе Система / Утилиты. COSMIC Store не устанавливается: её заменяет Roudix Store.

Это значения по умолчанию, поставляемые в виде общесистемных файлов cosmic-config: они применяются только к тому, что пользователь не менял, а пересборка никогда не отменяет выбор, сделанный в COSMIC Settings.

Собственные приложения и панель COSMIC по умолчанию используют цветовую схему Roudix (`assets/cosmic/`, сгенерирована из `assets/palette/Roudix.json`, устанавливается как системные значения по умолчанию модулем `modules/system/desktop/cosmic.nix`, Home Manager не задействован). Выбор другой темы или акцентного цвета в Параметры > Оформление переопределяет её, а пересборка никогда не затрагивает ваш выбор. Параметр «Применять текущую тему к приложениям GNOME» (Параметры > Рабочий стол > Оформление > Значки и тема тулкитов) включён по умолчанию: сам COSMIC экспортирует свою тему, поэтому GTK-приложения (браузеры, приложения Roudix...) получают цвета Roudix поверх adw-gtk3 без какого-либо CSS, написанного Roudix. Значки — Papirus-Roudix (см. `roudix.iconTheme`), а ваш терминал получает цветовую схему Roudix, как и на любом другом рабочем столе.

`system76-scheduler`, который включает модуль COSMIC из nixpkgs, по умолчанию отключён, потому что у Roudix есть собственный стек планировщика (SCX). Чтобы оставить его:

```nix
services.system76-scheduler.enable = true;
```

Чтобы изменить закреплённые приложения, просто закрепляйте / открепляйте их в доке: ваш выбор важнее значения по умолчанию.

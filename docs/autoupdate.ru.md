[English](autoupdate.md) · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · [Português (Brasil)](autoupdate.pt_BR.md) · **Русский** · [简体中文](autoupdate.zh_CN.md) · [हिन्दी](autoupdate.hi.md) · [العربية](autoupdate.ar.md)

# Автообновление

Если `roudix.autoupdate.enable = true`, система проверяет GitHub каждый час (и через 5 минут после загрузки).
Если в отслеживаемой ветке (по умолчанию `main`) обнаружены новые коммиты, она делает pull и запускает `nh os boot path:...` — новая конфигурация применится при следующей перезагрузке.
Ваши файлы `local.nix`, `username.nix`, `hardware-configuration.nix`, необязательные `modules/home/niri-custom.nix` / `modules/home/umbriel-custom.nix` / `modules/home/mango-custom.nix` и всё, что лежит в `dotfiles/perso/`, внесены в gitignore, и pull их никогда не затрагивает.

Чтобы настроить интервал или ветку, переопределите их в `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # если здесь поставить false, config.roudix.autoupdate возьмёт обновление на себя, но без git pull
  roudix.autoupdate.interval = "6h";   # проверять каждые 6 часов вместо 1 часа
  roudix.autoupdate.branch   = "main"; # отслеживаемая ветка: "main" (стабильная), "testing" или "dev" — задаётся установщиком
}
```

Ветка выбирается в установщике (и в скрипте, и в графическом установщике ISO). Позже её можно сменить через **Roudix Switcher → System → Update branch**: перед пересборкой он также переключает ваш локальный `~/.config/roudix` на эту ветку.

Автообновление выполняет только fast-forward: если на вашей машине есть локальные коммиты, которых нет на GitHub (или история разошлась), оно их не трогает и вместо этого присылает уведомление.

Проверить последний запуск:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

Чтобы запустить обновление вручную в любой момент:

```fish
update
```

Он выполняет тот же pull (та же ветка, то же правило «только fast-forward», та же блокировка — он никогда не пересекается с уже идущим автообновлением), затем пересобирает систему и обновляет ваши Flatpak. Параметры см. в [`update`](aliases.ru.md#update).

Сборка может занимать до 2 часов, после чего systemd сдаётся. Если запуск прерван или неожиданно остановился (тайм-аут, сбой), отправляется уведомление; обычная ошибка уведомляет сама по себе. После автообновления `update --changes` показывает, что будет применено при следующей загрузке.

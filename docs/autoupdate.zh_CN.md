[English](autoupdate.md) · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · [Português (Brasil)](autoupdate.pt_BR.md) · [Русский](autoupdate.ru.md) · **简体中文** · [हिन्दी](autoupdate.hi.md) · [العربية](autoupdate.ar.md)

# 自动更新

当 `roudix.autoupdate.enable = true` 时，系统会每小时检查一次 GitHub（并在开机后 5 分钟检查一次）。
如果在所跟踪的分支（默认为 `main`）上检测到新的提交，它会执行 pull 并运行 `nh os boot path:...` — 新配置将在下次重启时生效。
你的 `local.nix`、`username.nix`、`hardware-configuration.nix` 文件，可选的 `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix`，以及 `dotfiles/perso/` 下的所有内容都已加入 gitignore，pull 绝不会触碰它们。

要配置检查间隔或分支，请在 `local.nix` 中覆盖：

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # 如果这里设为 false，config.roudix.autoupdate 会接手更新，但不会执行 git pull
  roudix.autoupdate.interval = "6h";   # 每 6 小时检查一次，而不是每 1 小时
  roudix.autoupdate.branch   = "main"; # 要跟踪的分支："main"（稳定）、"testing" 或 "dev" — 由安装程序设置
}
```

分支在安装程序中选择（脚本和 ISO 图形安装程序都是如此）。之后你可以在 **Roudix Switcher → System → Update branch** 中更改，它还会在重新构建之前把你本地的 `~/.config/roudix` 检出切换到该分支。

自动更新只会执行 fast-forward：如果你的机器上有尚未推送到 GitHub 的本地提交（或已经分叉），它不会触碰这些提交，而是通知你。

查看上一次运行情况：

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

随时手动触发一次更新：

```fish
update
```

它执行同样的 pull（相同的分支、相同的仅 fast-forward 规则、相同的锁，因此绝不会与正在运行的自动更新重叠），然后重新构建并更新你的 Flatpak。其选项见 [`update`](aliases.zh_CN.md#update)。

构建最长可持续 2 小时，之后 systemd 会放弃。如果运行被终止或意外停止（超时、崩溃），会发送通知；普通错误本身也会通知。自动更新之后，`update --changes` 会显示下次启动时将应用的内容。

[English](aliases.md) · [Français](aliases.fr.md) · [Español](aliases.es.md) · [Português (Brasil)](aliases.pt_BR.md) · [Русский](aliases.ru.md) · **简体中文** · [हिन्दी](aliases.hi.md) · [العربية](aliases.ar.md)

# 别名与函数

## 随处可用

| 别名 | 作用 |
|-------|--------|
| `rebuild` | 立即应用配置 |
| `update` | 拉取配置、重新构建 + switch、更新 Flatpak（见[下文](#update)） |
| `cleanup` | 删除旧世代 + 垃圾回收 |
| `noctalia-reload` | 无需注销即可重启 Noctalia |
| `dms-reload` | 无需注销即可重启 Quickshell |
| `caelista-reload` | 无需注销即可重启 Quickshell |
| `roudix-switch <de>` | 切换桌面环境（下次重启生效） |
| `roudix-kernel-switch <kernel>` | 切换内核变体（下次重启生效） |

### `update`

[自动更新](autoupdate.zh_CN.md)的手动版本：相同的仓库、相同的跟踪分支、相同的仅 fast-forward 规则（你的本地提交绝不会被触碰）。它以你的普通用户身份运行，只在必要时使用 `sudo`。

1. 对所跟踪的分支执行 `git pull --ff-only`（如果你在其他分支上，例如功能分支，则跳过）
2. `nh os switch`（带 `--boot` 时为 `nh os boot`）
3. 更新用户和系统的 Flatpak，然后移除未使用的运行时（失败不会中断）

你从 git 获得的 `flake.lock` 是 CI 已经构建并验证过的版本，因此单纯的 `update` **不会**升级 flake 输入。

| 选项 | 作用 |
|--------|--------|
| `-i`, `--inputs [name…]` | 同时在本地升级 flake 输入（全部，或仅指定的几个）。如果构建失败，会恢复 `flake.lock` |
| `-b`, `--boot` | 在下次启动时应用，而不是立即 switch |
| `-c`, `--check` | 仅报告是否有新的提交 |
| `-n`, `--dry` | 试运行（`nh --dry`）：不拉取、不升级、不激活、不更新任何内容 |
| `--changes` | 显示下次启动的系统与当前运行系统的差异（自动更新之后很有用） |
| `--log` | 显示上次运行的日志（保存在 `~/.local/state/roudix/update.log`） |
| `--no-inputs` | 跳过输入升级（与 `roudix.update.bumpInputs = true` 搭配时有用） |
| `--no-pull` / `--no-flatpak` | 跳过 pull / Flatpak 更新 |

```fish
update                    # pull + 重新构建 + switch
update --inputs           # 升级所有输入，然后重新构建
update --inputs nixpkgs   # 仅升级 nixpkgs
```

在一台跟踪 `dev` 并且总是需要最新输入的机器上，在 `local.nix` 中设置 `roudix.update.bumpInputs = true;`：之后单纯的 `update` 的行为就与 `update --inputs` 相同。

> 执行 `update --inputs` 之后，`flake.lock` 属于本地修改：请提交并推送它（或执行 `git checkout flake.lock`），否则如果期间 CI 修改过该 lock，下一次自动更新的 pull 可能会拒绝运行。

## 仅限 Niri、Hyprland 和 MangoWC

| 别名 | 作用 |
|-------|--------|
| `roudix-shell-switch <shell>` | 切换图形 shell（下次重启生效） |

### 用法

```fish
# 切换桌面环境
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde

# 切换内核变体 — 可选列表取决于 hardware.myGpu，见 docs/installation.md
# AMD/Intel (xddxdd)：
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — 选择较少，nvidia_cachyos 二进制缓存需要它)：
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# 纯 nixpkgs 内核 — 两种 GPU 路径下都可用，不在 CachyOS overlay 之内
# （在 Nvidia 上会回退为本地重新构建的 Nvidia 模块，没有 nvidia_cachyos 缓存）：
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# 切换图形 shell（仅限 Niri、Hyprland 和 MangoWC）
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # 仅适用于 hyprland
```

这三个命令都会自动编辑 `hosts/roudix/local.nix` 并运行 `nh os boot` — 无需手动重新构建。更改会在下次重启时生效。

> **注意：** `roudix-kernel-switch` 会根据你当前的 `hardware.myGpu`，自动写入 `hardware.myKernel` 或 `hardware.myKernelChaotic` — 请传入与你的 GPU 列表对应的变体名称（见上表）。

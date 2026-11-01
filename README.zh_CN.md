[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português (Brasil)](README.pt_BR.md) · [Русский](README.ru.md) · **简体中文** · [हिन्दी](README.hi.md) · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS 配置（Unstable）— 多种 Wayland 合成器（hyprland、niri、mangowc 和 umbriel）· Gnome 与 KDE · CachyOS 内核

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| 预览 |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Roudix 预览幻灯片：Umbriel、GNOME 和 KDE Plasma" width="900"/> |

<sub>个人定制 — 你的外观会因配置而异 👀</sub><br/>
<sub>Wayland 合成器留给你自行定制：Roudix 只提供 Noctalia、Dux Shell 以及（仅 Hyprland）Caelestia 的默认配置。</sub>

</div>

---

## 硬件

| 组件 | 型号 |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## 技术栈

| 层 | 选择 |
|-------|--------|
| 操作系统 | Roudix (NixOS unstable) |
| Kernel | CachyOS (内核变体请参见[功能](docs/features.md)或[安装](docs/installation.zh_CN.md)) |
| Bootloader | Limine（默认） · systemd-boot |
| Compositor | Niri （可滚动平铺） · Hyprland （动态平铺） · MangoWC · Umbriel （可滚动平铺，Noctalia 原生） |
| 图形 shell | Noctalia · Dux Shell · Caelestia |
| 桌面环境 | KDE Plasma · Gnome |
| 显示管理器 | DMS Greeter （仅 Dms） · Noctalia Greeter （仅 noctalia） · plasma-login-manager （仅 KDE） · GDM （仅 Gnome） |
| 终端 | 可配置 (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| Shell | Fish · Bash |
| 浏览器 | 可配置 (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| 文件管理器 | 可配置 (Nautilus, Thunar, Dolphin, Nemo) |
| 编辑器 | 可配置 (Zed, VS Code, Neovim, 无) |
| 聊天 | Discord (Vencord · vanilla · 无) + Matrix (Element · Cinny · 无) |
| 音乐 | 可配置 (Spotify + Spicetify, YouTube Music Desktop, 无) |

---

## 文档

| | |
|-|-|
| 🖥️ [桌面与 shell](docs/desktop.md) | 切换合成器和图形 shell，个人覆盖配置 (Niri, Hyprland, GNOME, KDE) |
| ⚡ [别名与函数](docs/aliases.zh_CN.md) | 所有 shell 别名和函数 — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [安装](docs/installation.zh_CN.md) | 自动与手动安装指南 |
| ✨ [功能](docs/features.md) | 按桌面环境划分的完整功能列表 |
| 🔄 [自动更新](docs/autoupdate.zh_CN.md) | 自动 git pull + 重新构建的配置 |

---

## 目录结构

```
roudix/
├── roudix-installer.sh              # 基于 Bash 的安装脚本
├── flake.nix                        # 输入与输出
├── flake.lock
├── docs/                            # 文档
│   ├── desktop.md                   # 桌面环境与图形 shell
│   ├── aliases.md                   # Shell 别名与函数
│   ├── installation.md              # 安装指南
│   ├── features.md                  # 功能列表
│   ├── features.fr.md               # 功能列表（法语）
│   └── autoupdate.md                # 自动更新配置
│
├── hosts/
│   └── roudix/                      # 单一主机 — 桌面环境由 roudix.desktop.type 选择
│       ├── configuration.nix
│       ├── username.nix             # 已加入 gitignore — 你的用户名（见安装）
│       ├── local.nix                # 已加入 gitignore — 你个人的系统覆盖配置
│       ├── local.nix.example        # 复制为 local.nix 即可开始
│       └── hardware-configuration.nix
│
├── dotfiles/                        # 由 Home Manager 管理的原始配置文件
│   ├── easyeffects/                 # EasyEffects 预设
│   ├── fastfetch/
│   │   └── roudix.txt               # fastfetch 的默认 Roudix ASCII 标志
│   # niri/、niri-dms/ 已移除 — niri 配置现在完全
│   # 由 Nix 原生管理（见下方 modules/home/desktop/niri/）。
│   ├── hyprland/                    # Hyprland 配置（Lua）— 所有图形 shell 共用一棵目录树
│   │   ├── hyprland.lua             # 入口：加载 config/ 中的模块
│   │   └── config/
│   │       ├── shell.lua            # 根据 ROUDIX_HYPR_SHELL 选择 shell（noctalia / dms / caelestia）
│   │       ├── shells/              # 各 shell 的快捷键与集成（noctalia.lua、dms.lua、caelestia.lua）
│   │       ├── binds/common.lua     # 所有 shell 共用的快捷键
│   │       ├── rules/               # 窗口规则（common.lua、apps.lua、gaming.lua）
│   │       ├── ws.lua               # 共享的工作区表（供 workspaces、binds 和 rules 使用）
│   │       ├── workspaces.lua       # 工作区规则
│   │       ├── monitors.lua / input.lua / layout.lua / decorations.lua / animations.lua
│   │       ├── defaults.lua / colors.lua / environment.lua / autostart.lua / misc.lua
│   │       └── nix-noctalia.lua     # 加载实时 Noctalia 主题（由 matugen 生成）
│   │   # config/nix-plugins.lua 和 config/nix-apps.lua 由 Nix 生成（不在仓库中）
│   └── perso/                       # 个人配置（已加入 gitignore）
│
├── pkgs/
│   ├── roudix-branding              # Roudix 品牌包
│   ├── roudix-kernel-switcher       # Roudix Kernel Switcher 图形界面包
│   ├── roudix-switcher/             # Roudix 设置图形界面（桌面、游戏、编辑器、终端、浏览器、shell、文件管理器、聊天、系统、集成）
│   └──   roudix-scheduler-switcher    # Scheduler Switcher 图形界面包
│
└── modules/
    ├── system/                      # NixOS 系统级模块
    │   ├── desktop/                 # 桌面环境模块（NixOS 级）
    │   │   ├── default.nix          # 桌面选项（roudix.desktop.type + roudix.desktop.shell）
    │   │   └── niri.nix / hyprland.nix / gnome.nix / kde.nix / mangowc.nix / umbriel.nix
    │   │
    │   ├── boot/                    # 引导程序、内核与 CPU
    │   │   ├── boot.nix             # Limine/systemd-boot + 多系统启动项
    │   │   ├── boot.local.nix       # 已加入 gitignore — 你个人的启动项
    │   │   ├── boot.local.nix.example
    │   │   ├── kernel.nix           # 内核变体选择 — CachyOS 变体 + 纯 nixpkgs
    │   │   ├── cpu.nix              # Intel/AMD 微码 + i2c 模块
    │   │   └── bootloader/          # Limine 壁纸资源
    │   │
    │   ├── apps/                    # 应用选择模块（每个对应一个 roudix.* 选项）
    │   │   ├── apps.nix / appimage.nix / flatpak.nix / browser.nix / discord.nix
    │   │   ├── telegram.nix / matrix.nix / mail-client.nix / music-player.nix
    │   │   ├── video-player.nix / torrent-client.nix / password-manager.nix
    │   │   └── filemanager.nix / editor.nix / terminal.nix / spicetify.nix / content-creation.nix
    │   │
    │   ├── virtualization/          # QEMU/KVM、容器、虚拟机客户机调整、Waydroid
    │   │   └── virtualization.nix / containers.nix / vm-guest.nix / waydroid.nix
    │   │
    │   ├── rgb/                     # RGB 控制器路由
    │   │   ├── default.nix          # roudix.rgb 选项（openlinkhub / openrgb / none）
    │   │   └── openlinkhub.nix / openrgb.nix
    │   │
    │   ├── gaming/                  # Steam、Gamescope、ananicy-cpp、tuned-adm、SCX 调度器
    │   │   └── gaming.nix / scx.nix
    │   │
    │   ├── gpu/                     # GPU 配置（AMD/NVIDIA/Intel/VM + mesa-git）
    │   │
    │   ├── autoupdate.nix       # 配置变更时自动 git pull + 重新构建
    │   ├── binary-caches.nix    # Nix 二进制缓存（substituters + 受信任密钥）
    │   ├── common.nix           # 共享的系统配置（所有主机）
    │   ├── desktop-integration.nix  # 为裸合成器提供的密钥环 + xdg-desktop-portal 栈
    │   ├── environment.nix      # 环境变量
    │   ├── fstrim.nix           # SSD/NVMe 的 fstrim
    │   ├── hosts-gta.nix        # BattlEye hosts 屏蔽（GTA 修复，可选）
    │   ├── icon-theme.nix       # 系统级图标主题选择
    │   ├── keyboard.nix         # 图形（Wayland）键盘布局/变体
    │   ├── pipewire.nix         # PipeWire 音频 + rnnoise 降噪
    │   ├── shell.nix            # 默认 shell（fish/bash）
    │   ├── update.nix           # Flake 更新配置
    │   ├── roudix-update.nix    # `update` 命令（pull + 重新构建 + Flatpak），脚本位于 roudix-update.sh，shell 补全位于 completions/
    │   └── version.nix          # Roudix 系统品牌（os-release、distroName）
    │   # 终端/文件管理器：通过 hosts/roudix/ 中的 local.nix 选择你喜欢的
    │
    └── home/                        # Home Manager 用户级模块
        ├── common.nix               # 共享的 home 配置（所有用户和桌面环境）
        ├── bash.nix                 # Bash shell 配置 + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + fish 自动启动
        ├── fish.nix                 # Fish shell + 别名 + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # 用户游戏软件包（proton、mangohud...）
        ├── git.nix                  # Git 配置
        ├── mangohud.nix             # MangoHud 覆盖层（各桌面环境共用）
        ├── papirus-icon.nix         # Papirus 图标主题（各桌面环境共用）
        ├── papirus-folders.nix      # Papirus 文件夹颜色配置（共用）
        ├── tela-icon.nix            # Tela 图标主题（各桌面环境共用）
        ├── spicetify.nix            # Spotify + Spicetify（Comfy 主题）
        ├── ssh.nix                  # SSH + GitHub
        ├── shell-modules.nix        # 共享的 shell 模块导入（noctalia、dms、caelestia）
        └── desktop/                 # 每个桌面环境一个文件夹 — Home Manager 一侧，对应 modules/system/desktop/
            ├── default.nix          # 无条件导入全部六个（每个内部都由 lib.mkIf 保护）
            ├── gnome/
            │   ├── default.nix      # 壁纸、主题、图标、光标
            │   └── _extensions.nix  # GNOME 扩展 — 软件包、启用的 UUID、dconf 设置
            ├── kde/default.nix      # plasma-manager 配置（壁纸、面板、锁屏）
            ├── hyprland/default.nix # 感知 shell（noctalia/dms/caelestia）、插件、软件包
            ├── mangowc/default.nix  # 生成的 mango config.conf/apps.conf、软件包
            ├── niri/                # programs.niri.settings，按主题拆分，感知 shell
            │   ├── default.nix      # 组装设置、实时主题 include、软件包
            │   ├── _general.nix     # 环境、自动启动、光标（感知 shell）
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # 输出 + 命名工作区
            │   ├── _ws.nix          # 共享的工作区图标字形常量
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # 将实时主题的 `include` 追加到 niri-flake 渲染出的配置中
            └── umbriel/             # programs.umbriel.settings，按主题拆分（仅限 Noctalia）
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # 加载 noctalia.toml（Umbriel 原生的实时主题 include）
```

---

## Flake 输入

| 输入 | 来源 |
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

## 另见

| 项目 | 描述 |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | 由 Gaming Linux FR 制作的基于 NixOS 的游戏发行版 |

---

## 个人 dotfiles

个人配置文件位于 `dotfiles/perso/` — 它们已加入 gitignore（`dotfiles/perso/README.md` 除外），`git pull` 和自动更新程序绝不会触碰它们。

结构与用法请参见 [`dotfiles/perso/README.md`](dotfiles/perso/README.md)。

对于合成器级别的覆盖配置（显示器、快捷键、间距…），请改用生成的用户覆盖文件 — 它们由 home-manager 管理，不受 `git pull` 影响。详见[桌面与 shell](docs/desktop.md#personal-compositor-overrides)。

## 开发

```bash
nix develop     # 开发 shell：just、ruff、statix、deadnix、shellcheck、gettext
just            # 列出所有任务
just ci         # CI 检查的全部内容（评估每个主机、lint、Python、翻译）
```

安装程序使用 gettext 进行翻译 — 参见 [安装程序 › 翻译](iso/roudix-installer/README.md#traductions)。

## 许可证
   MIT — 参见 [LICENSE](LICENSE)。Roudix Store 采用 GPL-2.0-only，部分
   第三方文件保留其各自的许可证：参见 [THIRD_PARTY.md](THIRD_PARTY.md)。

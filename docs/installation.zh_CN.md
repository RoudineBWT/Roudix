[English](installation.md) · [Français](installation.fr.md) · [Español](installation.es.md) · [Português (Brasil)](installation.pt_BR.md) · [Русский](installation.ru.md) · **简体中文** · [हिन्दी](installation.hi.md) · [العربية](installation.ar.md)

# 安装

根据你的起点，有三种方式可以运行 Roudix：

| 情况 | 使用 |
|-----------|-----|
| 全新机器，尚未安装任何系统 | **Roudix ISO** — 直接启动进入图形安装程序（包含分区） |
| 已安装 NixOS（官方 ISO、其他发行版的 NixOS 安装、虚拟机…） | **`roudix-installer.sh`** — 将 Roudix flake 部署到你现有的安装上 |
| 你想掌控每一个步骤，或脚本无法覆盖你的情况 | **手动安装**（见下文） |

## 方案 A — Roudix ISO（全新安装推荐）

ISO 自带我们自己的 GTK4/libadwaita 图形安装程序（`roudix-installer`），运行在 GNOME 临场会话之上，并通过 [disko](https://github.com/nix-community/disko) 为你完成磁盘分区 — 无需事先安装 NixOS。

1. 获取最新的 ISO：打开仓库的 **Actions** 标签页 → **💿 Build Roudix ISO** 工作流 → 如果列表中没有近期构建，就运行它（`workflow_dispatch`），然后打开该次运行，从作业摘要中获取下载链接（ISO 托管在 Cloudflare R2 上，而不是 GitHub 构件）。
2. 把它写入 U 盘（例如使用 `dd`、Ventoy、Rufus…）并从 U 盘启动。
3. 登录后安装程序窗口会自动打开（它会用 `sudo` 重新启动自己：临场会话需要 root 权限来运行 disko/`nixos-install`）。依次完成各页面：磁盘选择、内核、桌面、浏览器、编辑器、Discord、游戏应用、区域设置、时区、键盘布局、RGB 控制器以及可选模块。
4. 确认后，它会对磁盘分区（disko），把 ISO 内置的 Roudix flake 复制到 `/mnt/etc/nixos`，并运行 `nixos-install --flake /mnt/etc/nixos#roudix`。

> **注意：** 如果临场会话的键盘与你的实体键盘不一致，启动菜单还提供键盘布局特化项（US/BE/FR/DE/CH/UK）— 请在启动安装程序之前选好。

这一路径完全取代下面两个步骤（无需 `roudix-installer.sh`，也无需手动步骤）— 重启后直接看安装完成之后的内容即可。

## 方案 B — 已经安装了 NixOS

如果已经安装了 NixOS（通过官方稳定版/unstable ISO 或其他方式），只想在上面部署 Roudix，有两个安装程序：图形版（在桌面会话中使用）和 bash 脚本（在纯 TTY 下也能用）。

> **注意：** 请先用 [stable](https://nixos.org/download/) 或 [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165) ISO 安装 NixOS，然后运行下面的某个安装程序，或按手动安装步骤操作。

### B1 — 图形安装程序（桌面环境下推荐）

与 ISO 中相同的向导，只是没有磁盘页面。请在你想保留的账户下运行：

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **不会清除任何内容。** 配置会放到 `~/.config/roudix`（已有的文件夹会被移到一边，绝不会删除），然后 `nixos-rebuild boot` 构建 Roudix 并安排在下次启动时启用。你当前的系统仍保留在启动菜单中。
- **你的 `/etc/nixos` 会被备份** 到 `/var/backups/roudix/nixos-<date>/`，并附带 `RESTORE.txt`（上一代系统、引导程序、`stateVersion` 以及回退所需的确切命令）。`hardware-configuration.nix` 原样复用，绝不覆盖。
- **先模拟。** 摘要页上的*模拟*按钮会在临时文件夹中生成配置，检查每个选项是否都已写入，并让 Nix 对整个系统求值。你的机器上不会有任何改动。
- 预检警告：`/boot` 剩余空间不足（512 MB 的 EFI 分区很容易满）、更换引导程序、较旧的 `system.stateVersion`。
- 通过 polkit 对话框请求管理员密码（需要 polkit 代理，即任何正常的桌面会话）。

**如何回退：** 在启动菜单中选择上一代系统，然后执行 `sudo nixos-rebuild switch --rollback`。如果机器完全无法启动，`RESTORE.txt` 会说明如何通过临场 U 盘恢复你原来的配置。

### B2 — Bash 脚本（TTY / 无图形会话）

**下载 roudix-installer 脚本**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

安装程序以交互方式处理所有事情：
- 询问要安装并跟踪哪个分支（`main` = 稳定，`testing`，`dev`），克隆它，生成 `hardware-configuration.nix`，并创建所有本地配置文件
- **自动检测其他操作系统**，通过 EFI NVRAM（`efibootmgr`）— 无需手动查找 PARTUUID
- **自动检测 GPU 和 CPU**（`lspci` / `/proc/cpuinfo`）— 预先选好并请你确认
- **检测是否运行在虚拟机中**（`systemd-detect-virt`）— 预先启用虚拟机客户机模式，并提示 GPU/CPU 检测可能不准确
- 询问内核、桌面、浏览器、编辑器、Discord、游戏应用、区域设置、时区、键盘映射、RGB 控制器和可选模块
- 构建并应用配置

---

## 方案 C — 手动安装

> ⚠️ **在重新构建之前，请仔细完成每一步。**

### 1. 克隆仓库

> **如果未安装 `git`**（全新的 NixOS 安装）：

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **否则：**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. 设置你的用户名

用你的用户名创建 `username.nix` 文件：

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> 该文件已加入 gitignore — `git pull` 绝不会覆盖它。

### 3. 替换 hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. 创建你的本地配置

**不要直接编辑 `configuration.nix` 或 `modules/home/common.nix`** — 它们会在 `git pull` 时被覆盖。
请改为创建你自己的本地覆盖文件（全部已加入 gitignore）：

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp modules/home/local.nix.example modules/home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

编辑 `hosts/roudix/local.nix` 以匹配你的硬件：

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri"、"hyprland"、"mangowc"、"umbriel"、"gnome" 或 "kde"
  hardware.myGpu      = "amd";                # "amd"、"nvidia" 或 "intel"
  hardware.myCpu      = "intel";              # "intel" 或 "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # xddxdd 内核 — 当 hardware.myGpu != "nvidia" 时使用
  hardware.myKernelChaotic = "cachyos";            # Chaotic-Nyx 内核 — 仅当 hardware.myGpu == "nvidia" 时使用
  roudix.boot.bootloader = "limine";          # "limine" 或 "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave"、"helium"、"vivaldi"、"firefox"、"librewolf"、"chromium" 或 []
  roudix.zen.enable   = false;                # 设为 true 可同时安装 Zen Browser (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub"、"openrgb" 或 "none" — 见下文
  roudix.mesa.useGit  = false;                # true = mesa-git（实验性，构建可能失败），false = nixpkgs 稳定版
  roudix.matrixClient = "none";               # "element"、"cinny" 或 "none"
  roudix.discord      = "vencord";            # "vencord"、"vanilla" 或 "none"
  roudix.editor       = "zed";                # "zed"、"vscode"、"neovim" 或 "none"

  # ── 游戏应用（默认全部为 true — 禁用你不想要的）────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── 裸合成器集成（仅限 niri/hyprland/mangowc/umbriel）───────
  roudix.desktopIntegration = "gnome";        # "gnome" 或 "kde" — 密钥环 + xdg-desktop-portal 栈；对 gnome/kde 会话无影响

  # ── 区域设置 / 时区 ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # 参见 https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # 必须与 time.timeZone 一致
  i18n.defaultLocale              = "en_US.UTF-8";     # 系统区域设置
  console.keyMap                  = "us";              # 控制台键盘布局 — 仅限 TTY，在图形会话启动之前

  # ── 图形（Wayland）键盘布局 — 独立于 console.keyMap ─
  # 对 GNOME/KDE 无效，它们通过各自的设置守护进程管理自己的布局。
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl"、"nodeadkeys"、"bepo"、"dvorak"、"colemak"、""（无）
}
```

**RGB 控制器选项：**

| 值 | 说明 |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — 完整的 Corsair 配置（iCUE Link、Commander...） |
| `openrgb` | OpenRGB — 多品牌混用（Razer、ASUS、MSI...） |
| `none` | 不管理 RGB |

**内存 RGB（仅限 OpenLinkHub）：**

如果你选择了 `openlinkhub`，还可以为你的 Corsair DDR4/DDR5 内存启用 RGB 控制。把下面几行添加到 `hosts/roudix/local.nix`：

```nix
roudix.memory.enable = true;                  # 通过 SMBus 启用内存 RGB
roudix.memory.type   = "ddr5";                # "ddr4" 或 "ddr5"
roudix.memory.smBus  = "i2c-9";              # 查找方法：sudo i2cdetect -l（查找 "SMBus"）
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # 查找方法：sudo dmidecode -t memory | grep 'Part Number'
```

在设置之前，先找出正确的值：

```bash
# 如果缺少所需工具，请先安装（全新的 NixOS 安装）
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# 找到你的 SMBus（包含 "SMBus"、"i801"、"piix4" 或 "nforce" 的那一行）
sudo i2cdetect -l

# 找到你的内存部件编号
sudo dmidecode -t memory | grep 'Part Number'
```

> **注意：** `roudix.memory.enable` 会自动把 `acpi_enforce_resources=lax` 作为内核参数应用，并把 `spd5118`（DDR5）或 `ee1004`（DDR4）加入黑名单以释放 SMBus。OpenLinkHub 的 `config.json` 会在激活时自动修补。

**常用时区值：**

| 时区 | 地区 |
|----------|--------|
| `Europe/Brussels` | 比利时 |
| `Europe/Paris` | 法国 |
| `Europe/London` | 英国 |
| `Europe/Berlin` | 德国 |
| `Europe/Amsterdam` | 荷兰 |
| `America/New_York` | 美国东部 |
| `America/Los_Angeles` | 美国西部 |
| `Asia/Tokyo` | 日本 |
| `UTC` | 通用 |

**常用区域设置值：**

| 区域设置 | 语言 |
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

**常用控制台键盘映射值：**

| 键盘映射 | 布局 |
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

> **注意：** `environment.sessionVariables.TZ` 必须始终与 `time.timeZone` 一致 — 两者都控制时区，一个在系统层面，一个在会话层面。

编辑 `modules/home/local.nix` 以进行个人的 home-manager 覆盖（额外软件包、dotfiles、别名、fastfetch...）：

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> 所有可用的覆盖选项（包括 fastfetch 自定义）请参见 `modules/home/local.nix.example`。

### 5. 配置内核

Roudix 根据你的 GPU 使用**两个不同的内核来源**：

- **`hardware.myGpu != "nvidia"`**（AMD 或 Intel）→ 内核来自 [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel)，通过 `hardware.myKernel` 选择。无需担心 Nvidia 模块，因此可以使用完整的 36 个变体。
- **`hardware.myGpu == "nvidia"`** → 内核来自 **Chaotic-Nyx**，通过 `hardware.myKernelChaotic` 选择。这样才能获得 **`nvidia_cachyos`**，一个与其内核匹配的预编译 Nvidia 驱动 — 否则每次内核升级时 Nvidia 内核模块都要在本地重新构建。这里的变体集合刻意更小（Chaotic-Nyx 没有发布那么多变体，而且 `-lto` 变体更容易破坏像 Nvidia 这样的树外模块）。

两个选项还接受少数**纯 nixpkgs 内核**，它们完全不在各自的 CachyOS overlay 之内 — 如果你只想要不带 CachyOS 补丁的普通内核，它们很有用：`zen`、`nixpkgs-lts`、`nixpkgs-latest`、`nixpkgs-testing`、`xanmod-lts`、`xanmod-latest`。在 Nvidia 路径上，它们会跳过 `nvidia_cachyos` 缓存，改为在本地重新构建 Nvidia 模块（见 `nvidia.nix`）。

**更新的 nixpkgs 内核 — `hardware.myKernelSource`：** 这些 nixpkgs 内核默认跟随主 `nixpkgs` 输入（nixos-unstable）。把 `hardware.myKernelSource` 设为 `"master"` 或 `"staging-next"`，即可**只**从 NixOS/nixpkgs 的该分支获取内核（以及针对它构建的树外模块，例如 Nvidia），从而更早获得内核更新 — 系统其余部分不受影响。可选值：`"nixpkgs"`（默认）、`"master"`、`"staging-next"`。注意事项：这样的内核可能尚未进入二进制缓存，因此请预期较长的本地构建；`staging-next` 还带有进行中的工具链变更，所以在三者中风险最高。它对 `cachyos-*` 内核无效（会显示警告）。设置之后，请运行一次 `nix flake lock`，以锁定新的输入。

**`hardware.myKernel` 变体（xddxdd — 仅限 AMD/Intel）：**

| 变体 | 说明 |
|---------|-------------|
| `zen` | 纯 `linuxPackages_zen` (nixpkgs) — 不在 xddxdd overlay 之内 |
| `nixpkgs-lts` | nixpkgs 默认 LTS 内核（未修改） — 不在 xddxdd overlay 之内 |
| `nixpkgs-latest` | nixpkgs 最新 mainline 内核（未修改） — 不在 xddxdd overlay 之内 |
| `nixpkgs-testing` | 纯 nixpkgs `linux_testing`（RC/mainline） — 不在 xddxdd overlay 之内 |
| `xanmod-lts` | XanMod LTS 分支（`linuxPackages_xanmod`，nixpkgs）— 性能 governor、lazy 抢占、BBRv3 |
| `xanmod-latest` | XanMod 主分支（`linuxPackages_xanmod_latest`，nixpkgs） |
| `cachyos-latest` | 标准的最新 CachyOS 内核 |
| `cachyos-latest-v2` | 针对 x86_64-v2 优化 |
| `cachyos-latest-v3` | 针对 x86_64-v3 优化（推荐用于现代 CPU） |
| `cachyos-latest-v4` | 针对 x86_64-v4 优化（AVX-512，仅限非常新的 CPU） |
| `cachyos-latest-zen4` | 针对 AMD Zen 4 优化 |
| `cachyos-latest-lto` | LTO 构建，性能更好 |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3（性能最佳，仅限现代 CPU） |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | 长期支持的 CachyOS 内核 |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + 针对 x86_64-v3 优化 |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3（稳定 + 性能） |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | BMQ 调度器 |
| `cachyos-bmq-lto` | BMQ 调度器 + LTO |
| `cachyos-bore` | BORE 调度器（交互性更好） |
| `cachyos-bore-lto` | BORE 调度器 + LTO |
| `cachyos-deckify` | 针对 Steam Deck 优化 |
| `cachyos-deckify-lto` | 针对 Steam Deck 优化 + LTO |
| `cachyos-eevdf` | EEVDF 调度器 |
| `cachyos-eevdf-lto` | EEVDF 调度器 + LTO |
| `cachyos-hardened` | 安全加固内核 |
| `cachyos-hardened-lto` | 安全加固 + LTO |
| `cachyos-rc` | 候选发布版 — 最前沿，可能不稳定 |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | 实时 + BORE 调度器 |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | 针对服务器优化（无桌面调优） |
| `cachyos-server-lto` | 针对服务器优化 + LTO |

**`hardware.myKernelChaotic` 变体（Chaotic-Nyx — 仅限 Nvidia）：**

| 变体 | 说明 |
|---------|-------------|
| `cachyos` | 默认 — LTO + BORE 调度器，附带匹配的 `nvidia_cachyos` |
| `cachyos-lts` | 长期支持 |
| `cachyos-server` | 针对服务器优化（无桌面调优） |
| `cachyos-hardened` | 安全加固 |
| `zen` | 纯 `linuxPackages_zen` (nixpkgs) — Nvidia 模块在本地重新构建 |
| `nixpkgs-lts` | 纯 nixpkgs LTS — Nvidia 模块在本地重新构建 |
| `nixpkgs-latest` | 纯 nixpkgs 最新 mainline — Nvidia 模块在本地重新构建 |
| `nixpkgs-testing` | 纯 nixpkgs `linux_testing`（RC） — Nvidia 模块在本地重新构建 |
| `xanmod-lts` | XanMod LTS (nixpkgs) — Nvidia 模块在本地重新构建 |
| `xanmod-latest` | XanMod 主分支 (nixpkgs) — Nvidia 模块在本地重新构建 |

> **NVIDIA 说明：** 仅支持 GTX 20xx / RTX 系列及更新型号。RTX 20xx+（Turing+）默认启用开源驱动。不支持 GTX 10xx/16xx。

> **Spicetify Comfy 主题说明：** 首次构建之后，请手动复制 color.ini：
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/apps/media/spicetify/Comfy/color.ini
> ```
> 然后运行 `rebuild` 使其生效。

### 6. 更新磁盘挂载

在 `hosts/roudix/local.nix` 中，添加带有你自己 UUID 的 `lib.mkForce` 块（如果没有第二块磁盘则跳过）：

```bash
lsblk -f  # 查找你磁盘的 UUID
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. 配置 Limine 多系统启动（可选）

> 如果你的机器上只有 NixOS，请跳过此步骤。

Limine 可以启动位于其他磁盘上的其他操作系统。`boot.local.nix` 控制额外的启动项 — 它已加入 gitignore，绝不会被 `git pull` 覆盖。

**不要直接编辑 `modules/system/boot/boot.nix`** — 它会在 `git pull` 时被覆盖。

#### 如果你使用了自动安装程序

安装程序已通过 EFI NVRAM（`efibootmgr`）自动检测到你的其他操作系统，并为你写好了 `boot.local.nix` — 无需任何手动操作。你可以查看结果：

```bash
cat modules/system/boot/boot.local.nix
```

#### 如果你是手动安装

**获取你的 PARTUUID：**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

查找文件系统类型为 `vfat`、标签为 `EFI system partition` 的分区 — 它们就是你的 ESP。

**编辑 `modules/system/boot/boot.local.nix`** 并添加你的启动项：

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

> **提示：** UUID 之后的 EFI 路径取决于另一个操作系统所用的引导程序。常见路径：
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - 任意发行版（备用）： `/EFI/BOOT/BOOTX64.EFI`

如果没有其他操作系统要添加，让 `extraEntries` 保持为空即可：

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` 已列入 `.gitignore` — 绝不会被 `git pull` 覆盖。

### 8. 更新 git 配置

`modules/home/dev/git.nix` 已加入 gitignore（与 `local.nix` 一样）— 复制受版本控制的模板并填写你的身份信息：

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

- `init.defaultBranch = "main"` — 当你对新仓库执行 `git init` 时，第一个分支使用的名称（不影响本仓库自己的分支，只影响你自己创建的分支）。
- `pull.rebase = false` — 当本地分支与远程分支分叉时 `git pull` 的行为：`false` 为合并（创建一个 merge 提交，默认且最简单的行为），`true` 则把你的本地提交变基到远程之上（线性历史，但会改写你的提交 — 如果你对 rebase 冲突不熟悉，请避免）。对个人配置仓库而言，`false` 是更安全的选择。

> 如果文件缺失，`common.nix` 会直接跳过它 — 在你复制它之前，Home Manager 根本不会配置 git，但不会有任何问题。

### 9. 启用/禁用可选模块

在 `hosts/roudix/local.nix` 中：

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + 每日自动更新
roudix.fstrim.enable         = true;   # 推荐用于 SSD/NVMe
roudix.virtualization.enable = false;  # 为 QEMU/KVM 启用
roudix.vmGuest.enable        = true;   # 仅在虚拟机内启用
roudix.hosts.gtaFix.enable   = true;   # 屏蔽 BattlEye 遥测（GTA 修复）
roudix.autoupdate.enable     = true;   # 有变更时自动 git pull + nh os boot
roudix.zen.enable            = false;  # 安装 Zen Browser（默认禁用）
roudix.mesa.useGit           = false;  # true = mesa-git（实验性，最前沿 — 构建可能失败），false = nixpkgs 稳定版
roudix.boot.bootloader       = "limine";  # "limine" 或 "systemd-boot"
roudix.matrixClient          = "none"; # "element"、"cinny" 或 "none"
```

> **提醒：** 如果你设置了 `roudix.autoupdate.enable = true`，还要配置间隔：
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. 自定义 fastfetch（可选）

默认情况下，Roudix 在 fastfetch 中显示它的 ASCII 标志。你可以在 `modules/home/local.nix` 中覆盖它，而无需改动 git：

```nix
# 使用自定义图片（需要 kitty 终端）
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# 使用自定义 ASCII 文件
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# 覆盖整个 fastfetch 配置（替换全部）
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` 会覆盖整个 Roudix 默认配置。不使用它时，你的键会与默认值合并。
> 更多示例请参见 `modules/home/local.nix.example`。

### 11. 构建

> **如果尚未启用 flakes 和 nix-command**（全新的 NixOS 安装）：

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **否则：**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

构建完成后，今后的所有操作都使用 fish 别名。

> 三个 `local.nix` 文件和 `boot.local.nix` 都已列入 `.gitignore` — 绝不会被 `git pull` 覆盖。

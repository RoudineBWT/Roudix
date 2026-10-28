[English](features.md) · [Français](features.fr.md) · [Español](features.es.md) · [Português (Brasil)](features.pt_BR.md) · [Русский](features.ru.md) · **简体中文** · [हिन्दी](features.hi.md) · [العربية](features.ar.md)

# 功能

## 内核与性能

- 启用 NTSync 的 CachyOS 内核（`ntsync` 模块）
- 两个内核提供方，由 `hardware.myGpu` 自动选择：
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel)，36 个变体（`hardware.myKernel`）
  - Nvidia → Chaotic-Nyx，4 个变体（`hardware.myKernelChaotic`）— 附带 `nvidia_cachyos`，一个与其内核配套的预编译驱动，因此内核升级时无需在本地重新编译 Nvidia 模块
- 两个提供方都可以选择原版 nixpkgs 内核，完全独立于 CachyOS overlay — `zen`（`linuxPackages_zen`）、`nixpkgs-lts`、`nixpkgs-latest`、`nixpkgs-testing`（RC/mainline）、`xanmod-lts` / `xanmod-latest`（XanMod）。在 Nvidia 上，这些内核会回退到本地重新编译的 Nvidia 模块（没有 `nvidia_cachyos` 缓存）
- `hardware.myKernelSource`（`nixpkgs` / `master` / `staging-next`）只会从较新的 nixpkgs 中获取这些 nixpkgs 内核，以便更早升级内核，而不影响系统的其余部分
- 启用 ZRAM（100% 内存，zstd，swappiness 150）
- 禁用 zswap
- 自动配置 CPU 微码（Intel 或 AMD）
- Intel：自动应用 `split_lock_detect=off`
- 启用 ananicy-cpp（进程优先级守护进程，使用 CachyOS 规则）
- 支持 SCX 调度器 — 热切换，无需重启（bpfland、lavd、flash、p2dq、rusty…），通过 Kernel Switcher 图形界面操作 — 通过 `scx-switch` 只需输入一次密码，即可一次性完成 ananicy-cpp 的停止/启动和调度器切换 — **注意：** SCX 在重启后不会保留；重启后 ananicy-cpp 会自动重新启动，需要通过 Kernel Switcher 图形界面重新应用调度器

## 启动

- Limine 引导程序（默认）— 现代、快速、支持多磁盘 — 或 systemd-boot，可通过 `roudix.boot.bootloader` 选择
- 自动将 UEFI 启动项重命名为 "Roudix"
- 多系统启动菜单（Windows、位于不同 ESP 上的其他 Linux 发行版）
- 启动标签显示 Roudix 名称 + NixOS 发行版本

## 游戏

- Steam + Proton-GE + Proton-CachyOS（x86_64-v3）+ Gamescope（gamescope-wsi，会话默认禁用）
- 预先配置好 OBS 捕获所需的环境变量（通过 `environment.sessionVariables` 设置 `OBS_VKCAPTURE`）
- 自定义横向 MangoHud 悬浮层（`Powered By Roudix` 标签）
- 手柄支持（Steam Hardware + game-devices-udev-rules）
- 为 Wine/Steam 提供 32 位支持
- `game-performance` 包装器 — 在游戏运行期间切换到专用的 `tuned-adm` 性能配置，通过 `systemd-run --user --scope` cgroup 进行跟踪（因此即使 Steam 重新 fork/分离也不受影响），并在退出时恢复（用法：在 Steam 启动选项中填写 `game-performance %command%`）— 有意禁用 GameMode（在此与 ananicy-cpp 不兼容）
- 全系统提供 `ffmpegthumbnailer`（文件管理器中的视频缩略图）
- KDE 上使用 `protonup-qt`，其他桌面环境使用 `protonplus`
- Heroic、Lutris、Faugus Launcher、Prism Launcher（Minecraft，或使用 Modrinth App 作为替代 — `roudix.gaming.apps.modrinth.enable`）以及 Vintage Story（通过 roudix-caches）
- 每个游戏应用都可通过 `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` 单独启用/禁用（默认全部为 `true`）
- 可选的 [Millennium](https://github.com/SteamClientHomebrew/Millennium) 魔改 Steam 客户端（主题 + 插件）— 默认关闭，通过 `roudix.gaming.steam.millennium.enable = true` 启用（或在安装程序中启用）。非官方 mod；`game-performance` 的沙盒调整和 Proton 兼容工具仍可正常使用，改回 `false` 即可恢复原版 Steam
- 可选的类主机游戏模式：`roudix.gaming.gamescopeSession.enable` 会在登录界面添加一个 "Steam (Gaming Mode)" 会话（在 gamescope 中运行 Steam Big Picture，支持 VRR/HDR/MangoApp，启动时检测刷新率）。在 Steam 中点击"切换到桌面"会打开你的桌面，而 "Return to Gaming Mode" 应用可以直接返回游戏，无需经过登录界面。基于 GLF-OS；支持 niri、umbriel、GNOME、KDE、Hyprland 和 MangoWC
- 可选的 Decky Loader（Steam 插件），通过 `roudix.gaming.gamescopeSession.decky.enable` 启用，从 Jovian-NixOS 的 flake input 获取（用 `nix flake update jovian` 更新，无需手动维护 sha）；没有二进制缓存，因此首次重建时会在本地编译

## 桌面（Niri）

- Niri 可滚动平铺式 Wayland 合成器 — 通过 [niri-flake](https://github.com/epireyn/niri-flake)（epireyn）提供，默认使用 `niri-unstable`，并预先配置了 `niri-epireyn.cachix.org` 二进制缓存
- 配置是 Nix 原生的（`programs.niri.settings`），按主题拆分（general、animations、input、layout、outputs、binds、rules），并在构建时通过 `niri validate` 校验 — 配置有误会让构建失败，而不是在登录时让合成器崩溃
- Noctalia/DMS 的实时主题同步（由 matugen/DMS 生成的颜色、alt-tab、模糊）通过在生成的配置中追加一条 `include` 来保留，而不是静态写死
- Noctalia（v5）现代化 shell
- xdg-desktop-portal-gnome + gtk（已配置屏幕录制和远程桌面 portal）
- Bibata Modern Ice 光标（24 px）
- adw-gtk3 + Papirus 图标 + Papirus Folders
- Element Desktop 搭配 gnome-libsecret / kwallet6（根据桌面环境自动检测）
- GNOME Polkit 代理
- DMS Greeter（greetd）

## 桌面（MangoWC）

- MangoWC Wayland 合成器
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Bibata Modern Ice 光标（24 px）
- GNOME Polkit 代理
- Ly 显示管理器
- adw-gtk3 + Papirus 图标 + Papirus Folders
- 缩放打开动画 + 官方贝塞尔曲线
- 在游戏显示器上启用 VRR + 撕裂（DP-1 1440p@240）
- 使用 grim + slurp + satty（标注）截图 — 3 个快捷键
- rofi 窗口切换器（Alt+Tab）
- 预先配置好 XDG Desktop Portal 环境变量（Pipewire 屏幕捕获、OBS、Discord Go Live）
- 对所有游戏应用（Steam、Heroic、Minecraft、Lutris、Bottles）启用 force_tearing + idleinhibit_when_focus
- 未聚焦窗口透明度（0.85）
- Hotarea overview（鼠标移到屏幕角落的手势）
- 浮动吸附 + 在 tile 之间拖拽
- 支持 scratchpad：为任意窗口提供通用池（移动/切换/恢复），
  另有可选的（`roudix.mangowc.scratchpadApps`）按应用命名的 scratchpad，
  适用于 Discord/Element/Telegram/Spotify — 每个应用都有自己的切换键

## 桌面（Umbriel）

- Umbriel 可滚动平铺式 Wayland 合成器 — Noctalia 自己的原生合成器，通过 [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) 提供（仅限 Noctalia，不支持切换 shell）
- 配置是 Nix 原生的（`programs.umbriel.settings`），按主题拆分（general、appearance、animation、input、layout、outputs、binds、rules），并在构建时校验（`validateConfig = true`）
- Noctalia 的实时主题同步（由 matugen 生成的颜色）通过 Umbriel 原生的 `include.files` 机制保留，没有静态颜色快照
- Bibata Modern Ice 光标（24 px）
- adw-gtk3 + Papirus 图标 + Papirus Folders
- Hot corners（鼠标移到角落触发 overview）和工作区总览（Mod+O）
- 支持 scratchpad（按需移动/切换/恢复浮动窗口）
- 按工作区覆盖布局（例如游戏工作区不留间隙）

## 桌面（Hyprland）

- Hyprland 动态平铺式 Wayland 合成器，通过 UWSM 启动
- Noctalia 现代化 shell
- xdg-desktop-portal-hyprland + gtk portal
- Bibata Modern Ice 光标（24 px）
- GNOME Polkit 代理（通过 systemd 用户服务启动）
- awww 壁纸守护进程
- 使用 grim + slurp + satty（标注）截图 — 3 个快捷键

## 桌面（GNOME）

- GNOME（跟随 nixos-unstable 分支）
- 精选扩展集（blur、tiling、vitals、arcmenu...）— 通过 dconf 启用
- ArcMenu 使用 Roudix 徽标作为菜单按钮图标
- 通过 `environment.gnome.excludePackages` 移除多余软件
- Papirus-Dark 图标主题
- adw-gtk3-dark GTK 主题（默认深色模式）
- Bibata Modern Ice 光标（24 px）
- Roudix 壁纸（根据系统主题切换浅色/深色）
- 通过 dconf 应用 `color-scheme = prefer-dark`
- 扩展设置（ArcMenu、Dash to Dock、Dash to Panel、Blur My Shell...）通过 `modules/home/desktop/gnome/_extensions.nix` 预先配置
- 通过 `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions` 添加/移除扩展，无需修改核心文件
- 在 `modules/home/local.nix` 中覆盖壁纸、主题、图标和光标

## 桌面（KDE）

- KDE Plasma 6，搭配 plasma-login-manager（Plasma 6.6+，nixpkgs unstable）
- 启用 KDE Connect
- xdg-desktop-portal-kde
- Papirus-Dark 图标主题
- Breeze Dark 外观 + 配色方案
- 登录界面和桌面使用 Roudix Dark 壁纸
- 精选软件包：partitionmanager、kcalc、digikam、vlc...
- 移除多余软件（排除 Discover）
- 在 `modules/home/local.nix` 中覆盖壁纸、面板和图标主题

## 音乐

通过 `roudix.musicPlayer` 选择其一 — `"spotify"`（默认）、`"ytmdesktop"`、
`"sonora"` 或 `"none"`。

- `"spotify"` — 打了 Spicetify 补丁的 Spotify。本地主题，默认 "colorful"
  （或 "comfy"），另有去广告和隐藏播客扩展 — 见下方
  开关。
- `"ytmdesktop"` — YouTube Music Desktop App（非官方、基于 Electron 的
  YouTube Music 客户端）。
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora)，一个原生
  （Rust/GPUI）客户端，在同一个应用中支持 Spotify、YouTube Music、Apple Music、Deezer 和
  Subsonic。可选的 `roudix.sonora.provider` 用于选择它启动时使用的
  服务（`"youtube"` = YouTube Music）。它不会绕过订阅：
  如果某项服务需要订阅，Sonora 同样需要。

## 可选的通用应用

GIMP、Inkscape、SongRec 和 EasyEffects（+ rnnoise-plugin）默认随系统提供，但
每一个都可以通过 `roudix.apps.<name>.enable`（`gimp`、
`inkscape`、`songrec`、`easyeffects`）单独关闭。

Signal 和 ZapZap（非官方、观感接近原生的 WhatsApp 桌面客户端）
没有真正可以互相切换的替代品，因此它们只是简单的 opt-in 布尔选项，
默认关闭：`roudix.apps.signal.enable` 和 `roudix.apps.zapzap.enable`。

Fluxer 是可自托管的 Discord 替代品，同样是这类 opt-in
布尔选项：`roudix.apps.fluxer.enable`。它目前还不在 nixpkgs 中，因此
直接取自 `nix-gaming-edge` flake input 中预编译好的
`fluxer-desktop` 包。它有意与 `roudix.discord`
和 `roudix.gaming.enable` 保持独立 — 你完全可能既想要 Discord
又想要 Fluxer，或者想要 Fluxer 却没有任何游戏配置。

邮件客户端和密码管理器也可使用，均为 opt-in（默认关闭）：
`roudix.mailClient` — `"thunderbird"`（功能齐全）、
`"betterbird"`（经过精细调校的 Thunderbird 分支，取自
[betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) flake
input — 目前还不在 nixpkgs 中）或 `"geary"`（轻量级 GNOME 客户端）；
`roudix.passwordManager` —
`"bitwarden"`（云同步）、`"keepassxc"`（本地离线保险库）或
`"protonpass"`（云同步，使用 Proton 账户）。

同样可选，opt-in（默认关闭）：通过
`roudix.torrentClient` 提供 BT 客户端 — `"qbittorrent"`（功能丰富，基于 Qt）、
`"fragments"`（极简的 GNOME/libadwaita 客户端）、`"deluge"`（基于插件）或
`"none"`（默认）。

## Spicetify

- 主题：`roudix.spicetify.theme` — `"colorful"`（默认，sanoojes/spicetify-colorful）或 `"comfy"`（内置的 Comfy 主题）
- 配色方案：`roudix.spicetify.colorScheme` — `null`（默认）使用主题自带的默认方案（colorful 为 "noctalia"，comfy 为 "Comfy"）
- 扩展可单独开关：`roudix.spicetify.extensions.adblock.enable`、`roudix.spicetify.extensions.hidePodcasts.enable`（默认均为 `true`）
- Marketplace 自定义应用：`roudix.spicetify.marketplace.enable`（默认 `true`）

## 浏览器

- 通过 `roudix.browsers` 选项配置浏览器列表
- 支持 `brave`、`helium`（通过 x13-me/helium-nix，包含 DRM 补丁 — 选择 `helium` 时会通过 `modules/home/apps/browser/helium-widevine.nix` 自动接入 Widevine 播放）、`vivaldi`（带 ffmpeg 编解码器）、`firefox`、`librewolf`、`chromium`，或 `[]` 表示不安装
- Zen Browser 可通过 `roudix.zen.enable = true` 单独启用（默认关闭）；可通过 `roudix.zen.variant` 选择通道 — `"twilight"`（默认）或 `"beta"`

## 其他

- 通过 `roudix.discord` 选择 Discord — `"vencord"`（打补丁的客户端，默认）、`"vanilla"`（未打补丁）或 `"none"`（不安装）
- 通过 `roudix.telegram` 选择 Telegram — `"telegram"`（官方 Telegram Desktop）、`"ayugram"`（非官方分支：幽灵模式、防撤回、本地消息历史...）或 `"none"`（默认，不安装）
- 通过 `roudix.editor` 选择代码编辑器 — `"zed"`（默认）、`"vscode"`、`"neovim"` 或 `"none"`（自行管理，例如 AppImage/Flatpak）
- 通过 `roudix.keyboardLayout` / `roudix.keyboardVariant` 设置图形界面（Wayland）键盘布局（XKB，例如 `"be"` / `"intl"`）— 独立于 `console.keyMap`，后者只在图形会话启动之前对 TTY 生效；对 GNOME/KDE 无效，它们自行管理布局
- 面向"裸"合成器（Niri、Hyprland、MangoWC、Umbriel）的 keyring + xdg-desktop-portal 组合，可通过 `roudix.desktopIntegration` 选择 — `"gnome"`（gnome-keyring + xdg-desktop-portal-gtk/-gnome，默认）或 `"kde"`（KWallet + xdg-desktop-portal-kde + polkit-kde-agent，并将 GNOME 应用替换为 Kate / Gwenview / KDE Partition Manager / Dolphin；保留 adw-gtk3、nwg-look、qt6ct 和 gvfs，使 GTK 应用仍能保持主题）；对 GNOME/KDE 会话无效，它们保留各自的原生组合
- 全系统启用 `nix-ld` — 无需 FHS 环境即可运行未打补丁的动态二进制文件（预先配置了常用库：glibc、openssl、zlib、libGL、X11、libxkbcommon、dbus、glib 等）
- OBS Studio，可通过 `roudix.contentCreation.obs.enable` 单独开关（默认 `true`），插件可通过 `roudix.contentCreation.obs.plugins.<name>.enable` 逐个开关（默认启用 `vkcapture` + `pipewireAudioCapture`；另可用：`backgroundRemoval`、`moveTransition`、`aitumMultistream`、`gstreamer`、`compositeBlur`、`advancedSceneSwitcher`、`inputOverlay`、`waveform`）
- 通过 `roudix.contentCreation.videoEditor` 选择视频编辑器 — `"kdenlive"`（默认）、`"davinci-resolve"`（免费）、`"davinci-resolve-studio"`（付费，需要许可证）、`"shotcut"` 或 `"none"`；当 `hardware.myGpu = "amd"` 时，DaVinci Resolve 会自动获得 AMD OpenCL ICD
- 为 OBS/DaVinci 自动设置 `v4l2loopback` 虚拟摄像头（`roudix.contentCreation.virtualCamera.enable`，默认 `true`）
- Chatterino2 Twitch 聊天客户端，通过 `roudix.contentCreation.streaming.chatterino.enable` opt-in 启用
- 整个内容创作组可通过 `roudix.contentCreation.enable` 开关
- GPU Screen Recorder
- 面向 AMD 的 Mesa Git 选项 — 通过 `local.nix` 中的 `roudix.mesa.useGit = true` 启用实验性/最前沿的 Mesa（默认：nixpkgs 的稳定版 Mesa）— ⚠️ **实验性**，视 nixpkgs 状态而定，构建可能失败
- 自动应用 AMD GPU 稳定性内核参数（`mem_sleep_default=deep`、`amdgpu.gpu_recovery=1`、`amdgpu.lockup_timeout=1000`、`amdgpu.runpm=0`、`amdgpu.sg_display=0`）— 修复 RDNA2/RDNA3 上的随机卡死和睡眠唤醒问题
- 通过 `roudix.rgb` 选择 RGB 控制器 — `openlinkhub`（Corsair iCUE Link / Commander，通过 CI 自动更新）、`openrgb`（多品牌：Razer、ASUS、MSI…）或 `none`
- 服务运行后，可在 [http://127.0.0.1:27003](http://127.0.0.1:27003) 访问 OpenLinkHub 网页界面
- 通过 OpenLinkHub 控制 DDR4/DDR5 内存 RGB — 用 `roudix.memory.enable = true` 启用，并配置 `roudix.memory.type`、`roudix.memory.smBus` 和 `roudix.memory.sku`（参见 `installation.zh_CN.md`）
- PipeWire 搭配 rnnoise 立体声降噪（nofail，LADSPA_PATH 兼容 26.05/26.11）
- Flatpak，带 Flathub 远程仓库 + 每日自动更新（通过 nix-flatpak）
- Blueman 蓝牙管理器
- Matrix 客户端 — 可通过 `roudix.matrixClient` 配置（`element`、`cinny` 或 `none`）— Element 在 KDE 上自动选择 kwallet6，其他环境选择 gnome-libsecret
- 通过 `roudix.videoPlayer` 选择视频播放器 — `"vlc"`（支持的格式最广，默认）、`"clapper"`（现代 GTK4 播放器）、`"mpv"`（+ yt-dlp，极简/流媒体）、`"celluloid"`（mpv 的 GTK 前端）或 `"none"`；适用于所有桌面（以前仅在裸合成器上硬编码使用 Clapper，另有一个与桌面环境无关的独立 mpv 开关）
- 通过 `appimage.nix` 启用 AppImage 支持
- Waydroid（Android 容器）— 可选，`roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager（可选，`roudix.virtualization.enable`）
- vm-curator（可选，`roudix.virtualization.vmCurator.enable`）— virt-manager 的 Rust TUI 替代品，直接驱动 QEMU（不使用 libvirt），支持 3D 加速和 GPU 直通；可以单独启用，也可以与 libvirt 栈一起启用
- 虚拟机客户端优化模块（剪贴板共享、自动调整分辨率、QEMU agent、Spice）

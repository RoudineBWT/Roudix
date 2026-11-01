[English](desktop.md) · [Français](desktop.fr.md) · [Español](desktop.es.md) · [Português (Brasil)](desktop.pt_BR.md) · [Русский](desktop.ru.md) · **简体中文** · [हिन्दी](desktop.hi.md) · [العربية](desktop.ar.md)

# 桌面环境

随时可以使用 `roudix-switch <de>` 或图形界面 **Roudix Customizer**（`roudix-switcher` 软件包）切换桌面——无需单独的主机配置。该图形界面的功能已不止切换桌面：它现在在一个应用中涵盖了桌面、游戏（按应用开关）、编辑器、终端、浏览器、登录 Shell、文件管理器、聊天客户端（Discord/Matrix）和集成（keyring/portal 栈）。

| 取值 | 桌面 | 说明 |
|------|------|------|
| `niri` | Niri + (Noctalia, DMS) | 默认——可滚动平铺（scrollable tiling）的 Wayland |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | 动态平铺 Wayland——通过 UWSM 启动 |
| `mangowc` | MangoWC + (Noctalia, DMS) | Wayland 合成器 |
| `umbriel` | Umbriel + Noctalia | 可滚动平铺——Noctalia 自带的原生合成器，仅限 Noctalia（不能切换 Shell） |
| `gnome` | GNOME | |
| `kde` | KDE Plasma 6 | plasma-login-manager、KDE Connect |
| `cinnamon` | Cinnamon | X11 会话 + LightDM——经典桌面，适合较旧的硬件（GNOME 49 仅支持 Wayland） |
| `cosmic` | COSMIC | System76 的 Wayland 桌面（cosmic-comp），cosmic-greeter |

要永久更改，请编辑 `hosts/roudix/local.nix`：

```nix
roudix.desktop.type = "niri"; # "niri"、"hyprland"、"mangowc"、"gnome"、"kde"、"cinnamon" 或 "cosmic"
```

或者使用 fish 函数——它会一步完成配置修改和重新构建：

```fish
roudix-switch kde
```

> **注意：** `roudix-switch` 使用 `nh os boot`——更改将在下次重启时生效。

---

## 图形 Shell（仅限 Niri、Hyprland 和 MangoWC）

对于 Wayland 合成器（Niri、Hyprland、MangoWC），可以独立于合成器切换 Shell/状态栏栈。对于 Hyprland，**同一个配置树**（`dotfiles/hyprland/`）包含通用快捷键，并根据 `roudix.desktop.shell` 选择 Shell。

| 取值 | Shell | Hyprland |
|------|-------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | Dux Shell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**注意：** Caelestia 仅在 Hyprland 上可用。Shell 通过 `ROUDIX_HYPR_SHELL` 注入会话，因此不存在需要保持同步的独立 `hyprland-dms/` 或 `hyprland-caelestia/` 目录树。

### Shell 自动启动

启动方式取决于所选的 Shell 和合成器，每个 Shell 恰好只有一种启动机制：

- **Hyprland + Noctalia：** 通过 Lua 钩子 `hyprland.start` 启动 `noctalia`。
- **Hyprland + Caelestia：** 通过 Lua 钩子 `hyprland.start` 启动 `caelestia-shell`。
- **Hyprland + DMS：** DMS 用户 systemd 服务；Hyprland 在启动时将会话环境导出到 systemd。
- **MangoWC + Noctalia：** 通过 MangoWC 的 `autostart_sh` 启动 `noctalia`。
- **MangoWC + DMS：** DMS 用户 systemd 服务，经由 `mango-session.target` 触发；因此 MangoWC 不会执行 `dms run`。

DMS 不能同时由 systemd 和合成器启动：其官方文档建议在使用 systemd 服务时移除 `dms run`。

要更改，请编辑 `hosts/roudix/local.nix`：

```nix
roudix.desktop.shell = "noctalia"; # "noctalia"、"dms" 或 "caelestia"
```

然后重新构建：

```fish
rebuild
```

或者使用 fish 函数（仅在 Niri、Hyprland 和 MangoWC 上可用）——它会一步完成配置修改和重新构建：

```fish
roudix-shell-switch dms
```

> **注意：** `roudix-shell-switch` 使用 `nh os boot`——更改将在下次重启时生效。

---

## nixpkgs 版本或最新版本（flake）

Niri、MangoWC 和 Umbriel 始终来自各自的 flake。对于 Shell（以及与之配套的 greeter），Roudix 默认使用 **nixpkgs** 版本。若要获得由项目自身 flake 构建的最新版本，请在 `local.nix` 中按组件开启——或在 `roudix-switcher` / 安装程序中开启，开关只会出现在你所选的 Shell 上：

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia（+ noctalia-greeter）
roudix.desktop.latest.dms       = true;  # Dux Shell（+ dms-greeter）
roudix.desktop.latest.caelestia = true;  # Caelestia（DMS greeter 跟随它）
```

Roudix 中的 Hyprland 没有 flake 版本：它始终来自 nixpkgs。

> **注意：** Roudix 的配置是**优先针对 flake（latest）版本**编写的。在 nixpkgs 版本上，如果出现提示某个选项、设置或配置键*不存在*的配置错误，这是**正常的**：它是在 nixpkgs 所提供的版本之后才加入的。请等待 nixpkgs 跟进，或将该组件设置为 `true`。

> 如果某个 flake 模块没有暴露 `package` 选项（DMS、MangoWC 和 DMS greeter 可能出现这种情况），就无法应用 nixpkgs 版本：Roudix 会保持使用 flake 版本，并在构建时打印警告。

---

## 个人合成器覆盖配置

Niri 和 Umbriel 原生地在 Nix 中配置（`programs.niri.settings` / `programs.umbriel.settings`）——是真正的、带类型的 attrset，而不是生成的文本文件。这意味着覆盖配置就是普通的 Nix：添加一个尚不存在的键，它会自动合并；如果修改仓库已经设置的键（同一输出、同一快捷键），则需要 `lib.mkForce`，否则 Nix 会因 “conflicting definitions” 错误拒绝构建。

MangoWC 和 Hyprland 仍然基于文本（见下文）。

你可以直接把覆盖配置放在 `modules/home/local.nix` 中，但如果你大量定制某个合成器，使用专用文件会更整洁——`modules/home/local.nix` 会自动导入 `modules/home/niri-custom.nix`、`modules/home/umbriel-custom.nix` 和 `modules/home/mango-custom.nix`（如果存在）（复制对应的 `*.example` 文件即可开始；它们与 `local.nix` 一样被 gitignore）。

**Niri**

```nix
# 修改 niri-flake 已设置的显示器（需要 lib.mkForce）
# — 在会话中运行 `niri msg outputs` 获取真实的连接器名称
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# 重新映射仓库已定义的快捷键（需要 lib.mkForce）
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# 添加尚不存在的快捷键（不需要 mkForce）
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# 添加窗口规则——列表会在多个文件之间拼接（CONCATENATE），因此这只会追加到
# 仓库的规则之后，不需要 mkForce
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# 修改输出（需要 lib.mkForce — 运行 `umbriel outputs` 获取真实名称）
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# 重新映射仓库已定义的快捷键
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# 添加尚不存在的快捷键
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# 添加窗口规则
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** 仍然会在其配置的最末尾加载一个由 home-manager 生成的个人覆盖文件——**`git pull` 永远不会改动它**——因为它在实践中没有带类型的 Nix 模式：

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

由于它是一大段文本而不是几行 Nix，放在单独的文件中更合适——参见 `modules/home/mango-custom.nix.example`。

**Hyprland 现在使用 `dotfiles/hyprland/` 中的模块化 Lua 配置。** 入口是 `dotfiles/hyprland/hyprland.lua`，它会加载 `config/` 中负责显示器、布局、动画、快捷键、窗口规则和 Shell 集成的模块。Nix 会把这个目录树原样复制到 `~/.config/hypr/`。

当前配置面向 Hyprland 0.55+，使用原生的 `dwindle`、`master` 和 `scrolling` 布局。Nix 模块会在入口之前生成一个小型加载器 `config/nix-plugins.lua`；Roudix 已包含 `borders-plus-plus`。`dynamic_cursors` 块仍然是可选的，仅在该插件存在时才生效。

### 自定义 Hyprland

与具体机器相关的值（`DP-1`/`DP-3` 输出、主显示器、默认应用、键盘等）位于 `dotfiles/hyprland/config/` 下。如果你把 Hyprland 配置保存在 Roudix 仓库中，可以直接编辑它们。

如果想在不修改受版本控制文件的情况下做个人覆盖，请在 `modules/home/local.nix` 中使用 `xdg.configFile."hypr/..."` 和 `lib.mkForce`。

> 修改 Lua 配置后，请运行 `rebuild`。涉及 Shell 或环境的更改可能需要重启会话。

> 完整的示例列表请参见 `modules/home/niri-custom.nix.example`、`modules/home/umbriel-custom.nix.example`、`modules/home/mango-custom.nix.example` 和 `modules/home/local.nix.example`。

---

## GNOME 覆盖配置

使用 `roudix.desktop.type = "gnome"` 时，扩展管理放在 `hosts/roudix/local.nix` 中，外观覆盖放在 `modules/home/local.nix` 中。

**在默认扩展之外添加扩展**（`hosts/roudix/local.nix`）
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**按 UUID 禁用某个默认扩展**（`hosts/roudix/local.nix`）
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**两者结合——例如用另一个启动器替换 ArcMenu**（`hosts/roudix/local.nix`）
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**手动更改外观（推荐）**

Roudix 将 GNOME 的外观（壁纸、深色主题、图标、光标、扩展设置）作为*默认值*提供。在“设置”、“优化（Tweaks）”或扩展的首选项中修改任何内容，它就归你所有：重新构建永远不会还原它。Roudix 的更新只会更改你没有动过的设置的默认值。

**从你的配置中强制指定某个值**（`modules/home/local.nix`）

如果你更希望以声明式的方式固定某个值，请通过 home-manager 设置。与上面的手动方式不同，它会在**每次**重新构建时重新应用，并覆盖你在界面中所做的更改：
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # 或 "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
不需要 `lib.mkForce`：home-manager 不再定义这些键。

**恢复 Roudix 的默认值**（针对某个设置或整个分区）
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> 所有可用的 GNOME 覆盖选项请参见 `hosts/roudix/local.nix.example` 和 `modules/home/local.nix.example`。

---

## KDE Plasma 覆盖配置

使用 `roudix.desktop.type = "kde"` 时：

Roudix **只应用一次** KDE 外观，绝不会在每次重新构建时应用，因此你在“系统设置”中所做的任何更改都会保留：

- **深色主题、图标、光标**：仅在首次登录时应用，由 `~/.local/state/roudix/kde-theme-seeded` 控制。若想主动恢复 Roudix 外观：`rm ~/.local/state/roudix/kde-theme-seeded`，然后注销再登录。
- **启动时开启 NumLock、锁屏壁纸**：`/etc/xdg` 中普通的 KConfig 默认值，优先级低于你的 `~/.config`，绝不会覆盖它。
- **壁纸和面板**：由 plasma-manager 在首次登录时应用，之后仅在 Roudix 自身通过更新修改了它们的定义时才会重新执行。

**从你的配置中固定值**（`modules/home/local.nix`）

通过 plasma-manager 设置的任何内容都会在**每次**重新构建时重新应用，因此只对你希望保持声明式的内容使用它：

**壁纸**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**配色方案 / 图标 / 光标**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**任务栏 / 面板**
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

> 只有 `wallpaper` 和 `panels` 需要 `lib.mkForce`，它们仍然定义在 `modules/home/desktop/kde/default.nix` 中。

## Cinnamon 默认设置

Cinnamon 默认使用 Roudix Kitsune 壁纸（桌面和 LightDM 登录界面均如此），使用 Roudix 徽标作为菜单图标，并在面板中固定默认浏览器（`roudix.browsers` 中的第一个）、Roudix Store 和“设置”。GTK4 / libadwaita 应用遵循深色主题。这些都是默认值：只会应用于用户未更改过的内容。面板固定项（浏览器、Nemo、Roudix Store、设置）和菜单图标是小程序（applet）的默认值，以两个 applet 的补丁副本形式提供：不会重新构建 Cinnamon 的任何部分。

登录界面（slick-greeter）没有设置应用。可以这样更改它的壁纸：

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # 无需重新构建
roudix-lightdm-wallpaper --reset                    # 恢复为 Kitsune
```

在 `hosts/roudix/local.nix` 中覆盖固定的应用：

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## COSMIC 默认设置

COSMIC 默认使用 Roudix Kitsune 壁纸，以及来自 `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions` 的键盘布局。程序坞会固定在 Roudix 中选择的浏览器（以及启用时的 Zen）、COSMIC Files、你的终端、Roudix Store 和 COSMIC Settings——思路与 GNOME 的 dash 和 Plasma 的任务管理器相同。在应用库中，所有 Roudix 应用（Store、Customizer、Kernel Switcher、Scheduler、Hardware Sync、Config、Welcome）都归入一个 **Roudix** 文件夹，不再列在“系统 / 实用工具”下。COSMIC Store 不会被安装：由 Roudix Store 取而代之。

这些都是默认值，以系统级 cosmic-config 文件的形式提供：只会应用于用户未更改过的内容，重新构建也绝不会还原你在 COSMIC Settings 中做出的选择。

COSMIC 自带的应用和面板默认使用 Roudix 配色方案（`assets/cosmic/`，由 `assets/palette/Roudix.json` 生成，由 `modules/system/desktop/cosmic.nix` 安装为系统默认值，不涉及 Home Manager）。在“设置 > 外观”中选择其他主题或强调色即可覆盖它，重新构建绝不会改动你的选择。“将当前主题应用于 GNOME 应用”（设置 > 桌面 > 外观 > 图标和工具包主题）默认开启：COSMIC 自己会导出它的主题，因此 GTK 应用（浏览器、Roudix 的应用等）会在 adw-gtk3 之上获得 Roudix 的配色，无需 Roudix 编写任何 CSS。图标为 Papirus-Roudix（参见 `roudix.iconTheme`），你的终端也会像在其他所有桌面上一样获得 Roudix 配色方案。

nixpkgs 的 COSMIC 模块会启用 `system76-scheduler`，但它默认被关闭，因为 Roudix 有自己的调度器栈（SCX）。如需保留它：

```nix
services.system76-scheduler.enable = true;
```

要更改固定的应用，只需在程序坞中固定 / 取消固定：你的选择优先于默认值。

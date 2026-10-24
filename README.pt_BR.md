[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · **Português (Brasil)** · [Русский](README.ru.md) · [简体中文](README.zh_CN.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### Configuração do NixOS (Unstable) — Vários compositores Wayland (hyprland, niri, mangowc e umbriel) · Gnome e KDE · Kernel CachyOS

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| Pré-visualização |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Apresentação do Roudix: Umbriel, GNOME e KDE Plasma" width="900"/> |

<sub>Personalização pessoal — a sua ficará diferente dependendo da sua configuração 👀</sub><br/>
<sub>Os compositores Wayland ficam por sua conta para personalizar: o Roudix só inclui a configuração padrão do Noctalia, do DankMaterialShell e (somente Hyprland) do Caelestia.</sub>

</div>

---

## Hardware

| Componente | Modelo |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## Stack

| Camada | Escolha |
|-------|--------|
| SO | Roudix (NixOS unstable) |
| Kernel | CachyOS (escolha sua variante em [Funcionalidades](docs/features.md) ou em [Instalação](docs/installation.pt_BR.md)) |
| Bootloader | Limine (padrão) · systemd-boot |
| Compositor | Niri (tiling com rolagem) · Hyprland (tiling dinâmico) · MangoWC · Umbriel (tiling com rolagem, nativo do Noctalia) |
| Shell gráfico | Noctalia · DankMaterialShell · Caelestia |
| Ambiente de desktop | KDE Plasma · Gnome |
| Gerenciador de login | DMS Greeter (somente Dms) · Noctalia Greeter (somente noctalia) · plasma-login-manager (somente KDE) · GDM (somente Gnome) |
| Terminal | Configurable (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| Shell | Fish · Bash |
| Navegador | Configurable (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| Gerenciador de arquivos | Configurable (Nautilus, Thunar, Dolphin, Nemo) |
| Editor | Configurable (Zed, VS Code, Neovim, nenhum) |
| Chat | Discord (Vencord · vanilla · nenhum) + Matrix (Element · Cinny · nenhum) |
| Música | Configurable (Spotify + Spicetify, YouTube Music Desktop, nenhum) |

---

## Documentação

| | |
|-|-|
| 🖥️ [Desktop e shells](docs/desktop.md) | Troque de compositor e de shell gráfico, ajustes pessoais (Niri, Hyprland, GNOME, KDE) |
| ⚡ [Aliases e funções](docs/aliases.pt_BR.md) | Todos os aliases e funções de shell — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [Instalação](docs/installation.pt_BR.md) | Guia de instalação automatizada e manual |
| ✨ [Funcionalidades](docs/features.md) | Lista completa de funcionalidades por ambiente de desktop |
| 🔄 [Atualização automática](docs/autoupdate.pt_BR.md) | Configuração do git pull + rebuild automáticos |

---

## Estrutura

```
roudix/
├── roudix-installer.sh              # Instalador baseado em Bash
├── flake.nix                        # Inputs e outputs
├── flake.lock
├── docs/                            # Documentação
│   ├── desktop.md                   # Ambientes de desktop e shells gráficos
│   ├── aliases.md                   # Aliases e funções de shell
│   ├── installation.md              # Guia de instalação
│   ├── features.md                  # Lista de funcionalidades
│   ├── features.fr.md               # Lista de funcionalidades (francês)
│   └── autoupdate.md                # Configuração da atualização automática
│
├── hosts/
│   └── roudix/                      # Um único host — o DE é escolhido por roudix.desktop.type
│       ├── configuration.nix
│       ├── username.nix             # no gitignore — seu nome de usuário (veja a instalação)
│       ├── local.nix                # no gitignore — seus ajustes pessoais do sistema
│       ├── local.nix.example        # copie para local.nix para começar
│       └── hardware-configuration.nix
│
├── dotfiles/                        # Arquivos de configuração brutos gerenciados pelo Home Manager
│   ├── easyeffects/                 # Presets do EasyEffects
│   ├── fastfetch/
│   │   └── roudix.txt               # Logo ASCII padrão do Roudix para o fastfetch
│   # niri/, niri-dms/ removidos — a config do niri agora é totalmente
│   # nativa do Nix (veja modules/home/desktop/niri/ abaixo).
│   ├── hyprland/                    # Config do Hyprland (Lua) — uma única árvore para todos os shells gráficos
│   │   ├── hyprland.lua             # Ponto de entrada: carrega os módulos de config/
│   │   └── config/
│   │       ├── shell.lua            # Escolhe o shell (noctalia / dms / caelestia) a partir de ROUDIX_HYPR_SHELL
│   │       ├── shells/              # Atalhos e integração por shell (noctalia.lua, dms.lua, caelestia.lua)
│   │       ├── binds/common.lua     # Atalhos compartilhados por todos os shells
│   │       ├── rules/               # Regras de janelas (common.lua, apps.lua, gaming.lua)
│   │       ├── ws.lua               # Tabela de workspaces compartilhada (usada por workspaces, binds e regras)
│   │       ├── workspaces.lua       # Regras de workspaces
│   │       ├── monitors.lua / input.lua / layout.lua / decorations.lua / animations.lua
│   │       ├── defaults.lua / colors.lua / environment.lua / autostart.lua / misc.lua
│   │       └── nix-noctalia.lua     # Carrega o tema ao vivo do Noctalia (gerado pelo matugen)
│   │   # config/nix-plugins.lua e config/nix-apps.lua são gerados pelo Nix (não estão no repositório)
│   └── perso/                       # Configuração pessoal (no gitignore)
│
├── pkgs/
│   ├── roudix-branding              # Pacote de branding do Roudix
│   ├── roudix-kernel-switcher       # Pacote da GUI Roudix Kernel Switcher
│   ├── roudix-switcher/             # GUI de configurações do Roudix (desktop, jogos, editor, terminal, navegador, shell, gerenciador de arquivos, chat, sistema, integração)
│   └──   roudix-scheduler-switcher    # Pacote da GUI Scheduler Switcher
│
└── modules/
    ├── system/                      # Módulos do NixOS em nível de sistema
    │   ├── desktop/                 # Módulos de ambiente de desktop (nível NixOS)
    │   │   ├── default.nix          # Opções de desktop (roudix.desktop.type + roudix.desktop.shell)
    │   │   └── niri.nix / hyprland.nix / gnome.nix / kde.nix / mangowc.nix / umbriel.nix
    │   │
    │   ├── boot/                    # Bootloader, kernel e CPU
    │   │   ├── boot.nix             # Limine/systemd-boot + entradas multi-SO
    │   │   ├── boot.local.nix       # no gitignore — suas entradas de boot pessoais
    │   │   ├── boot.local.nix.example
    │   │   ├── kernel.nix           # Seleção de variante de kernel — variantes do CachyOS + nixpkgs simples
    │   │   ├── cpu.nix              # Microcódigo Intel/AMD + módulos i2c
    │   │   └── bootloader/          # Recurso de papel de parede do Limine
    │   │
    │   ├── apps/                    # Módulos de seleção de apps (uma opção roudix.* cada)
    │   │   ├── apps.nix / appimage.nix / flatpak.nix / browser.nix / discord.nix
    │   │   ├── telegram.nix / matrix.nix / mail-client.nix / music-player.nix
    │   │   ├── video-player.nix / torrent-client.nix / password-manager.nix
    │   │   └── filemanager.nix / editor.nix / terminal.nix / spicetify.nix / content-creation.nix
    │   │
    │   ├── virtualization/          # QEMU/KVM, contêineres, ajustes de convidado de VM, Waydroid
    │   │   └── virtualization.nix / containers.nix / vm-guest.nix / waydroid.nix
    │   │
    │   ├── rgb/                     # Roteamento do controlador RGB
    │   │   ├── default.nix          # Opção roudix.rgb (openlinkhub / openrgb / none)
    │   │   └── openlinkhub.nix / openrgb.nix
    │   │
    │   ├── gaming/                  # Steam, Gamescope, ananicy-cpp, tuned-adm, schedulers SCX
    │   │   └── gaming.nix / scx.nix
    │   │
    │   ├── gpu/                     # Configuração de GPU (AMD/NVIDIA/Intel/VM + mesa-git)
    │   │
    │   ├── autoupdate.nix       # Git pull automático + rebuild quando a configuração muda
    │   ├── binary-caches.nix    # Caches binários do Nix (substituters + chaves confiáveis)
    │   ├── common.nix           # Configuração de sistema compartilhada (todos os hosts)
    │   ├── desktop-integration.nix  # Chaveiro + stack xdg-desktop-portal para compositores sem ambiente
    │   ├── environment.nix      # Variáveis de ambiente
    │   ├── fstrim.nix           # fstrim para SSD/NVMe
    │   ├── hosts-gta.nix        # Bloqueio de hosts do BattlEye (correção do GTA, opcional)
    │   ├── icon-theme.nix       # Seleção do tema de ícones em todo o sistema
    │   ├── keyboard.nix         # Layout/variante de teclado gráfico (Wayland)
    │   ├── pipewire.nix         # Áudio PipeWire + supressão de ruído com rnnoise
    │   ├── shell.nix            # Shell padrão (fish/bash)
    │   ├── update.nix           # Configuração de atualização do flake
    │   ├── roudix-update.nix    # Comando `update` (pull + rebuild + Flatpaks), script em roudix-update.sh, completions de shell em completions/
    │   └── version.nix          # Branding do SO Roudix (os-release, distroName)
    │   # terminal/gerenciador de arquivos: escolha seu favorito via local.nix em hosts/roudix/
    │
    └── home/                        # Módulos do Home Manager em nível de usuário
        ├── common.nix               # Config de home compartilhada (todos os usuários e DEs)
        ├── bash.nix                 # Config do shell Bash + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + inicialização automática no fish
        ├── fish.nix                 # Shell Fish + aliases + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # Pacotes de jogos do usuário (proton, mangohud...)
        ├── git.nix                  # Configuração do Git
        ├── mangohud.nix             # Overlay do MangoHud (compartilhado entre DEs)
        ├── papirus-icon.nix         # Tema de ícones Papirus (compartilhado entre DEs)
        ├── papirus-folders.nix      # Configuração da cor das pastas do Papirus (compartilhada)
        ├── tela-icon.nix            # Tema de ícones Tela (compartilhado entre DEs)
        ├── spicetify.nix            # Spotify + Spicetify (tema Comfy)
        ├── ssh.nix                  # SSH + GitHub
        ├── shell-modules.nix        # Imports de módulos de shell compartilhados (noctalia, dms, caelestia)
        └── desktop/                 # Uma pasta por DE — lado Home Manager, espelha modules/system/desktop/
            ├── default.nix          # Importa os seis incondicionalmente (cada um é protegido internamente com lib.mkIf)
            ├── gnome/
            │   ├── default.nix      # Papel de parede, tema, ícones, cursor
            │   └── _extensions.nix  # Extensões do GNOME — pacotes, UUIDs habilitados, configurações do dconf
            ├── kde/default.nix      # Config do plasma-manager (papel de parede, painéis, tela de bloqueio)
            ├── hyprland/default.nix # Conforme o shell (noctalia/dms/caelestia), plugins, pacotes
            ├── mangowc/default.nix  # config.conf/apps.conf do mango gerados, pacotes
            ├── niri/                # programs.niri.settings, dividido por tema, conforme o shell
            │   ├── default.nix      # monta os ajustes, include do tema ao vivo, pacotes
            │   ├── _general.nix     # ambiente, autostart, cursor (conforme o shell)
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # saídas + workspaces nomeados
            │   ├── _ws.nix          # constantes de glifos de ícones de workspace compartilhadas
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # adiciona o `include` do tema ao vivo à config renderizada do niri-flake
            └── umbriel/             # programs.umbriel.settings, dividido por tema (somente Noctalia)
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # carrega noctalia.toml (o include de tema ao vivo nativo do Umbriel)
```

---

## Inputs do flake

| Input | Origem |
|-------|--------|
| nixpkgs | [nixos-unstable](https://github.com/NixOS/nixpkgs/tree/nixos-unstable) |
| nixpkgs-stable | [nixos-26.05](https://github.com/NixOS/nixpkgs/tree/nixos-26.05) |
| niri | [epireyn/niri-flake](https://github.com/epireyn/niri-flake) |
| home-manager | [nix-community/home-manager](https://github.com/nix-community/home-manager) |
| noctalia | [noctalia-dev/noctalia](https://github.com/noctalia-dev/noctalia) |
| umbriel | [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) |
| caelestia-shell | [caelestia-dots/shell](https://github.com/caelestia-dots/shell) |
| dms | [AvengeMedia/DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) |
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

## Veja também

| Projeto | Descrição |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | Distro gamer baseada em NixOS da Gaming Linux FR |

---

## Dotfiles pessoais

Os arquivos de configuração pessoais ficam em `dotfiles/perso/` — estão no gitignore (exceto `dotfiles/perso/README.md`) e nunca são tocados pelo `git pull` nem pelo atualizador automático.

Veja [`dotfiles/perso/README.md`](dotfiles/perso/README.md) para a estrutura e o uso.

Para ajustes em nível de compositor (monitores, atalhos, espaçamentos…), use os arquivos de ajustes de usuário gerados — eles são gerenciados pelo home-manager e ficam a salvo do `git pull`. Veja [Desktop e shells](docs/desktop.md#personal-compositor-overrides) para mais detalhes.

## Desenvolvimento

```bash
nix develop     # dev shell: just, ruff, statix, deadnix, shellcheck, gettext
just            # lista as tarefas
just ci         # tudo que a CI verifica (avalia cada host, lint, Python, traduções)
```

O instalador é traduzido com gettext — veja [Instalador › Traduções](iso/roudix-installer/README.md#traductions).

## Licença
   MIT — veja [LICENSE](LICENSE). A Roudix Store é GPL-2.0-only e alguns
   arquivos de terceiros mantêm suas próprias licenças: veja [THIRD_PARTY.md](THIRD_PARTY.md).

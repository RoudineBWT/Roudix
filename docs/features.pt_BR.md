[English](features.md) · [Français](features.fr.md) · [Español](features.es.md) · **Português (Brasil)** · [Русский](features.ru.md) · [简体中文](features.zh_CN.md) · [हिन्दी](features.hi.md) · [العربية](features.ar.md)

# Funcionalidades

## Kernel e desempenho

- Kernel CachyOS com NTSync ativado (módulo `ntsync`)
- Dois provedores de kernel, escolhidos automaticamente por `hardware.myGpu`:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 36 variantes (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 variantes (`hardware.myKernelChaotic`) — traz o `nvidia_cachyos`, um driver pré-compilado combinando com o kernel deles, então o módulo da Nvidia não é recompilado localmente a cada atualização do kernel
- Kernels "puros" do nixpkgs também podem ser escolhidos nos dois provedores, totalmente fora do overlay do CachyOS — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline), `xanmod-lts` / `xanmod-latest` (XanMod). Na Nvidia, esses voltam a usar um módulo da Nvidia recompilado localmente (sem o cache do `nvidia_cachyos`)
- `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) pega somente esses kernels do nixpkgs a partir de um nixpkgs mais recente, para atualizar o kernel mais cedo, sem mexer no resto do sistema
- ZRAM ativado (100% da RAM, zstd, swappiness 150)
- zswap desativado
- Microcódigo da CPU configurado automaticamente (Intel ou AMD)
- Intel: `split_lock_detect=off` aplicado automaticamente
- ananicy-cpp ativado (daemon de prioridade de processos, regras do CachyOS)
- Suporte ao scheduler SCX — troca em tempo real, sem precisar reiniciar (bpfland, lavd, flash, p2dq, rusty…) pela interface Kernel Switcher — um único pedido de senha via `scx-switch` cuida de parar/iniciar o ananicy-cpp e trocar o scheduler de uma vez — **nota:** o SCX não persiste após reinicializações; depois de reiniciar, o ananicy-cpp volta a iniciar automaticamente e o scheduler precisa ser reaplicado pela interface Kernel Switcher

## Inicialização

- Bootloader Limine (padrão) — moderno, rápido, com suporte a vários discos — ou systemd-boot, selecionável via `roudix.boot.bootloader`
- Renomeação automática da entrada UEFI para "Roudix"
- Menu de boot multi-OS (Windows, outras distros Linux em ESPs separadas)
- O rótulo de boot mostra o nome Roudix + a versão da release do NixOS

## Gaming

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, sessão desativada por padrão)
- Variáveis de ambiente de captura do OBS pré-configuradas (`OBS_VKCAPTURE` via `environment.sessionVariables`)
- Overlay MangoHud horizontal personalizado (rótulo `Powered By Roudix`)
- Suporte a controles (Steam Hardware + game-devices-udev-rules)
- Suporte a 32 bits para Wine/Steam
- Wrapper `game-performance` — troca para um perfil de desempenho `tuned-adm` dedicado durante a duração de um jogo, acompanhado por meio de um cgroup `systemd-run --user --scope` (assim ele sobrevive quando o Steam faz re-fork/se desanexa) e restaurado ao sair (uso: `game-performance %command%` nas opções de inicialização do Steam) — o GameMode está desativado de propósito (incompatível com o ananicy-cpp aqui)
- `ffmpegthumbnailer` disponível em todo o sistema (miniaturas de vídeo nos gerenciadores de arquivos)
- `protonup-qt` no KDE, `protonplus` nos outros ambientes de desktop
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft, ou Modrinth App como alternativa — `roudix.gaming.apps.modrinth.enable`) e Vintage Story (via roudix-caches)
- Cada app de gaming pode ser ativado/desativado individualmente via `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (todos `true` por padrão)
- Cliente Steam modificado [Millennium](https://github.com/SteamClientHomebrew/Millennium) opcional (temas + plugins) — desativado por padrão, ative com `roudix.gaming.steam.millennium.enable = true` (ou pelo instalador). Mod não oficial; o ajuste de sandbox do `game-performance` e as ferramentas de compatibilidade do Proton continuam funcionando, e voltar para `false` restaura o Steam padrão
- Modo Gaming opcional estilo console: `roudix.gaming.gamescopeSession.enable` adiciona uma sessão "Steam (Gaming Mode)" na tela de login (Steam Big Picture dentro do gamescope, VRR/HDR/MangoApp, taxa de atualização detectada na inicialização). "Mudar para o Desktop" no Steam abre o seu desktop, e o app "Return to Gaming Mode" volta ao jogo sem passar pela tela de login. Baseado no GLF-OS; compatível com niri, umbriel, GNOME, KDE, Hyprland e MangoWC
- Decky Loader opcional (plugins do Steam) via `roudix.gaming.gamescopeSession.decky.enable`, obtido do flake input do Jovian-NixOS (`nix flake update jovian` para atualizá-lo, sem sha para manter à mão); não há cache binário, então ele é compilado localmente na primeira reconstrução

## Desktop (Niri)

- Niri, compositor Wayland de tiling com rolagem — fornecido via [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), usando `niri-unstable` por padrão, com o cache binário `niri-epireyn.cachix.org` pré-configurado
- A configuração é nativa do Nix (`programs.niri.settings`), dividida por assunto (general, animations, input, layout, outputs, binds, rules) e validada em tempo de build com `niri validate` — uma configuração quebrada faz o build falhar, em vez de o compositor falhar no login
- A sincronização de tema ao vivo do Noctalia/DMS (cores geradas pelo matugen/DMS, alt-tab, blur) é preservada adicionando um `include` à configuração gerada, em vez de embuti-la de forma estática
- Shell moderno Noctalia (v5)
- xdg-desktop-portal-gnome + gtk (portais de screencast e de desktop remoto configurados)
- Cursor Bibata Modern Ice (24 px)
- adw-gtk3 + ícones Papirus + Papirus Folders
- Element Desktop com gnome-libsecret / kwallet6 (detectado automaticamente conforme o ambiente de desktop)
- Agente Polkit do GNOME
- DMS Greeter (greetd)

## Desktop (MangoWC)

- MangoWC, compositor Wayland
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Cursor Bibata Modern Ice (24 px)
- Agente Polkit do GNOME
- Gerenciador de login Ly
- adw-gtk3 + ícones Papirus + Papirus Folders
- Animação de abertura com zoom + curvas bezier oficiais
- VRR + tearing ativados no monitor gamer (DP-1 1440p@240)
- Capturas de tela com grim + slurp + satty (anotação) — 3 atalhos de teclado
- Alternador de janelas com rofi (Alt+Tab)
- Variáveis de ambiente do XDG Desktop Portal pré-configuradas (captura de tela com Pipewire, OBS, Discord Go Live)
- force_tearing + idleinhibit_when_focus em todos os apps de gaming (Steam, Heroic, Minecraft, Lutris, Bottles)
- Opacidade das janelas sem foco (0.85)
- Hotarea overview (gesto do mouse no canto)
- Snap flutuante + arrastar de tile para tile
- Suporte a scratchpad: um pool genérico para qualquer janela (mover/alternar/restaurar),
  mais um scratchpad nomeado opcional (`roudix.mangowc.scratchpadApps`) por
  app para Discord/Element/Telegram/Spotify — cada um com a sua própria tecla de alternância

## Desktop (Umbriel)

- Umbriel, compositor Wayland de tiling com rolagem — o compositor nativo do próprio Noctalia, fornecido via [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (somente com Noctalia, sem troca de shell)
- A configuração é nativa do Nix (`programs.umbriel.settings`), dividida por assunto (general, appearance, animation, input, layout, outputs, binds, rules) e validada em tempo de build (`validateConfig = true`)
- A sincronização de tema ao vivo do Noctalia (cores geradas pelo matugen) é preservada pelo mecanismo nativo `include.files` do Umbriel, sem instantâneo estático de cores
- Cursor Bibata Modern Ice (24 px)
- adw-gtk3 + ícones Papirus + Papirus Folders
- Hot corners (overview ao levar o mouse ao canto) e uma visão geral dos workspaces (Mod+O)
- Suporte a scratchpad (mover/alternar/restaurar uma janela flutuante sob demanda)
- Ajustes de layout por workspace (p. ex., sem gap no workspace de gaming)

## Desktop (Hyprland)

- Hyprland, compositor Wayland de tiling dinâmico iniciado via UWSM
- Shell moderno Noctalia
- xdg-desktop-portal-hyprland + portal gtk
- Cursor Bibata Modern Ice (24 px)
- Agente Polkit do GNOME (iniciado via serviço de usuário do systemd)
- Daemon de papel de parede awww
- Capturas de tela com grim + slurp + satty (anotação) — 3 atalhos de teclado

## Desktop (GNOME)

- GNOME (acompanha o branch nixos-unstable)
- Conjunto selecionado de extensões (blur, tiling, vitals, arcmenu...) — ativadas via dconf
- ArcMenu com o logo do Roudix como ícone do botão de menu
- Bloatware removido via `environment.gnome.excludePackages`
- Tema de ícones Papirus-Dark
- Tema GTK adw-gtk3-dark (modo escuro por padrão)
- Cursor Bibata Modern Ice (24 px)
- Papel de parede do Roudix (claro/escuro conforme o tema do sistema)
- `color-scheme = prefer-dark` aplicado via dconf
- Configurações das extensões (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) pré-configuradas via `modules/home/desktop/gnome/_extensions.nix`
- Adicione/remova extensões sem editar os arquivos principais via `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Sobrescreva papel de parede, tema, ícones e cursor em `modules/home/local.nix`

## Desktop (KDE)

- KDE Plasma 6 com plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect ativado
- xdg-desktop-portal-kde
- Tema de ícones Papirus-Dark
- Look & feel e esquema de cores Breeze Dark
- Papel de parede Roudix Dark na tela de login e no desktop
- Pacotes selecionados: partitionmanager, kcalc, digikam, vlc...
- Bloatware removido (Discover excluído)
- Sobrescreva papel de parede, painéis e tema de ícones em `modules/home/local.nix`

## Música

Escolha um via `roudix.musicPlayer` — `"spotify"` (padrão), `"ytmdesktop"`,
`"sonora"` ou `"none"`.

- `"spotify"` — Spotify modificado com Spicetify. Tema local, "colorful" por
  padrão (ou "comfy"), além das extensões de adblock e de ocultar podcasts — veja
  os interruptores abaixo.
- `"ytmdesktop"` — YouTube Music Desktop App (cliente não oficial do YouTube Music,
  baseado em Electron).
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora), um cliente nativo
  (Rust/GPUI) para Spotify, YouTube Music, Apple Music, Deezer e
  Subsonic em um único app. A opção `roudix.sonora.provider` escolhe o
  provedor com o qual ele inicia (`"youtube"` = YouTube Music). Ele não contorna
  assinaturas: se um serviço exige uma, o Sonora também exige.

## Apps comuns opcionais

GIMP, Inkscape, SongRec e EasyEffects (+ rnnoise-plugin) vêm por padrão, mas
cada um pode ser desativado individualmente via `roudix.apps.<name>.enable` (`gimp`,
`inkscape`, `songrec`, `easyeffects`).

Signal e ZapZap (um cliente de desktop do WhatsApp não oficial, com cara de app nativo)
não têm uma alternativa de verdade entre as quais escolher, então são simples booleanos opt-in,
desativados por padrão: `roudix.apps.signal.enable` e `roudix.apps.zapzap.enable`.

Fluxer, uma alternativa ao Discord que pode ser auto-hospedada, é o mesmo tipo de booleano
opt-in: `roudix.apps.fluxer.enable`. Ele ainda não está no nixpkgs, então é
obtido diretamente do pacote pré-compilado `fluxer-desktop` do flake input
`nix-gaming-edge`. É deliberadamente independente de `roudix.discord`
e de `roudix.gaming.enable` — nada impede você de querer Discord
e Fluxer ao mesmo tempo, ou Fluxer sem nenhum setup de gaming.

Um cliente de e-mail e um gerenciador de senhas também estão disponíveis, opt-in (desativados
por padrão): `roudix.mailClient` — `"thunderbird"` (completo),
`"betterbird"` (um fork do Thunderbird ajustado, obtido do flake input
[betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) — ainda não
está no nixpkgs) ou `"geary"` (cliente leve do GNOME);
`roudix.passwordManager` —
`"bitwarden"` (sincronizado na nuvem), `"keepassxc"` (cofre local, offline) ou
`"protonpass"` (sincronizado na nuvem, conta Proton).

Também disponível, opt-in (desativado por padrão): um cliente de torrent via
`roudix.torrentClient` — `"qbittorrent"` (cheio de recursos, baseado em Qt),
`"fragments"` (cliente mínimo do GNOME/libadwaita), `"deluge"` (baseado em plugins) ou
`"none"` (padrão).

## Spicetify

- Tema: `roudix.spicetify.theme` — `"colorful"` (padrão, sanoojes/spicetify-colorful) ou `"comfy"` (tema Comfy incluído)
- Esquema de cores: `roudix.spicetify.colorScheme` — `null` (padrão) usa o esquema padrão do próprio tema ("noctalia" para colorful, "Comfy" para comfy)
- Extensões ativáveis individualmente: `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (ambas `true` por padrão)
- App personalizado Marketplace: `roudix.spicetify.marketplace.enable` (`true` por padrão)

## Navegador

- Lista de navegadores configurável pela opção `roudix.browsers`
- Compatível com `brave`, `helium` (via x13-me/helium-nix, inclui o patch de DRM — a reprodução com Widevine é configurada automaticamente via `modules/home/apps/browser/helium-widevine.nix` quando `helium` é selecionado), `vivaldi` (com codecs ffmpeg), `firefox`, `librewolf`, `chromium`, ou `[]` para nenhum
- Zen Browser disponível separadamente via `roudix.zen.enable = true` (desativado por padrão); o canal é selecionável via `roudix.zen.variant` — `"twilight"` (padrão) ou `"beta"`

## Outros

- Discord selecionável via `roudix.discord` — `"vencord"` (cliente modificado, padrão), `"vanilla"` (sem modificações) ou `"none"` (não instalado)
- Telegram selecionável via `roudix.telegram` — `"telegram"` (Telegram Desktop oficial), `"ayugram"` (fork não oficial: modo fantasma, anti-recall, histórico local de mensagens...) ou `"none"` (padrão, não instalado)
- Editor de código selecionável via `roudix.editor` — `"zed"` (padrão), `"vscode"`, `"neovim"` ou `"none"` (gerencie o seu, p. ex. AppImage/Flatpak)
- Layout de teclado gráfico (Wayland) via `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, p. ex. `"be"` / `"intl"`) — independente de `console.keyMap`, que cobre apenas o TTY antes de a sessão gráfica iniciar; não tem efeito no GNOME/KDE, que gerenciam o próprio layout
- Pilha de keyring + xdg-desktop-portal para compositores "puros" (Niri, Hyprland, MangoWC, Umbriel) selecionável via `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, padrão) ou `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent, e os apps do GNOME trocados por Kate / Gwenview / KDE Partition Manager / Dolphin; adw-gtk3, nwg-look, qt6ct e gvfs são mantidos para que os apps GTK continuem com tema); não tem efeito nas sessões GNOME/KDE, que mantêm a pilha nativa
- `nix-ld` ativado em todo o sistema — execute binários dinâmicos sem patch, sem precisar de um ambiente FHS (pré-configurado com bibliotecas comuns: glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib e mais)
- OBS Studio, ativável individualmente via `roudix.contentCreation.obs.enable` (`true` por padrão), com plugins ativados um a um via `roudix.contentCreation.obs.plugins.<name>.enable` (`vkcapture` + `pipewireAudioCapture` ativados por padrão; também disponíveis: `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- Editor de vídeo selecionável via `roudix.contentCreation.videoEditor` — `"kdenlive"` (padrão), `"davinci-resolve"` (gratuito), `"davinci-resolve-studio"` (pago, exige licença), `"shotcut"` ou `"none"`; o DaVinci Resolve recebe automaticamente um ICD de OpenCL para AMD quando `hardware.myGpu = "amd"`
- Câmera virtual `v4l2loopback` configurada automaticamente para OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`, `true` por padrão)
- Cliente de chat da Twitch Chatterino2, opt-in via `roudix.contentCreation.streaming.chatterino.enable`
- Todo o grupo de criação de conteúdo pode ser ativado/desativado via `roudix.contentCreation.enable`
- GPU Screen Recorder
- Opção Mesa Git para AMD — ative um Mesa experimental/de ponta via `roudix.mesa.useGit = true` no `local.nix` (padrão: Mesa estável do nixpkgs) — ⚠️ **experimental**, o build pode falhar dependendo do estado do nixpkgs
- Parâmetros de kernel para estabilidade de GPU AMD aplicados automaticamente (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — corrigem travamentos aleatórios e problemas ao voltar da suspensão em RDNA2/RDNA3
- Controlador RGB selecionável via `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, atualizado automaticamente via CI), `openrgb` (multimarcas: Razer, ASUS, MSI…) ou `none`
- A interface web do OpenLinkHub fica disponível em [http://127.0.0.1:27003](http://127.0.0.1:27003) assim que o serviço estiver rodando
- Controle de RGB da RAM DDR4/DDR5 via OpenLinkHub — ative com `roudix.memory.enable = true` e configure `roudix.memory.type`, `roudix.memory.smBus` e `roudix.memory.sku` (veja `installation.pt_BR.md`)
- PipeWire com supressão de ruído estéreo rnnoise (nofail, compatibilidade de LADSPA_PATH 26.05/26.11)
- Flatpak com o remote do Flathub + atualização automática diária (via nix-flatpak)
- Gerenciador de Bluetooth Blueman
- Cliente Matrix — configurável via `roudix.matrixClient` (`element`, `cinny` ou `none`) — o Element seleciona automaticamente kwallet6 no KDE e gnome-libsecret nos demais
- Player de vídeo selecionável via `roudix.videoPlayer` — `"vlc"` (maior suporte a formatos, padrão), `"clapper"` (player moderno em GTK4), `"mpv"` (+ yt-dlp, mínimo/streaming), `"celluloid"` (interface GTK para o mpv) ou `"none"`; vale para todos os desktops (antes era o Clapper fixo apenas nos compositores puros, mais um interruptor de mpv separado, independente do ambiente de desktop)
- Suporte a AppImage ativado via `appimage.nix`
- Waydroid (contêiner Android) — opcional, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (opcional, `roudix.virtualization.enable`)
- vm-curator (opcional, `roudix.virtualization.vmCurator.enable`) — alternativa TUI em Rust ao virt-manager, controla o QEMU diretamente (sem libvirt), com aceleração 3D e suporte a GPU passthrough; pode ser ativado de forma independente ou junto com a pilha do libvirt
- Módulo de otimizações para convidados de VM (compartilhamento de área de transferência, redimensionamento automático, agente QEMU, Spice)

[English](desktop.md) · [Français](desktop.fr.md) · [Español](desktop.es.md) · **Português (Brasil)** · [Русский](desktop.ru.md) · [简体中文](desktop.zh_CN.md) · [हिन्दी](desktop.hi.md) · [العربية](desktop.ar.md)

# Ambientes de desktop

Troque de desktop a qualquer momento com `roudix-switch <de>` ou pela interface gráfica **Roudix Customizer** (pacote `roudix-switcher`) — sem precisar de um host separado. A interface foi além da simples troca de desktop: agora cobre Desktop, Gaming (chaves por aplicativo), Editor, Terminal, Navegador, Shell de login, Gerenciador de arquivos, Cliente de chat (Discord/Matrix) e Integração (pilha keyring/portal) em um único aplicativo.

| Valor | Desktop | Notas |
|-------|---------|-------|
| `niri` | Niri + (Noctalia, DMS) | Padrão — Wayland com tiling rolável (scrollable tiling) |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Wayland com tiling dinâmico — iniciado via UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | Compositor Wayland |
| `umbriel` | Umbriel + Noctalia | Tiling rolável — o compositor nativo do próprio Noctalia, somente Noctalia (sem troca de shell) |
| `gnome` | GNOME 49.5 | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |
| `cinnamon` | Cinnamon | Sessão X11 + LightDM — desktop clássico, adequado a hardware mais antigo (o GNOME 49 é somente Wayland) |
| `cosmic` | COSMIC | Desktop Wayland da System76 (cosmic-comp), cosmic-greeter |

Para mudar de forma permanente, edite `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome", "kde", "cinnamon" ou "cosmic"
```

Ou use a função do fish — ela edita a configuração e reconstrói em um único passo:

```fish
roudix-switch kde
```

> **Nota:** `roudix-switch` usa `nh os boot` — as mudanças são aplicadas na próxima reinicialização.

---

## Shells gráficos (somente Niri, Hyprland e MangoWC)

Nos compositores Wayland (Niri, Hyprland, MangoWC), você pode trocar a pilha de shell/barra independentemente do compositor. No Hyprland, **uma única árvore de configuração** (`dotfiles/hyprland/`) contém os atalhos comuns e seleciona o shell a partir de `roudix.desktop.shell`.

| Valor | Shell | Hyprland |
|-------|-------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | DankMaterialShell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**Nota:** o Caelestia só está disponível no Hyprland. O shell é injetado na sessão por meio de `ROUDIX_HYPR_SHELL`, portanto não há árvores `hyprland-dms/` ou `hyprland-caelestia/` separadas para manter sincronizadas.

### Inicialização automática do shell

A inicialização depende do shell e do compositor selecionados, com exatamente um mecanismo de inicialização por shell:

- **Hyprland + Noctalia:** `noctalia` a partir do hook Lua `hyprland.start`.
- **Hyprland + Caelestia:** `caelestia-shell` a partir do hook Lua `hyprland.start`.
- **Hyprland + DMS:** serviço de usuário systemd do DMS; o Hyprland exporta o ambiente da sessão para o systemd na inicialização.
- **MangoWC + Noctalia:** `noctalia` a partir de `autostart_sh` do MangoWC.
- **MangoWC + DMS:** serviço de usuário systemd do DMS, acionado por `mango-session.target`; o MangoWC, portanto, não executa `dms run`.

O DMS não deve ser iniciado ao mesmo tempo pelo systemd e pelo compositor: a documentação oficial recomenda remover `dms run` quando o serviço systemd é usado.

Para mudar, edite `hosts/roudix/local.nix`:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" ou "caelestia"
```

Depois reconstrua:

```fish
rebuild
```

Ou use a função do fish (disponível somente no Niri, Hyprland e MangoWC) — ela edita a configuração e reconstrói em um único passo:

```fish
roudix-shell-switch dms
```

> **Nota:** `roudix-shell-switch` usa `nh os boot` — as mudanças são aplicadas na próxima reinicialização.

---

## nixpkgs ou última versão (flake)

Niri, MangoWC e Umbriel vêm sempre do próprio flake. Para o shell (e o greeter que o acompanha), o Roudix usa por padrão a versão do **nixpkgs**. Para obter a versão mais recente possível, compilada a partir do flake do próprio projeto, ative-a por componente em `local.nix` — ou pelo `roudix-switcher` / instalador, onde a chave só aparece para o shell selecionado:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # DankMaterialShell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (o greeter do DMS o acompanha)
```

O Hyprland não tem versão flake no Roudix: ele vem sempre do nixpkgs.

> **Atenção:** as configurações do Roudix são escritas **primeiro para as versões flake (latest)**. Nas versões do nixpkgs, um erro de configuração dizendo que uma opção, um ajuste ou uma chave de configuração *não existe* é **normal**: ela foi adicionada depois da versão fornecida pelo nixpkgs. Espere o nixpkgs se atualizar ou defina o componente como `true`.

> Se um módulo flake não expõe uma opção `package` (possível para DMS, MangoWC e o greeter do DMS), a versão do nixpkgs não pode ser aplicada: o Roudix permanece na versão flake e exibe um aviso durante a compilação.

---

## Personalizações do compositor

Niri e Umbriel são configurados nativamente em Nix (`programs.niri.settings` / `programs.umbriel.settings`) — attrsets reais e tipados, não um arquivo de texto gerado. Isso significa que as personalizações são apenas Nix: adicione uma chave que ainda não existe e ela é mesclada automaticamente; se você mexer em uma chave que o repositório já define (mesma saída, mesmo atalho), precisará de `lib.mkForce`, ou o Nix se recusará a compilar com um erro de «conflicting definitions».

MangoWC e Hyprland continuam baseados em texto (veja abaixo).

Você pode colocar personalizações diretamente em `home/local.nix`, mas se estiver personalizando bastante um compositor, um arquivo dedicado deixa tudo mais organizado — `home/local.nix` importa automaticamente `home/niri-custom.nix`, `home/umbriel-custom.nix` e `home/mango-custom.nix` se existirem (copie o arquivo `*.example` correspondente para começar; eles ficam no gitignore, como `local.nix`).

**Niri**

```nix
# Alterar um monitor que o niri-flake já define (precisa de lib.mkForce)
# — execute `niri msg outputs` na sessão para obter o nome real do conector
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# Remapear um atalho que o repositório já define (precisa de lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# Adicionar um atalho que ainda não existe (não precisa de mkForce)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# Adicionar uma regra de janela — as listas se CONCATENAM entre arquivos, então isto
# apenas se soma às regras do repositório, sem precisar de mkForce
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# Alterar uma saída (precisa de lib.mkForce — execute `umbriel outputs` para o nome real)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# Remapear um atalho que o repositório já define
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# Adicionar um atalho que ainda não existe
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# Adicionar uma regra de janela
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** ainda carrega, bem no final da sua configuração, um arquivo de personalização pessoal gerado pelo home-manager — **nunca modificado pelo `git pull`** — porque, na prática, não tem um esquema Nix tipado:

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

Como é um grande bloco de texto e não algumas linhas de Nix, ele se encaixa melhor em um arquivo próprio — veja `home/mango-custom.nix.example`.

**O Hyprland agora usa a configuração Lua modular em `dotfiles/hyprland/`.** O ponto de entrada é `dotfiles/hyprland/hyprland.lua`, que carrega os módulos de `config/` para monitores, layouts, animações, atalhos, regras de janela e integrações de shell. O Nix copia essa árvore como está para `~/.config/hypr/`.

A configuração atual tem como alvo o Hyprland 0.55+ e usa os layouts nativos `dwindle`, `master` e `scrolling`. O módulo Nix gera um pequeno carregador `config/nix-plugins.lua` antes do ponto de entrada; o `borders-plus-plus` é incluído pelo Roudix. O bloco `dynamic_cursors` continua opcional e só se aplica quando esse plugin está presente.

### Personalizando o Hyprland

Os valores específicos da máquina (as saídas `DP-1`/`DP-3`, monitor principal, aplicativos padrão, teclado etc.) ficam em `dotfiles/hyprland/config/`. Edite-os diretamente se você mantém sua configuração do Hyprland no repositório do Roudix.

Para personalizações pessoais sem alterar arquivos versionados, use `home/local.nix` com `xdg.configFile."hypr/..."` e `lib.mkForce`.

> Depois de alterar a configuração Lua, execute `rebuild`. Pode ser necessário reiniciar a sessão para mudanças de shell ou de ambiente.

> Veja `home/niri-custom.nix.example`, `home/umbriel-custom.nix.example`, `home/mango-custom.nix.example` e `home/local.nix.example` para a lista completa de exemplos.

---

## Personalizações do GNOME

Ao usar `roudix.desktop.type = "gnome"`, o gerenciamento de extensões fica em `hosts/roudix/local.nix` e as personalizações de aparência ficam em `home/local.nix`.

**Adicionar extensões além das padrão** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**Desativar uma extensão padrão pelo UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**Combinar as duas — por exemplo, trocar o ArcMenu por outro lançador** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**Mudando a aparência manualmente (recomendado)**

O Roudix entrega a aparência do GNOME (papel de parede, tema escuro, ícones, cursor, configurações das extensões) como *padrões*. Mude qualquer coisa em Configurações, Ajustes ou nas preferências de uma extensão e passa a ser sua: uma reconstrução nunca a reverte. As atualizações do Roudix só alteram os padrões das configurações que você não tocou.

**Forçando um valor a partir da sua configuração** (`home/local.nix`)

Se preferir fixar um valor de forma declarativa, defina-o pelo home-manager. Diferentemente do caminho manual acima, ele é reaplicado a **cada** reconstrução e se sobrepõe ao que você muda na interface:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # ou "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
Não é preciso `lib.mkForce`: o home-manager não define mais essas chaves.

**Recuperando os padrões do Roudix** para uma configuração (ou uma seção inteira)
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> Veja `hosts/roudix/local.nix.example` e `home/local.nix.example` para todas as opções de personalização do GNOME disponíveis.

---

## Personalizações do KDE Plasma

Ao usar `roudix.desktop.type = "kde"`:

O Roudix aplica a aparência do KDE **uma única vez**, nunca a cada reconstrução, então tudo o que você mudar em Configurações do Sistema permanece:

- **Tema escuro, ícones, cursor**: aplicados apenas no primeiro login, protegidos por `~/.local/state/roudix/kde-theme-seeded`. Para recuperar de propósito a aparência do Roudix: `rm ~/.local/state/roudix/kde-theme-seeded` e saia/entre novamente na sessão.
- **NumLock na inicialização, papel de parede da tela de bloqueio**: padrões simples do KConfig em `/etc/xdg`, que ficam abaixo do seu `~/.config` e nunca o sobrescrevem.
- **Papel de parede e painel**: aplicados pelo plasma-manager no primeiro login e só executados de novo se o próprio Roudix alterar a definição deles em uma atualização.

**Fixando valores a partir da sua configuração** (`home/local.nix`)

Tudo o que você definir pelo plasma-manager é reaplicado a **cada** reconstrução, então use-o apenas para o que você quer que seja declarativo:

**Papel de parede**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Esquema de cores / ícones / cursor**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**Barra de tarefas / Painéis**
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

> `lib.mkForce` só é necessário para `wallpaper` e `panels`, que ainda são definidos em `home/desktop/kde/default.nix`.

## Padrões do Cinnamon

O Cinnamon vem por padrão com o papel de parede Roudix Kitsune, na área de trabalho e na tela de login do LightDM, usa o logotipo do Roudix como ícone do menu e fixa no painel o navegador padrão (o primeiro de `roudix.browsers`), a Roudix Store e as Configurações. Os aplicativos GTK4 / libadwaita seguem o tema escuro. São padrões: só se aplicam ao que o usuário não alterou. Os itens fixados do painel (navegador, Nemo, Roudix Store, Configurações) e o ícone do menu são padrões de applets, entregues como cópias modificadas de dois applets: nada do Cinnamon é recompilado.

A tela de login (slick-greeter) não tem aplicativo de configurações. Mude o papel de parede dela com:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # sem necessidade de rebuild
roudix-lightdm-wallpaper --reset                    # volta ao Kitsune
```

Substitua os aplicativos fixados em `hosts/roudix/local.nix`:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## Padrões do COSMIC

O COSMIC vem por padrão com o papel de parede Roudix Kitsune e o layout de teclado de `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions`. O dock fixa o(s) navegador(es) escolhido(s) no Roudix (e o Zen, se ativado), o COSMIC Files, seu terminal, a Roudix Store e o COSMIC Settings — a mesma ideia do dash do GNOME e do gerenciador de tarefas do Plasma. Na biblioteca de aplicativos, todos os aplicativos do Roudix (Store, Customizer, Kernel Switcher, Scheduler, Hardware Sync, Config, Welcome) são agrupados em uma pasta **Roudix** e deixam de aparecer em Sistema / Utilitários. A COSMIC Store não é instalada: a Roudix Store a substitui.

São padrões, entregues como arquivos cosmic-config de todo o sistema: só se aplicam ao que o usuário não alterou, e uma reconstrução nunca reverte uma escolha feita no COSMIC Settings.

Os aplicativos e o painel do próprio COSMIC usam por padrão o esquema de cores do Roudix (`assets/cosmic/`, gerado a partir de `assets/palette/Roudix.json`, instalado como padrões do sistema por `modules/system/desktop/cosmic.nix`, sem Home Manager). Escolher outro tema ou destaque em Configurações > Aparência o sobrescreve, e uma reconstrução nunca toca na sua escolha. «Aplicar o tema atual aos aplicativos GNOME» (Configurações > Desktop > Aparência > Ícones e tema de toolkits) vem ativado por padrão: o próprio COSMIC exporta seu tema, de modo que os aplicativos GTK (navegadores, os aplicativos do Roudix...) recebem as cores do Roudix sobre o adw-gtk3, sem nenhum CSS escrito pelo Roudix. Os ícones são Papirus-Roudix (veja `roudix.iconTheme`), e seu terminal recebe o esquema de cores do Roudix como em todos os outros desktops.

O `system76-scheduler`, que o módulo COSMIC do nixpkgs ativa, vem desativado por padrão porque o Roudix tem sua própria pilha de scheduler (SCX). Para mantê-lo:

```nix
services.system76-scheduler.enable = true;
```

Para mudar os aplicativos fixados, basta fixar / desafixar pelo dock: a sua escolha vale mais que o padrão.

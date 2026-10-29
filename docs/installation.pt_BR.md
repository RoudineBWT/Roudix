[English](installation.md) · [Français](installation.fr.md) · [Español](installation.es.md) · **Português (Brasil)** · [Русский](installation.ru.md) · [简体中文](installation.zh_CN.md) · [हिन्दी](installation.hi.md) · [العربية](installation.ar.md)

# Instalação

Há três formas de colocar o Roudix para funcionar, dependendo do seu ponto de partida:

| Situação | Use |
|-----------|-----|
| Máquina nova, nada instalado ainda | **ISO do Roudix** — inicializa direto em um instalador gráfico (inclui o particionamento) |
| NixOS já instalado (ISO oficial, instalação de NixOS de outra distro, uma VM…) | **`roudix-installer.sh`** — instala o flake do Roudix sobre a sua instalação existente |
| Você quer controlar cada etapa, ou o script não cobre o seu caso | **Instalação manual** (abaixo) |

## Opção A — ISO do Roudix (recomendada para uma instalação nova)

A ISO traz o nosso próprio instalador gráfico GTK4/libadwaita (`roudix-installer`) sobre uma sessão GNOME ao vivo, e cuida do particionamento do disco com o [disko](https://github.com/nix-community/disko) — você não precisa ter o NixOS instalado antes.

1. Baixe a ISO mais recente: vá até a aba **Actions** do repositório → workflow **💿 Build Roudix ISO** → execute-o (`workflow_dispatch`) se não houver uma build recente listada; depois abra a execução e pegue o link de download publicado no resumo do job (a ISO fica hospedada no Cloudflare R2, não como artefato do GitHub).
2. Grave-a em um pendrive (por exemplo, `dd`, Ventoy, Rufus…) e inicialize por ele.
3. A janela do instalador abre automaticamente no login (ela se reexecuta com `sudo`: a sessão ao vivo precisa de root para o disko/`nixos-install`). Percorra as páginas: seleção de disco, kernel, desktop, navegador, editor, Discord, aplicativos de jogos, localidade, fuso horário, layout de teclado, controlador RGB e módulos opcionais.
4. Ao confirmar, ele particiona o disco (disko), copia o flake do Roudix embutido na ISO para `/mnt/etc/nixos` e executa `nixos-install --flake /mnt/etc/nixos#roudix`.

> **Nota:** o menu de boot também oferece especializações de layout de teclado (US/BE/FR/DE/CH/UK) caso o teclado da sessão ao vivo não corresponda ao físico — escolha uma antes de iniciar o instalador.

Este caminho substitui por completo as duas etapas abaixo (não é preciso usar o `roudix-installer.sh` nem as etapas manuais) — pule para o que vem depois da instalação, quando ele reiniciar.

## Opção B — Você já tem o NixOS instalado

Se o NixOS já está instalado (pela ISO oficial stable/unstable ou por qualquer outro meio) e você só quer colocar o Roudix por cima, há dois instaladores: o gráfico (a partir de uma sessão de desktop) e o script bash (funciona em um TTY puro).

> **Nota:** instale primeiro o NixOS com a ISO [stable](https://nixos.org/download/) ou [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165), e depois execute um dos instaladores abaixo ou siga a instalação manual.

### B1 — Instalador gráfico (recomendado em um desktop)

O mesmo assistente da ISO, sem a página de disco. Execute-o a partir da conta que você quer manter:

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **Nada é apagado.** A configuração vai para `~/.config/roudix` (uma pasta existente é movida para o lado, nunca excluída); depois o `nixos-rebuild boot` constrói o Roudix e o agenda para a próxima inicialização. Seu sistema atual continua no menu de boot.
- **Seu `/etc/nixos` recebe backup** em `/var/backups/roudix/nixos-<date>/`, junto com um `RESTORE.txt` (geração anterior, bootloader, `stateVersion` e os comandos exatos para voltar). O `hardware-configuration.nix` é reutilizado como está, nunca sobrescrito.
- **Simule primeiro.** O botão *Simular* na página de resumo gera a configuração em uma pasta temporária, verifica se todas as opções foram gravadas e faz o Nix avaliar o sistema inteiro. Nada na sua máquina é modificado.
- Avisos prévios: pouco espaço livre em `/boot` (uma partição EFI de 512 MB enche rápido), mudança de bootloader, um `system.stateVersion` mais antigo.
- Pede sua senha de administrador por um diálogo do polkit (precisa de um agente polkit, ou seja, qualquer sessão de desktop normal).

**Voltar atrás:** escolha a geração anterior no menu de boot e depois `sudo nixos-rebuild switch --rollback`. Se a máquina não inicializar de jeito nenhum, o `RESTORE.txt` explica como restaurar sua configuração antiga a partir de um USB ao vivo.

### B2 — Script bash (TTY / sem sessão gráfica)

**Baixe o script roudix-installer**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

O instalador cuida de tudo de forma interativa:
- Pergunta qual branch instalar e acompanhar (`main` = estável, `testing`, `dev`), clona, gera o `hardware-configuration.nix` e cria todos os arquivos de configuração local
- **Detecta outros sistemas operacionais automaticamente** pela NVRAM EFI (`efibootmgr`) — sem procurar PARTUUID manualmente
- **Detecta GPU e CPU automaticamente** (`lspci` / `/proc/cpuinfo`) — pré-seleciona e pede confirmação
- **Detecta se está rodando em uma VM** (`systemd-detect-virt`) — pré-ativa o modo convidado de VM e avisa que a detecção de GPU/CPU pode ser imprecisa
- Pergunta sobre kernel, desktop, navegador, editor, Discord, aplicativos de jogos, localidade, fuso horário, keymap, controlador RGB e módulos opcionais
- Constrói e aplica a configuração

---

## Opção C — Instalação manual

> ⚠️ **Siga cada etapa com atenção antes de reconstruir.**

### 1. Clone o repositório

> **Se o `git` não estiver instalado** (instalação nova do NixOS):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **Caso contrário:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Defina seu nome de usuário

Crie o arquivo `username.nix` com o seu nome de usuário:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> Este arquivo está no gitignore — ele nunca será sobrescrito por um `git pull`.

### 3. Substitua o hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Crie suas configurações locais

**Nunca edite o `configuration.nix` nem o `modules/home/common.nix` diretamente** — eles são sobrescritos pelo `git pull`.
Em vez disso, crie seus arquivos locais de personalização (todos no gitignore):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp modules/home/local.nix.example modules/home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

Edite o `hosts/roudix/local.nix` para corresponder ao seu hardware:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "mangowc", "umbriel", "gnome" ou "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" ou "intel"
  hardware.myCpu      = "intel";              # "intel" ou "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # kernel do xddxdd — usado quando hardware.myGpu != "nvidia"
  hardware.myKernelChaotic = "cachyos";            # kernel do Chaotic-Nyx — usado somente quando hardware.myGpu == "nvidia"
  roudix.boot.bootloader = "limine";          # "limine" ou "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" ou []
  roudix.zen.enable   = false;                # defina como true para instalar também o Zen Browser (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub", "openrgb" ou "none" — veja abaixo
  roudix.mesa.useGit  = false;                # true = mesa-git (experimental, a build pode falhar), false = nixpkgs estável
  roudix.matrixClient = "none";               # "element", "cinny" ou "none"
  roudix.discord      = "vencord";            # "vencord", "vanilla" ou "none"
  roudix.editor       = "zed";                # "zed", "vscode", "neovim" ou "none"

  # ── Aplicativos de jogos (todos true por padrão — desative o que você não quiser) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── Integração com compositor puro (somente niri/hyprland/mangowc/umbriel) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" ou "kde" — chaveiro + pilha xdg-desktop-portal; sem efeito em sessões gnome/kde

  # ── Localidade / Fuso horário ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # veja https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # deve corresponder a time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # localidade do sistema
  console.keyMap                  = "us";              # layout de teclado do console — somente TTY, antes de a sessão gráfica iniciar

  # ── Layout de teclado gráfico (Wayland) — independente de console.keyMap ─
  # Sem efeito no GNOME/KDE, que gerenciam o próprio layout pelo seu daemon de configurações.
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl", "nodeadkeys", "bepo", "dvorak", "colemak", "" (nenhum)
}
```

**Opções de controlador RGB:**

| Valor | Descrição |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — configuração completa da Corsair (iCUE Link, Commander...) |
| `openrgb` | OpenRGB — marcas variadas (Razer, ASUS, MSI...) |
| `none` | Sem gerenciamento de RGB |

**RGB da RAM (somente OpenLinkHub):**

Se você selecionou `openlinkhub`, também pode ativar o controle de RGB da sua RAM Corsair DDR4/DDR5. Adicione estas linhas ao `hosts/roudix/local.nix`:

```nix
roudix.memory.enable = true;                  # ativar o RGB da RAM via SMBus
roudix.memory.type   = "ddr5";                # "ddr4" ou "ddr5"
roudix.memory.smBus  = "i2c-9";              # descubra com: sudo i2cdetect -l (procure "SMBus")
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # descubra com: sudo dmidecode -t memory | grep 'Part Number'
```

Para descobrir os valores corretos antes de defini-los:

```bash
# Instale as ferramentas necessárias se não estiverem disponíveis (instalação nova do NixOS)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# Encontre o seu SMBus (uma linha com "SMBus", "i801", "piix4" ou "nforce")
sudo i2cdetect -l

# Encontre o part number da sua RAM
sudo dmidecode -t memory | grep 'Part Number'
```

> **Nota:** `roudix.memory.enable` aplica automaticamente `acpi_enforce_resources=lax` como parâmetro do kernel e coloca `spd5118` (DDR5) ou `ee1004` (DDR4) na lista de bloqueio para liberar o SMBus. O `config.json` do OpenLinkHub é ajustado automaticamente na ativação.

**Valores comuns de fuso horário:**

| Fuso horário | Região |
|----------|--------|
| `Europe/Brussels` | Bélgica |
| `Europe/Paris` | França |
| `Europe/London` | Reino Unido |
| `Europe/Berlin` | Alemanha |
| `Europe/Amsterdam` | Países Baixos |
| `America/New_York` | EUA (Leste) |
| `America/Los_Angeles` | EUA (Oeste) |
| `Asia/Tokyo` | Japão |
| `UTC` | Universal |

**Valores comuns de localidade:**

| Localidade | Idioma |
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

**Valores comuns de keymap do console:**

| Keymap | Layout |
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

> **Nota:** `environment.sessionVariables.TZ` deve sempre corresponder a `time.timeZone` — ambos controlam o fuso horário, um no nível do sistema e outro no nível da sessão.

Edite o `modules/home/local.nix` para personalizações pessoais do home-manager (pacotes extras, dotfiles, aliases, fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> Veja `modules/home/local.nix.example` para todas as opções de personalização disponíveis, incluindo a personalização do fastfetch.

### 5. Configure o kernel

O Roudix usa **dois provedores de kernel diferentes**, dependendo da sua GPU:

- **`hardware.myGpu != "nvidia"`** (AMD ou Intel) → kernel do [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), escolhido por `hardware.myKernel`. Sem módulo Nvidia com que se preocupar, então o conjunto completo de 36 variantes está disponível.
- **`hardware.myGpu == "nvidia"`** → kernel do **Chaotic-Nyx**, escolhido por `hardware.myKernelChaotic`. Isso é necessário para obter o **`nvidia_cachyos`**, um driver Nvidia pré-compilado que combina com o kernel deles — caso contrário, o módulo de kernel da Nvidia é recompilado localmente a cada atualização do kernel. O conjunto de variantes aqui é menor de propósito (o Chaotic-Nyx não publica tantas variantes, e as variantes `-lto` têm mais chance de quebrar módulos externos como o da Nvidia).

Ambas as opções também aceitam alguns **kernels simples do nixpkgs**, totalmente fora do respectivo overlay do CachyOS — úteis se você só quer um kernel padrão sem patches do CachyOS: `zen`, `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing`, `xanmod-lts`, `xanmod-latest`. No caminho Nvidia, eles dispensam o cache do `nvidia_cachyos` e recompilam o módulo Nvidia localmente (veja `nvidia.nix`).

**Kernels do nixpkgs mais recentes — `hardware.myKernelSource`:** esses kernels do nixpkgs seguem por padrão o input principal `nixpkgs` (nixos-unstable). Defina `hardware.myKernelSource` como `"master"` ou `"staging-next"` para pegar **somente o kernel** (e os módulos externos compilados contra ele, como o da Nvidia) desse branch do NixOS/nixpkgs e receber as atualizações do kernel mais cedo — o resto do sistema não é alterado. Valores: `"nixpkgs"` (padrão), `"master"`, `"staging-next"`. Ressalvas: esse kernel pode ainda não estar em um cache binário, então espere uma compilação local demorada; o `staging-next` também carrega mudanças de toolchain em andamento, sendo o mais arriscado dos três. Não tem efeito sobre os kernels `cachyos-*` (um aviso é exibido). Depois de definir, execute `nix flake lock` uma vez para que o novo input seja travado.

**Variantes de `hardware.myKernel` (xddxdd — somente AMD/Intel):**

| Variante | Descrição |
|---------|-------------|
| `zen` | `linuxPackages_zen` simples (nixpkgs) — fora do overlay do xddxdd |
| `nixpkgs-lts` | Kernel LTS padrão do nixpkgs, sem modificações — fora do overlay do xddxdd |
| `nixpkgs-latest` | Kernel mainline mais recente do nixpkgs, sem modificações — fora do overlay do xddxdd |
| `nixpkgs-testing` | `linux_testing` simples do nixpkgs (RC/mainline) — fora do overlay do xddxdd |
| `xanmod-lts` | Branch XanMod LTS (`linuxPackages_xanmod`, nixpkgs) — governor de desempenho, preempção lazy, BBRv3 |
| `xanmod-latest` | Branch principal do XanMod (`linuxPackages_xanmod_latest`, nixpkgs) |
| `cachyos-latest` | Kernel CachyOS mais recente, padrão |
| `cachyos-latest-v2` | otimizado para x86_64-v2 |
| `cachyos-latest-v3` | otimizado para x86_64-v3 (recomendado para CPUs modernas) |
| `cachyos-latest-v4` | otimizado para x86_64-v4 (AVX-512, somente CPUs muito recentes) |
| `cachyos-latest-zen4` | otimizado para AMD Zen 4 |
| `cachyos-latest-lto` | Build LTO para melhor desempenho |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (melhor desempenho, somente CPUs modernas) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | Kernel CachyOS de suporte de longo prazo |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + otimizado para x86_64-v3 |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (estável + desempenho) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | Agendador BMQ |
| `cachyos-bmq-lto` | Agendador BMQ + LTO |
| `cachyos-bore` | Agendador BORE (melhor interatividade) |
| `cachyos-bore-lto` | Agendador BORE + LTO |
| `cachyos-deckify` | Otimizado para Steam Deck |
| `cachyos-deckify-lto` | Otimizado para Steam Deck + LTO |
| `cachyos-eevdf` | Agendador EEVDF |
| `cachyos-eevdf-lto` | Agendador EEVDF + LTO |
| `cachyos-hardened` | Kernel reforçado em segurança |
| `cachyos-hardened-lto` | Reforçado em segurança + LTO |
| `cachyos-rc` | Release candidate — na ponta da inovação, potencialmente instável |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | Tempo real + agendador BORE |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | Otimizado para servidor (sem ajustes de desktop) |
| `cachyos-server-lto` | Otimizado para servidor + LTO |

**Variantes de `hardware.myKernelChaotic` (Chaotic-Nyx — somente Nvidia):**

| Variante | Descrição |
|---------|-------------|
| `cachyos` | Padrão — LTO + agendador BORE, acompanha o `nvidia_cachyos` correspondente |
| `cachyos-lts` | Suporte de longo prazo |
| `cachyos-server` | Otimizado para servidor (sem ajustes de desktop) |
| `cachyos-hardened` | Reforçado em segurança |
| `zen` | `linuxPackages_zen` simples (nixpkgs) — módulo Nvidia recompilado localmente |
| `nixpkgs-lts` | LTS simples do nixpkgs — módulo Nvidia recompilado localmente |
| `nixpkgs-latest` | Mainline mais recente do nixpkgs, sem modificações — módulo Nvidia recompilado localmente |
| `nixpkgs-testing` | `linux_testing` simples do nixpkgs (RC) — módulo Nvidia recompilado localmente |
| `xanmod-lts` | XanMod LTS (nixpkgs) — módulo Nvidia recompilado localmente |
| `xanmod-latest` | Branch principal do XanMod (nixpkgs) — módulo Nvidia recompilado localmente |

> **Nota sobre NVIDIA:** somente GTX 20xx / série RTX e mais recentes são suportadas. Os drivers abertos vêm ativados por padrão para RTX 20xx+ (Turing+). GTX 10xx/16xx não são suportadas.

> **Nota sobre o tema Spicetify Comfy:** depois da sua primeira build, copie o color.ini manualmente:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/apps/media/spicetify/Comfy/color.ini
> ```
> Depois execute `rebuild` para aplicar.

### 6. Atualize a montagem do disco

No `hosts/roudix/local.nix`, adicione um bloco `lib.mkForce` com o seu próprio UUID (ou pule se não houver disco secundário):

```bash
lsblk -f  # descubra o UUID do seu disco
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Configure o multi-boot do Limine (opcional)

> Pule esta etapa se você só tem o NixOS na máquina.

O Limine pode inicializar outros sistemas operacionais em discos separados. O `boot.local.nix` controla as entradas extras — ele está no gitignore e nunca é sobrescrito pelo `git pull`.

**Nunca edite o `modules/system/boot/boot.nix` diretamente** — ele é sobrescrito pelo `git pull`.

#### Se você usou o instalador automático

O instalador detectou seus outros sistemas operacionais automaticamente pela NVRAM EFI (`efibootmgr`) e escreveu o `boot.local.nix` para você — nenhuma ação manual é necessária. Você pode revisar o resultado:

```bash
cat modules/system/boot/boot.local.nix
```

#### Se você está instalando manualmente

**Obtenha seus PARTUUIDs:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Procure partições com o tipo de sistema de arquivos `vfat` e o rótulo `EFI system partition` — essas são as suas ESPs.

**Edite o `modules/system/boot/boot.local.nix`** e adicione suas entradas:

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

> **Dica:** o caminho EFI depois do UUID depende do bootloader usado pelo outro sistema operacional. Caminhos comuns:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - Qualquer distro (alternativa): `/EFI/BOOT/BOOTX64.EFI`

Se você não tem outro sistema operacional para adicionar, deixe `extraEntries` vazio:

```nix
{
  extraEntries = "";
}
```

> O `boot.local.nix` está listado no `.gitignore` — ele nunca será sobrescrito por um `git pull`.

### 8. Atualize a configuração do git

O `modules/home/dev/git.nix` está no gitignore (como o `local.nix`) — copie o modelo versionado e preencha a sua identidade:

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

- `init.defaultBranch = "main"` — nome usado para o primeiro branch quando você faz `git init` em um repositório novo (não afeta o branch deste repositório, apenas os que você criar).
- `pull.rebase = false` — o que o `git pull` faz quando o seu branch local e o remoto divergiram: `false` faz merge (cria um commit de merge, o comportamento padrão e mais simples), `true` reaplica seus commits locais sobre o remoto (histórico linear, mas reescreve seus commits — evite se você não se sente à vontade com conflitos de rebase). `false` é a escolha mais segura para um repositório de configuração pessoal.

> Se o arquivo não existir, o `common.nix` simplesmente o ignora — o Home Manager não configurará o git até você copiá-lo, mas nada quebra.

### 9. Ative/desative módulos opcionais

No `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + atualização automática diária
roudix.fstrim.enable         = true;   # recomendado para SSD/NVMe
roudix.virtualization.enable = false;  # ative para QEMU/KVM
roudix.vmGuest.enable        = true;   # ative somente dentro de uma VM
roudix.hosts.gtaFix.enable   = true;   # bloqueia a telemetria do BattlEye (correção do GTA)
roudix.autoupdate.enable     = true;   # git pull automático + nh os boot quando houver mudanças
roudix.zen.enable            = false;  # instala o Zen Browser (desativado por padrão)
roudix.mesa.useGit           = false;  # true = mesa-git (experimental, de ponta — a build pode falhar), false = nixpkgs estável
roudix.boot.bootloader       = "limine";  # "limine" ou "systemd-boot"
roudix.matrixClient          = "none"; # "element", "cinny" ou "none"
```

> **Lembrete:** se você definir `roudix.autoupdate.enable = true`, configure também o intervalo:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. Personalize o fastfetch (opcional)

Por padrão, o Roudix mostra o seu logo ASCII no fastfetch. Você pode substituí-lo no `modules/home/local.nix` sem mexer no git:

```nix
# Use uma imagem personalizada (requer o terminal kitty)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Use um arquivo ASCII personalizado
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Substitua toda a configuração do fastfetch (substitui tudo)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` sobrescreve toda a configuração padrão do Roudix. Sem ele, suas chaves são mescladas com as padrão.
> Veja `modules/home/local.nix.example` para mais exemplos.

### 11. Construa

> **Se flakes e nix-command ainda não estiverem ativados** (instalação nova do NixOS):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **Caso contrário:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

Depois de construído, use os aliases do fish para todas as operações futuras.

> Os três arquivos `local.nix` e o `boot.local.nix` estão listados no `.gitignore` — eles nunca serão sobrescritos por um `git pull`.

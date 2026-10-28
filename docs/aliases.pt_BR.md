[English](aliases.md) · [Français](aliases.fr.md) · [Español](aliases.es.md) · **Português (Brasil)** · [Русский](aliases.ru.md) · [简体中文](aliases.zh_CN.md) · [हिन्दी](aliases.hi.md) · [العربية](aliases.ar.md)

# Aliases e funções

## Disponíveis em qualquer lugar

| Alias | Ação |
|-------|--------|
| `rebuild` | Aplicar a configuração imediatamente |
| `update` | Fazer pull da configuração, reconstruir + switch, atualizar os Flatpaks (veja [abaixo](#update)) |
| `cleanup` | Remover gerações antigas + coleta de lixo |
| `noctalia-reload` | Reiniciar o Noctalia sem encerrar a sessão |
| `dms-reload` | Reiniciar o Quickshell sem encerrar a sessão |
| `caelestia-reload` | Reiniciar o Quickshell sem encerrar a sessão |
| `roudix-switch <de>` | Trocar de ambiente de desktop (aplica na próxima reinicialização) |
| `roudix-kernel-switch <kernel>` | Trocar de variante de kernel (aplica na próxima reinicialização) |

### `update`

Equivalente manual da [atualização automática](autoupdate.pt_BR.md): mesmo repositório, mesmo branch acompanhado, mesma regra de apenas fast-forward (seus commits locais nunca são tocados). Roda com seu usuário normal e usa `sudo` somente onde é necessário.

1. `git pull --ff-only` do branch acompanhado (ignorado se você estiver em outro branch, ex.: um branch de feature)
2. `nh os switch` (ou `nh os boot` com `--boot`)
3. Atualização dos Flatpaks, de usuário e de sistema, e remoção dos runtimes sem uso (nunca é fatal)

O `flake.lock` que você recebe do git é o que a CI já construiu e validou, então um simples `update` **não** atualiza os inputs do flake.

| Opção | Efeito |
|--------|--------|
| `-i`, `--inputs [name…]` | Também atualiza os inputs do flake localmente (todos, ou só os indicados). Se a construção falhar, o `flake.lock` é restaurado |
| `-b`, `--boot` | Aplicar na próxima inicialização em vez de fazer switch agora |
| `-c`, `--check` | Apenas informar se há novos commits disponíveis |
| `-n`, `--dry` | Simulação (`nh --dry`): nada é baixado, atualizado, ativado ou instalado |
| `--changes` | Mostra o que o sistema da próxima inicialização muda em relação ao que está rodando (útil após uma atualização automática) |
| `--log` | Mostra o log da última execução (guardado em `~/.local/state/roudix/update.log`) |
| `--no-inputs` | Pular a atualização dos inputs (útil com `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | Pular o pull / a atualização dos Flatpaks |

```fish
update                    # pull + reconstruir + switch
update --inputs           # atualizar todos os inputs e reconstruir
update --inputs nixpkgs   # atualizar apenas o nixpkgs
```

Em uma máquina que acompanha o `dev` e sempre quer inputs recentes, defina `roudix.update.bumpInputs = true;` no `local.nix`: um simples `update` passa então a se comportar como `update --inputs`.

> Depois de `update --inputs`, o `flake.lock` é uma modificação local: faça commit e push (ou `git checkout flake.lock`); caso contrário, o próximo pull da atualização automática pode se recusar a rodar se a CI tiver mexido no lock nesse meio-tempo.

## Somente Niri, Hyprland e MangoWC

| Alias | Ação |
|-------|--------|
| `roudix-shell-switch <shell>` | Trocar de shell gráfico (aplica na próxima reinicialização) |

### Uso

```fish
# Trocar de ambiente de desktop
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde
roudix-switch cinnamon
roudix-switch cosmic

# Trocar de variante de kernel — a lista depende de hardware.myGpu, veja docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — conjunto menor, necessário para o cache binário do nvidia_cachyos):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# Kernels simples do nixpkgs — disponíveis nos dois caminhos de GPU, fora do overlay do CachyOS
# (na Nvidia, recorrem a um módulo Nvidia reconstruído localmente, sem o cache do nvidia_cachyos):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# Trocar de shell gráfico (somente Niri, Hyprland e MangoWC)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # apenas para hyprland
```

Os três comandos editam `hosts/roudix/local.nix` automaticamente e executam `nh os boot` — não é preciso reconstruir manualmente. As mudanças são aplicadas na próxima reinicialização.

> **Nota:** `roudix-kernel-switch` grava em `hardware.myKernel` ou `hardware.myKernelChaotic` automaticamente, conforme o seu `hardware.myGpu` atual — passe o nome da variante correspondente à lista da sua GPU (veja a tabela acima).

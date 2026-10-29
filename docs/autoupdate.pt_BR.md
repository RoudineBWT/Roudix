[English](autoupdate.md) · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · **Português (Brasil)** · [Русский](autoupdate.ru.md) · [简体中文](autoupdate.zh_CN.md) · [हिन्दी](autoupdate.hi.md) · [العربية](autoupdate.ar.md)

# Atualização automática

Quando `roudix.autoupdate.enable = true`, o sistema consulta o GitHub a cada hora (e 5 min depois da inicialização).
Se novos commits forem detectados no branch acompanhado (`main` por padrão), ele faz um pull e executa `nh os boot path:...` — a nova configuração é aplicada na próxima reinicialização.
Seus arquivos `local.nix`, `username.nix`, `hardware-configuration.nix`, os opcionais `modules/home/niri-custom.nix` / `modules/home/umbriel-custom.nix` / `modules/home/mango-custom.nix` e tudo que estiver em `dotfiles/perso/` estão no gitignore e nunca são tocados pelo pull.

Para configurar o intervalo ou o branch, sobrescreva em `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # se você colocar false aqui, o config.roudix.autoupdate assume a atualização, mas sem git pull
  roudix.autoupdate.interval = "6h";   # verificar a cada 6 horas em vez de 1h
  roudix.autoupdate.branch   = "main"; # branch a acompanhar: "main" (estável), "testing" ou "dev" — definido pelo instalador
}
```

O branch é escolhido no instalador (tanto o script quanto o instalador gráfico da ISO). Você pode mudá-lo depois em **Roudix Switcher → System → Update branch**, que também move seu checkout local de `~/.config/roudix` para esse branch antes de reconstruir.

A atualização automática só faz fast-forward: se sua máquina tiver commits locais que não estão no GitHub (ou tiver divergido), ela não mexe neles e avisa você com uma notificação.

Ver a última execução:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

Para disparar uma atualização manualmente a qualquer momento:

```fish
update
```

Ele faz o mesmo pull (mesmo branch, mesma regra de apenas fast-forward, mesmo lock, então nunca se sobrepõe a uma atualização automática em andamento), depois reconstrói e atualiza seus Flatpaks. Veja [`update`](aliases.pt_BR.md#update) para as opções.

A construção pode levar até 2 horas antes de o systemd desistir. Se a execução for interrompida ou parar de forma inesperada (timeout, falha), uma notificação é enviada; um erro simples já notifica por conta própria. Depois de uma atualização automática, `update --changes` mostra o que será aplicado na próxima inicialização.

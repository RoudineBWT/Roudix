[English](autoupdate.md) · [Français](autoupdate.fr.md) · **Español** · [Português (Brasil)](autoupdate.pt_BR.md) · [Русский](autoupdate.ru.md) · [简体中文](autoupdate.zh_CN.md) · [हिन्दी](autoupdate.hi.md) · [العربية](autoupdate.ar.md)

# Actualización automática

Cuando `roudix.autoupdate.enable = true`, el sistema consulta GitHub cada hora (y 5 min después del arranque).
Si se detectan commits nuevos en la rama seguida (`main` por defecto), hace un pull y ejecuta `nh os boot path:...` — la nueva configuración se aplica en el próximo reinicio.
Tus archivos `local.nix`, `username.nix`, `hardware-configuration.nix`, los opcionales `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix` y todo lo que haya en `dotfiles/perso/` están en el gitignore y el pull nunca los toca.

Para configurar el intervalo o la rama, sobrescribe en `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # si pones false aquí, config.roudix.autoupdate tomará el relevo para actualizar, pero sin git pull
  roudix.autoupdate.interval = "6h";   # comprobar cada 6 horas en lugar de cada hora
  roudix.autoupdate.branch   = "main"; # rama a seguir: "main" (estable), "testing" o "dev" — la fija el instalador
}
```

La rama se elige en el instalador (tanto el script como el instalador gráfico de la ISO). Puedes cambiarla después desde **Roudix Switcher → System → Update branch**, que además cambia tu copia local de `~/.config/roudix` a esa rama antes de reconstruir.

La actualización automática solo hace fast-forward: si tu equipo tiene commits locales que no están en GitHub (o ha divergido), no los toca y te avisa con una notificación.

Ver la última ejecución:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

Para lanzar una actualización a mano en cualquier momento:

```fish
update
```

Hace el mismo pull (misma rama, misma regla de solo fast-forward, mismo bloqueo: nunca se solapa con una actualización automática en curso), luego reconstruye y actualiza tus Flatpaks. Consulta [`update`](aliases.es.md#update) para ver sus opciones.

La compilación puede tardar hasta 2 horas antes de que systemd se rinda. Si la ejecución se interrumpe o se detiene de forma inesperada (timeout, fallo), se envía una notificación; un error simple ya notifica por sí solo. Tras una actualización automática, `update --changes` muestra lo que se aplicará en el próximo arranque.

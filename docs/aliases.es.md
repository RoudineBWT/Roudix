[English](aliases.md) · [Français](aliases.fr.md) · **Español** · [Português (Brasil)](aliases.pt_BR.md) · [Русский](aliases.ru.md) · [简体中文](aliases.zh_CN.md) · [हिन्दी](aliases.hi.md) · [العربية](aliases.ar.md)

# Alias y funciones

## Disponibles en todas partes

| Alias | Acción |
|-------|--------|
| `rebuild` | Aplicar la configuración inmediatamente |
| `update` | Hacer pull de la configuración, reconstruir + switch, actualizar Flatpaks (ver [más abajo](#update)) |
| `cleanup` | Eliminar generaciones antiguas + recolección de basura |
| `noctalia-reload` | Reiniciar Noctalia sin cerrar la sesión |
| `dms-reload` | Reiniciar Quickshell sin cerrar la sesión |
| `caelestia-reload` | Reiniciar Quickshell sin cerrar la sesión |
| `roudix-switch <de>` | Cambiar de entorno de escritorio (se aplica en el próximo reinicio) |
| `roudix-kernel-switch <kernel>` | Cambiar de variante de kernel (se aplica en el próximo reinicio) |

### `update`

Equivalente manual de la [actualización automática](autoupdate.es.md): mismo repositorio, misma rama seguida, misma regla de solo fast-forward (tus commits locales nunca se tocan). Se ejecuta con tu usuario normal y usa `sudo` solo donde hace falta.

1. `git pull --ff-only` de la rama seguida (se omite si estás en otra rama, p. ej. una rama de feature)
2. `nh os switch` (o `nh os boot` con `--boot`)
3. Actualización de Flatpak, de usuario y de sistema, y eliminación de los runtimes sin uso (nunca es fatal)

El `flake.lock` que obtienes de git es el que la CI ya construyó y validó, así que un simple `update` **no** actualiza los inputs del flake.

| Opción | Efecto |
|--------|--------|
| `-i`, `--inputs [name…]` | Actualiza también los inputs del flake en local (todos, o solo los indicados). Si la compilación falla, se restaura `flake.lock` |
| `-b`, `--boot` | Aplicar en el próximo arranque en lugar de hacer switch ahora |
| `-c`, `--check` | Solo informar de si hay commits nuevos disponibles |
| `-n`, `--dry` | Simulación (`nh --dry`): no se hace pull, ni se actualiza, activa o instala nada |
| `--changes` | Muestra qué cambiará el sistema del próximo arranque respecto al que está en ejecución (útil tras una actualización automática) |
| `--log` | Muestra el registro de la última ejecución (guardado en `~/.local/state/roudix/update.log`) |
| `--no-inputs` | Omitir la actualización de inputs (útil con `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | Omitir el pull / la actualización de Flatpak |

```fish
update                    # pull + reconstruir + switch
update --inputs           # actualizar todos los inputs y reconstruir
update --inputs nixpkgs   # actualizar solo nixpkgs
```

En un equipo que sigue `dev` y siempre quiere inputs recientes, pon `roudix.update.bumpInputs = true;` en `local.nix`: un simple `update` se comportará entonces como `update --inputs`.

> Después de `update --inputs`, `flake.lock` es una modificación local: haz commit y push (o `git checkout flake.lock`); de lo contrario, el próximo pull de la actualización automática puede negarse a ejecutarse si la CI ha tocado el lock mientras tanto.

## Solo Niri, Hyprland y MangoWC

| Alias | Acción |
|-------|--------|
| `roudix-shell-switch <shell>` | Cambiar de shell gráfico (se aplica en el próximo reinicio) |

### Uso

```fish
# Cambiar de entorno de escritorio
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde
roudix-switch cinnamon
roudix-switch cosmic

# Cambiar de variante de kernel — la lista depende de hardware.myGpu, ver docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — conjunto más reducido, necesario para la caché binaria de nvidia_cachyos):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# Kernels de nixpkgs sin modificar — disponibles en ambas rutas de GPU, fuera del overlay de CachyOS
# (en Nvidia recurren a un módulo Nvidia reconstruido localmente, sin la caché de nvidia_cachyos):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# Cambiar de shell gráfico (solo Niri, Hyprland y MangoWC)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # solo para hyprland
```

Los tres comandos editan `hosts/roudix/local.nix` automáticamente y ejecutan `nh os boot` — no hace falta reconstruir a mano. Los cambios se aplican en el próximo reinicio.

> **Nota:** `roudix-kernel-switch` escribe en `hardware.myKernel` o `hardware.myKernelChaotic` automáticamente según tu `hardware.myGpu` actual — pasa el nombre de la variante que corresponda a la lista de tu GPU (ver la tabla de arriba).

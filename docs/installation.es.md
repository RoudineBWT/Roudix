[English](installation.md) · [Français](installation.fr.md) · **Español** · [Português (Brasil)](installation.pt_BR.md) · [Русский](installation.ru.md) · [简体中文](installation.zh_CN.md) · [हिन्दी](installation.hi.md) · [العربية](installation.ar.md)

# Instalación

Hay tres formas de poner Roudix en marcha, según tu punto de partida:

| Situación | Usa |
|-----------|-----|
| Equipo nuevo, sin nada instalado | **ISO de Roudix** — arranca directamente en un instalador gráfico (incluye el particionado) |
| NixOS ya instalado (ISO oficial, instalación de NixOS de otra distro, una VM…) | **`roudix-installer.sh`** — instala el flake de Roudix sobre tu instalación existente |
| Quieres controlar cada paso, o el script no cubre tu caso | **Instalación manual** (más abajo) |

## Opción A — ISO de Roudix (recomendada para una instalación nueva)

La ISO incluye nuestro propio instalador gráfico GTK4/libadwaita (`roudix-installer`) sobre una sesión GNOME en vivo, y se encarga del particionado del disco con [disko](https://github.com/nix-community/disko) — no necesitas tener NixOS instalado antes.

1. Descarga la última ISO: ve a la pestaña **Actions** del repositorio → flujo de trabajo **💿 Build Roudix ISO** → ejecútalo (`workflow_dispatch`) si no hay ninguna compilación reciente en la lista; luego abre la ejecución y coge el enlace de descarga publicado en el resumen del job (la ISO está alojada en Cloudflare R2, no como artefacto de GitHub).
2. Grábala en una unidad USB (p. ej. `dd`, Ventoy, Rufus…) y arranca desde ella.
3. La ventana del instalador se abre automáticamente al iniciar sesión (se vuelve a lanzar con `sudo`: la sesión en vivo necesita root para disko/`nixos-install`). Recorre las páginas: selección de disco, kernel, escritorio, navegador, editor, Discord, aplicaciones de gaming, configuración regional, zona horaria, distribución de teclado, controlador RGB y módulos opcionales.
4. Al confirmar, particiona el disco (disko), copia el flake de Roudix incluido en la ISO a `/mnt/etc/nixos` y ejecuta `nixos-install --flake /mnt/etc/nixos#roudix`.

> **Nota:** el menú de arranque también ofrece especializaciones de distribución de teclado (US/BE/FR/DE/CH/UK) por si el teclado de la sesión en vivo no coincide con el físico — elige una antes de iniciar el instalador.

Esta vía sustituye por completo los dos pasos siguientes (no hace falta `roudix-installer.sh` ni los pasos manuales) — pasa a lo que venga después de la instalación una vez que reinicie.

## Opción B — Ya tienes NixOS instalado

Si NixOS ya está instalado (con la ISO oficial stable/unstable, o por cualquier otro medio) y solo quieres instalar Roudix encima, hay dos instaladores: el gráfico (desde una sesión de escritorio) y el script bash (funciona desde un TTY puro).

> **Nota:** instala primero NixOS con la ISO [stable](https://nixos.org/download/) o [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165), y luego ejecuta uno de los instaladores de abajo o sigue la instalación manual.

### B1 — Instalador gráfico (recomendado en un escritorio)

El mismo asistente que la ISO, sin la página de disco. Ejecútalo desde la cuenta que quieres conservar:

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **No se borra nada.** La configuración va a `~/.config/roudix` (una carpeta existente se aparta, nunca se elimina); después `nixos-rebuild boot` construye Roudix y lo programa para el próximo arranque. Tu sistema actual sigue en el menú de arranque.
- **Se hace copia de seguridad de tu `/etc/nixos`** en `/var/backups/roudix/nixos-<date>/` junto con un `RESTORE.txt` (generación anterior, gestor de arranque, `stateVersion` y los comandos exactos para volver atrás). `hardware-configuration.nix` se reutiliza tal cual, nunca se sobrescribe.
- **Simula primero.** El botón *Simular* de la página de resumen genera la configuración en una carpeta temporal, comprueba que se escribió cada opción y hace que Nix evalúe todo el sistema. No se modifica nada en tu equipo.
- Avisos previos: poco espacio libre en `/boot` (una partición EFI de 512 MB se llena rápido), un cambio de gestor de arranque, un `system.stateVersion` más antiguo.
- Pide tu contraseña de administrador mediante un diálogo de polkit (necesita un agente polkit, es decir, cualquier sesión de escritorio normal).

**Volver atrás:** elige la generación anterior en el menú de arranque y luego `sudo nixos-rebuild switch --rollback`. Si el equipo no arranca en absoluto, `RESTORE.txt` explica cómo restaurar tu configuración anterior desde un USB en vivo.

### B2 — Script bash (TTY / sin sesión gráfica)

**Descarga el script roudix-installer**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

El instalador lo gestiona todo de forma interactiva:
- Pregunta qué rama instalar y seguir (`main` = estable, `testing`, `dev`), la clona, genera `hardware-configuration.nix` y crea todos los archivos de configuración local
- **Detecta otros sistemas operativos automáticamente** mediante la NVRAM EFI (`efibootmgr`) — sin buscar PARTUUID a mano
- **Detecta la GPU y la CPU automáticamente** (`lspci` / `/proc/cpuinfo`) — las preselecciona y pide confirmación
- **Detecta si se ejecuta en una VM** (`systemd-detect-virt`) — preactiva el modo invitado de VM y avisa de que la detección de GPU/CPU puede ser imprecisa
- Pregunta por kernel, escritorio, navegador, editor, Discord, aplicaciones de gaming, configuración regional, zona horaria, mapa de teclado, controlador RGB y módulos opcionales
- Construye y aplica la configuración

---

## Opción C — Instalación manual

> ⚠️ **Sigue cada paso con atención antes de reconstruir.**

### 1. Clona el repositorio

> **Si `git` no está instalado** (instalación nueva de NixOS):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **En caso contrario:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Define tu nombre de usuario

Crea el archivo `username.nix` con tu nombre de usuario:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> Este archivo está en el gitignore — un `git pull` nunca lo sobrescribirá.

### 3. Sustituye hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Crea tus configuraciones locales

**Nunca edites `configuration.nix` ni `home/common.nix` directamente** — se sobrescriben con `git pull`.
En su lugar, crea tus archivos locales de personalización (todos en el gitignore):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

Edita `hosts/roudix/local.nix` para que coincida con tu hardware:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "mangowc", "umbriel", "gnome" o "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" o "intel"
  hardware.myCpu      = "intel";              # "intel" o "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # kernel de xddxdd — se usa cuando hardware.myGpu != "nvidia"
  hardware.myKernelChaotic = "cachyos";            # kernel de Chaotic-Nyx — solo se usa cuando hardware.myGpu == "nvidia"
  roudix.boot.bootloader = "limine";          # "limine" o "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" o []
  roudix.zen.enable   = false;                # ponlo en true para instalar también Zen Browser (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub", "openrgb" o "none" — ver más abajo
  roudix.mesa.useGit  = false;                # true = mesa-git (experimental, la compilación puede fallar), false = nixpkgs estable
  roudix.matrixClient = "none";               # "element", "cinny" o "none"
  roudix.discord      = "vencord";            # "vencord", "vanilla" o "none"
  roudix.editor       = "zed";                # "zed", "vscode", "neovim" o "none"

  # ── Aplicaciones de gaming (todas en true por defecto — desactiva las que no quieras) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── Integración con compositor desnudo (solo niri/hyprland/mangowc/umbriel) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" o "kde" — llavero + pila xdg-desktop-portal; sin efecto en sesiones gnome/kde

  # ── Configuración regional / Zona horaria ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # ver https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # debe coincidir con time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # configuración regional del sistema
  console.keyMap                  = "us";              # distribución de teclado de la consola — solo TTY, antes de que arranque la sesión gráfica

  # ── Distribución de teclado gráfica (Wayland) — independiente de console.keyMap ─
  # Sin efecto en GNOME/KDE, que gestionan su propia distribución mediante su demonio de ajustes.
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl", "nodeadkeys", "bepo", "dvorak", "colemak", "" (ninguna)
}
```

**Opciones de controlador RGB:**

| Valor | Descripción |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — configuración completa de Corsair (iCUE Link, Commander...) |
| `openrgb` | OpenRGB — marcas variadas (Razer, ASUS, MSI...) |
| `none` | Sin gestión de RGB |

**RGB de la RAM (solo OpenLinkHub):**

Si seleccionaste `openlinkhub`, también puedes activar el control RGB de tu RAM Corsair DDR4/DDR5. Añade estas líneas a `hosts/roudix/local.nix`:

```nix
roudix.memory.enable = true;                  # activar el RGB de la RAM mediante SMBus
roudix.memory.type   = "ddr5";                # "ddr4" o "ddr5"
roudix.memory.smBus  = "i2c-9";              # búscalo con: sudo i2cdetect -l (busca "SMBus")
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # búscalo con: sudo dmidecode -t memory | grep 'Part Number'
```

Para encontrar los valores correctos antes de configurarlos:

```bash
# Instala las herramientas necesarias si no están disponibles (instalación nueva de NixOS)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# Busca tu SMBus (una línea con "SMBus", "i801", "piix4" o "nforce")
sudo i2cdetect -l

# Busca el número de pieza de tu RAM
sudo dmidecode -t memory | grep 'Part Number'
```

> **Nota:** `roudix.memory.enable` aplica automáticamente `acpi_enforce_resources=lax` como parámetro del kernel y pone en la lista negra `spd5118` (DDR5) o `ee1004` (DDR4) para liberar el SMBus. El `config.json` de OpenLinkHub se parchea automáticamente al activarse.

**Valores de zona horaria habituales:**

| Zona horaria | Región |
|----------|--------|
| `Europe/Brussels` | Bélgica |
| `Europe/Paris` | Francia |
| `Europe/London` | Reino Unido |
| `Europe/Berlin` | Alemania |
| `Europe/Amsterdam` | Países Bajos |
| `America/New_York` | EE. UU. (Este) |
| `America/Los_Angeles` | EE. UU. (Oeste) |
| `Asia/Tokyo` | Japón |
| `UTC` | Universal |

**Valores de configuración regional habituales:**

| Configuración regional | Idioma |
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

**Valores de mapa de teclado de consola habituales:**

| Mapa de teclado | Distribución |
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

> **Nota:** `environment.sessionVariables.TZ` debe coincidir siempre con `time.timeZone` — ambos controlan la zona horaria, uno a nivel de sistema y otro a nivel de sesión.

Edita `home/local.nix` para tus personalizaciones de home-manager (paquetes extra, dotfiles, alias, fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> Consulta `home/local.nix.example` para ver todas las opciones de personalización disponibles, incluida la personalización de fastfetch.

### 5. Configura el kernel

Roudix usa **dos proveedores de kernel distintos** según tu GPU:

- **`hardware.myGpu != "nvidia"`** (AMD o Intel) → kernel de [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), que se elige con `hardware.myKernel`. Sin módulo Nvidia de que preocuparse, así que está disponible el conjunto completo de 32 variantes.
- **`hardware.myGpu == "nvidia"`** → kernel de **Chaotic-Nyx**, que se elige con `hardware.myKernelChaotic`. Es necesario para obtener **`nvidia_cachyos`**, un driver Nvidia precompilado que coincide con su kernel — de lo contrario el módulo de kernel de Nvidia se recompila localmente con cada actualización del kernel. Aquí el conjunto de variantes es más reducido a propósito (Chaotic-Nyx no publica tantas variantes, y las variantes `-lto` son más propensas a romper módulos externos como el de Nvidia).

Ambas opciones aceptan también unos cuantos **kernels simples de nixpkgs**, totalmente fuera de su overlay respectivo de CachyOS — útiles si solo quieres un kernel estándar sin parches de CachyOS: `zen`, `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing`, `xanmod-lts`, `xanmod-latest`. En la ruta Nvidia se saltan la caché de `nvidia_cachyos` y recompilan el módulo Nvidia localmente (ver `nvidia.nix`).

**Kernels de nixpkgs más recientes — `hardware.myKernelSource`:** estos kernels de nixpkgs siguen por defecto el input principal `nixpkgs` (nixos-unstable). Pon `hardware.myKernelSource` en `"master"` o `"staging-next"` para tomar **solo el kernel** (y los módulos externos compilados contra él, p. ej. Nvidia) de esa rama de NixOS/nixpkgs y recibir antes las actualizaciones del kernel — el resto del sistema no se toca. Valores: `"nixpkgs"` (por defecto), `"master"`, `"staging-next"`. Advertencias: es posible que ese kernel aún no esté en una caché binaria, así que espera una compilación local larga; `staging-next` además incluye cambios de toolchain en curso, por lo que es el más arriesgado de los tres. No tiene efecto en los kernels `cachyos-*` (se muestra un aviso). Tras configurarlo, ejecuta `nix flake lock` una vez para que se bloquee el nuevo input.

**Variantes de `hardware.myKernel` (xddxdd — solo AMD/Intel):**

| Variante | Descripción |
|---------|-------------|
| `zen` | `linuxPackages_zen` simple (nixpkgs) — fuera del overlay de xddxdd |
| `nixpkgs-lts` | Kernel LTS por defecto de nixpkgs, sin modificar — fuera del overlay de xddxdd |
| `nixpkgs-latest` | Último kernel mainline de nixpkgs, sin modificar — fuera del overlay de xddxdd |
| `nixpkgs-testing` | `linux_testing` de nixpkgs sin modificar (RC/mainline) — fuera del overlay de xddxdd |
| `xanmod-lts` | Rama XanMod LTS (`linuxPackages_xanmod`, nixpkgs) — governor de rendimiento, preemption perezosa, BBRv3 |
| `xanmod-latest` | Rama principal de XanMod (`linuxPackages_xanmod_latest`, nixpkgs) |
| `cachyos-latest` | Último kernel CachyOS estándar |
| `cachyos-latest-v2` | optimizado para x86_64-v2 |
| `cachyos-latest-v3` | optimizado para x86_64-v3 (recomendado para CPU modernas) |
| `cachyos-latest-v4` | optimizado para x86_64-v4 (AVX-512, solo CPU muy recientes) |
| `cachyos-latest-zen4` | optimizado para AMD Zen 4 |
| `cachyos-latest-lto` | Compilación LTO para mejor rendimiento |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (máximo rendimiento, solo CPU modernas) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | Kernel CachyOS de soporte a largo plazo |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + optimizado para x86_64-v3 |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (estable + rendimiento) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | Planificador BMQ |
| `cachyos-bmq-lto` | Planificador BMQ + LTO |
| `cachyos-bore` | Planificador BORE (mejor interactividad) |
| `cachyos-bore-lto` | Planificador BORE + LTO |
| `cachyos-deckify` | Optimizado para Steam Deck |
| `cachyos-deckify-lto` | Optimizado para Steam Deck + LTO |
| `cachyos-eevdf` | Planificador EEVDF |
| `cachyos-eevdf-lto` | Planificador EEVDF + LTO |
| `cachyos-hardened` | Kernel reforzado en seguridad |
| `cachyos-hardened-lto` | Reforzado en seguridad + LTO |
| `cachyos-rc` | Release candidate — lo último de lo último, potencialmente inestable |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | Tiempo real + planificador BORE |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | Optimizado para servidor (sin ajustes de escritorio) |
| `cachyos-server-lto` | Optimizado para servidor + LTO |

**Variantes de `hardware.myKernelChaotic` (Chaotic-Nyx — solo Nvidia):**

| Variante | Descripción |
|---------|-------------|
| `cachyos` | Por defecto — LTO + planificador BORE, incluye el `nvidia_cachyos` correspondiente |
| `cachyos-lts` | Soporte a largo plazo |
| `cachyos-server` | Optimizado para servidor (sin ajustes de escritorio) |
| `cachyos-hardened` | Reforzado en seguridad |
| `zen` | `linuxPackages_zen` simple (nixpkgs) — módulo Nvidia recompilado localmente |
| `nixpkgs-lts` | LTS de nixpkgs sin modificar — módulo Nvidia recompilado localmente |
| `nixpkgs-latest` | Último mainline de nixpkgs sin modificar — módulo Nvidia recompilado localmente |
| `nixpkgs-testing` | `linux_testing` de nixpkgs sin modificar (RC) — módulo Nvidia recompilado localmente |
| `xanmod-lts` | XanMod LTS (nixpkgs) — módulo Nvidia recompilado localmente |
| `xanmod-latest` | Rama principal de XanMod (nixpkgs) — módulo Nvidia recompilado localmente |

> **Nota sobre NVIDIA:** solo se admiten GTX 20xx / serie RTX y posteriores. Los drivers abiertos están activados por defecto para RTX 20xx+ (Turing+). No se admiten las GTX 10xx/16xx.

> **Nota sobre el tema Spicetify Comfy:** tras tu primera compilación, copia a mano el color.ini:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> Después ejecuta `rebuild` para aplicarlo.

### 6. Actualiza el montaje del disco

En `hosts/roudix/local.nix`, añade un bloque `lib.mkForce` con tu propio UUID (o sáltalo si no tienes un disco secundario):

```bash
lsblk -f  # busca el UUID de tu disco
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Configura el arranque múltiple de Limine (opcional)

> Salta este paso si solo tienes NixOS en tu equipo.

Limine puede arrancar otros sistemas operativos en discos distintos. `boot.local.nix` controla las entradas adicionales — está en el gitignore y `git pull` nunca lo sobrescribe.

**Nunca edites `modules/system/boot/boot.nix` directamente** — se sobrescribe con `git pull`.

#### Si usaste el instalador automático

El instalador detectó tus otros sistemas operativos automáticamente desde la NVRAM EFI (`efibootmgr`) y escribió `boot.local.nix` por ti — no hace falta ninguna acción manual. Puedes revisar el resultado:

```bash
cat modules/system/boot/boot.local.nix
```

#### Si instalas manualmente

**Obtén tus PARTUUID:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Busca particiones con el tipo de sistema de archivos `vfat` y la etiqueta `EFI system partition` — esas son tus ESP.

**Edita `modules/system/boot/boot.local.nix`** y añade tus entradas:

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

> **Consejo:** la ruta EFI que va tras el UUID depende del gestor de arranque del otro sistema operativo. Rutas habituales:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - Cualquier distro (alternativa): `/EFI/BOOT/BOOTX64.EFI`

Si no tienes otro sistema operativo que añadir, deja `extraEntries` vacío:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` está en `.gitignore` — un `git pull` nunca lo sobrescribirá.

### 8. Actualiza la configuración de git

`modules/home/git.nix` está en el gitignore (como `local.nix`) — copia la plantilla versionada y rellena tu identidad:

```bash
cp modules/home/git.nix.example modules/home/git.nix
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

- `init.defaultBranch = "main"` — nombre que se usa para la primera rama cuando haces `git init` en un repositorio nuevo (no afecta a la rama de este repositorio, solo a las que crees tú).
- `pull.rebase = false` — qué hace `git pull` cuando tu rama local y la remota han divergido: `false` fusiona (crea un commit de merge, el comportamiento por defecto y más simple), `true` reaplica tus commits locales sobre el remoto (historial lineal, pero reescribe tus commits — evítalo si no te sientes cómodo con los conflictos de rebase). `false` es la opción más segura para un repositorio de configuración personal.

> Si falta el archivo, `common.nix` simplemente lo omite — Home Manager no configurará git hasta que lo copies, pero nada se rompe.

### 9. Activa/desactiva módulos opcionales

En `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + actualización automática diaria
roudix.fstrim.enable         = true;   # recomendado para SSD/NVMe
roudix.virtualization.enable = false;  # actívalo para QEMU/KVM
roudix.vmGuest.enable        = true;   # actívalo solo dentro de una VM
roudix.hosts.gtaFix.enable   = true;   # bloquea la telemetría de BattlEye (arreglo de GTA)
roudix.autoupdate.enable     = true;   # git pull automático + nh os boot al haber cambios
roudix.zen.enable            = false;  # instala Zen Browser (desactivado por defecto)
roudix.mesa.useGit           = false;  # true = mesa-git (experimental, de vanguardia — la compilación puede fallar), false = nixpkgs estable
roudix.boot.bootloader       = "limine";  # "limine" o "systemd-boot"
roudix.matrixClient          = "none"; # "element", "cinny" o "none"
```

> **Recordatorio:** si pones `roudix.autoupdate.enable = true`, configura también el intervalo:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. Personaliza fastfetch (opcional)

Por defecto Roudix muestra su logo ASCII en fastfetch. Puedes sustituirlo en `home/local.nix` sin tocar git:

```nix
# Usa una imagen personalizada (requiere el terminal kitty)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Usa un archivo ASCII personalizado
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Sustituye toda la configuración de fastfetch (reemplaza todo)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` sobrescribe toda la configuración por defecto de Roudix. Sin él, tus claves se combinan con las de por defecto.
> Consulta `home/local.nix.example` para ver más ejemplos.

### 11. Compila

> **Si flakes y nix-command aún no están activados** (instalación nueva de NixOS):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **En caso contrario:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

Una vez compilado, usa los alias de fish para todas las operaciones futuras.

> Los tres archivos `local.nix` y `boot.local.nix` están en `.gitignore` — un `git pull` nunca los sobrescribirá.

[English](desktop.md) · [Français](desktop.fr.md) · **Español** · [Português (Brasil)](desktop.pt_BR.md) · [Русский](desktop.ru.md) · [简体中文](desktop.zh_CN.md) · [हिन्दी](desktop.hi.md) · [العربية](desktop.ar.md)

# Entornos de escritorio

Cambia de escritorio en cualquier momento con `roudix-switch <de>` o con la interfaz gráfica **Roudix Customizer** (paquete `roudix-switcher`), sin necesidad de un host aparte. La interfaz ha ido más allá del simple cambio de escritorio: ahora cubre Escritorio, Gaming (interruptores por aplicación), Editor, Terminal, Navegador, Shell de inicio de sesión, Gestor de archivos, Cliente de chat (Discord/Matrix) e Integración (pila keyring/portal) en una sola aplicación.

| Valor | Escritorio | Notas |
|-------|------------|-------|
| `niri` | Niri + (Noctalia, DMS) | Predeterminado — Wayland con mosaico desplazable (scrollable tiling) |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Wayland con mosaico dinámico — se lanza mediante UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | Compositor Wayland |
| `umbriel` | Umbriel + Noctalia | Mosaico desplazable — el compositor nativo propio de Noctalia, solo Noctalia (sin cambio de shell) |
| `gnome` | GNOME | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |
| `cinnamon` | Cinnamon | Sesión X11 + LightDM — escritorio clásico, adecuado para hardware antiguo (GNOME 49 es solo Wayland) |
| `cosmic` | COSMIC | Escritorio Wayland de System76 (cosmic-comp), cosmic-greeter |

Para cambiarlo de forma permanente, edita `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome", "kde", "cinnamon" o "cosmic"
```

O usa la función de fish: edita la configuración y reconstruye en un solo paso:

```fish
roudix-switch kde
```

> **Nota:** `roudix-switch` usa `nh os boot`: los cambios se aplican en el próximo reinicio.

---

## Shells gráficos (solo Niri, Hyprland y MangoWC)

En los compositores Wayland (Niri, Hyprland, MangoWC) puedes cambiar la pila de shell/barra de forma independiente del compositor. En Hyprland, **un único árbol de configuración** (`dotfiles/hyprland/`) contiene los atajos comunes y elige el shell a partir de `roudix.desktop.shell`.

| Valor | Shell | Hyprland |
|-------|-------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | Dux Shell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**Nota:** Caelestia solo está disponible en Hyprland. El shell se inyecta en la sesión mediante `ROUDIX_HYPR_SHELL`, así que no hay árboles `hyprland-dms/` ni `hyprland-caelestia/` separados que mantener sincronizados.

### Inicio automático del shell

El arranque depende del shell y del compositor elegidos, con exactamente un mecanismo de inicio por shell:

- **Hyprland + Noctalia:** `noctalia` desde el hook Lua `hyprland.start`.
- **Hyprland + Caelestia:** `caelestia-shell` desde el hook Lua `hyprland.start`.
- **Hyprland + DMS:** servicio de usuario systemd de DMS; Hyprland exporta el entorno de la sesión a systemd al arrancar.
- **MangoWC + Noctalia:** `noctalia` desde `autostart_sh` de MangoWC.
- **MangoWC + DMS:** servicio de usuario systemd de DMS, activado a través de `mango-session.target`; por tanto, MangoWC no ejecuta `dms run`.

DMS no debe iniciarse a la vez por systemd y por el compositor: su documentación oficial recomienda eliminar `dms run` cuando se usa el servicio systemd.

Para cambiarlo, edita `hosts/roudix/local.nix`:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" o "caelestia"
```

Después reconstruye:

```fish
rebuild
```

O usa la función de fish (disponible solo en Niri, Hyprland y MangoWC): edita la configuración y reconstruye en un solo paso:

```fish
roudix-shell-switch dms
```

> **Nota:** `roudix-shell-switch` usa `nh os boot`: los cambios se aplican en el próximo reinicio.

---

## nixpkgs o última versión (flake)

Niri, MangoWC y Umbriel provienen siempre de su propio flake. Para el shell (y el greeter que lo acompaña), Roudix usa por defecto la versión de **nixpkgs**. Para obtener la última versión, compilada desde el flake del propio proyecto, actívala por componente en `local.nix`, o desde `roudix-switcher` / el instalador, donde el interruptor solo aparece para el shell que hayas seleccionado:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # Dux Shell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (el greeter de DMS lo sigue)
```

Hyprland no tiene versión flake en Roudix: siempre proviene de nixpkgs.

> **Ojo:** las configuraciones de Roudix se escriben **primero para las versiones flake (latest)**. En las versiones de nixpkgs, un error de configuración que diga que una opción, un ajuste o una clave de configuración *no existe* es **normal**: se añadió después de la versión que incluye nixpkgs. Espera a que nixpkgs se ponga al día, o pon el componente en `true`.

> Si un módulo flake no expone una opción `package` (posible con DMS, MangoWC y el greeter de DMS), no se puede aplicar la versión de nixpkgs: Roudix se queda con la versión flake y muestra una advertencia durante la compilación.

---

## Personalizaciones del compositor

Niri y Umbriel se configuran de forma nativa en Nix (`programs.niri.settings` / `programs.umbriel.settings`): son attrsets reales y tipados, no un archivo de texto generado. Eso significa que las personalizaciones son simplemente Nix: añade una clave que aún no existe y se fusiona automáticamente; si tocas una clave que el repositorio ya define (misma salida, mismo atajo) necesitas `lib.mkForce`, o Nix se negará a compilar con un error de «conflicting definitions».

MangoWC y Hyprland siguen basados en texto (ver más abajo).

Puedes poner las personalizaciones directamente en `modules/home/local.nix`, pero si personalizas mucho un compositor, un archivo dedicado mantiene todo más ordenado: `modules/home/local.nix` importa automáticamente `modules/home/niri-custom.nix`, `modules/home/umbriel-custom.nix` y `modules/home/mango-custom.nix` si existen (copia el archivo `*.example` correspondiente para empezar; están en gitignore igual que `local.nix`).

**Niri**

```nix
# Cambiar un monitor que niri-flake ya define (necesita lib.mkForce)
# — ejecuta `niri msg outputs` en sesión para obtener el nombre real del conector
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# Reasignar un atajo que el repositorio ya define (necesita lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# Añadir un atajo que aún no existe (no hace falta mkForce)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# Añadir una regla de ventana — las listas se CONCATENAN entre archivos, así que esto
# se suma a las reglas del repositorio, no hace falta mkForce
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# Cambiar una salida (necesita lib.mkForce — ejecuta `umbriel outputs` para el nombre real)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# Reasignar un atajo que el repositorio ya define
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# Añadir un atajo que aún no existe
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# Añadir una regla de ventana
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** sigue cargando, al final de su configuración, un archivo de personalización personal generado por home-manager — **nunca modificado por `git pull`** — porque en la práctica no tiene un esquema Nix tipado:

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

Como es un único bloque de texto grande y no unas pocas líneas de Nix, encaja mejor en su propio archivo: ver `modules/home/mango-custom.nix.example`.

**Hyprland usa ahora la configuración Lua modular de `dotfiles/hyprland/`.** El punto de entrada es `dotfiles/hyprland/hyprland.lua`, que carga los módulos de `config/` para monitores, layouts, animaciones, atajos, reglas de ventana e integraciones de shell. Nix copia este árbol tal cual a `~/.config/hypr/`.

La configuración actual está pensada para Hyprland 0.55+ y usa los layouts nativos `dwindle`, `master` y `scrolling`. El módulo Nix genera un pequeño cargador `config/nix-plugins.lua` antes del punto de entrada; Roudix incluye `borders-plus-plus`. El bloque `dynamic_cursors` sigue siendo opcional y solo se aplica cuando ese plugin está presente.

### Personalizar Hyprland

Los valores específicos de cada máquina (las salidas `DP-1`/`DP-3`, el monitor principal, las aplicaciones predeterminadas, el teclado, etc.) están en `dotfiles/hyprland/config/`. Edítalos directamente si mantienes tu configuración de Hyprland en el repositorio de Roudix.

Para personalizaciones personales sin modificar archivos versionados, usa `modules/home/local.nix` con `xdg.configFile."hypr/..."` y `lib.mkForce`.

> Tras cambiar la configuración Lua, ejecuta `rebuild`. Puede ser necesario reiniciar la sesión para los cambios de shell o de entorno.

> Consulta `modules/home/niri-custom.nix.example`, `modules/home/umbriel-custom.nix.example`, `modules/home/mango-custom.nix.example` y `modules/home/local.nix.example` para ver la lista completa de ejemplos.

---

## Personalizaciones de GNOME

Cuando usas `roudix.desktop.type = "gnome"`, la gestión de extensiones va en `hosts/roudix/local.nix` y las personalizaciones de apariencia van en `modules/home/local.nix`.

**Añadir extensiones además de las predeterminadas** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**Desactivar una extensión predeterminada por UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**Combinar ambas — p. ej. cambiar ArcMenu por otro lanzador** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**Cambiar el aspecto a mano (recomendado)**

Roudix entrega el aspecto de GNOME (fondo de pantalla, tema oscuro, iconos, cursor, ajustes de extensiones) como *valores predeterminados*. Cambia lo que quieras en Ajustes, Retoques o en las preferencias de una extensión y será tuyo: una reconstrucción nunca lo revierte. Las actualizaciones de Roudix solo modifican los valores predeterminados de los ajustes que no hayas tocado.

**Forzar un valor desde tu configuración** (`modules/home/local.nix`)

Si prefieres fijar un valor de forma declarativa, hazlo mediante home-manager. A diferencia de la vía manual anterior, se vuelve a aplicar en **cada** reconstrucción y se impone a lo que cambies en la interfaz:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # o "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
No hace falta `lib.mkForce`: home-manager ya no define estas claves.

**Recuperar los valores predeterminados de Roudix** para un ajuste (o una sección completa)
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> Consulta `hosts/roudix/local.nix.example` y `modules/home/local.nix.example` para ver todas las opciones de personalización de GNOME disponibles.

---

## Personalizaciones de KDE Plasma

Cuando usas `roudix.desktop.type = "kde"`:

Roudix aplica su aspecto de KDE **una sola vez**, nunca en cada reconstrucción, así que todo lo que cambies en Preferencias del sistema se mantiene:

- **Tema oscuro, iconos, cursor**: se aplican solo en el primer inicio de sesión, protegidos por `~/.local/state/roudix/kde-theme-seeded`. Para recuperar a propósito el aspecto de Roudix: `rm ~/.local/state/roudix/kde-theme-seeded` y cierra/abre sesión.
- **NumLock al arrancar, fondo de la pantalla de bloqueo**: valores predeterminados simples de KConfig en `/etc/xdg`, que quedan por debajo de tu `~/.config` y nunca lo sobrescriben.
- **Fondo de pantalla y panel**: los aplica plasma-manager en el primer inicio de sesión y solo se vuelven a ejecutar si Roudix cambia su definición en una actualización.

**Fijar valores desde tu configuración** (`modules/home/local.nix`)

Todo lo que definas mediante plasma-manager se vuelve a aplicar en **cada** reconstrucción, así que úsalo solo para lo que quieras que sea declarativo:

**Fondo de pantalla**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Esquema de colores / iconos / cursor**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**Barra de tareas / Paneles**
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

> `lib.mkForce` solo es necesario para `wallpaper` y `panels`, que siguen definidos en `modules/home/desktop/kde/default.nix`.

## Valores predeterminados de Cinnamon

Cinnamon incluye por defecto el fondo Roudix Kitsune, en el escritorio y en la pantalla de inicio de sesión de LightDM, usa el logo de Roudix como icono del menú y fija en el panel el navegador predeterminado (el primero de `roudix.browsers`), Roudix Store y Ajustes. Las aplicaciones GTK4 / libadwaita siguen el tema oscuro. Son valores predeterminados: solo se aplican a lo que el usuario no ha cambiado. Los elementos fijados del panel (navegador, Nemo, Roudix Store, Ajustes) y el icono del menú son valores predeterminados de applets, entregados como copias parcheadas de dos applets: no se reconstruye nada de Cinnamon.

La pantalla de inicio de sesión (slick-greeter) no tiene aplicación de ajustes. Cambia su fondo con:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # no hace falta reconstruir
roudix-lightdm-wallpaper --reset                    # volver a Kitsune
```

Sustituye las aplicaciones fijadas en `hosts/roudix/local.nix`:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## Valores predeterminados de COSMIC

COSMIC incluye por defecto el fondo Roudix Kitsune y la distribución de teclado de `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions`. El dock fija el navegador o navegadores elegidos en Roudix (y Zen si está activado), COSMIC Files, tu terminal, Roudix Store y COSMIC Settings — la misma idea que el dash de GNOME y el gestor de tareas de Plasma. En la biblioteca de aplicaciones, todas las aplicaciones de Roudix (Store, Customizer, Kernel Switcher, Scheduler, Hardware Sync, Config, Welcome) se agrupan en una carpeta **Roudix** y ya no aparecen en Sistema / Utilidades. COSMIC Store no se instala: Roudix Store la sustituye.

Son valores predeterminados, entregados como archivos cosmic-config de todo el sistema: solo se aplican a lo que el usuario no ha cambiado, y una reconstrucción nunca revierte una elección hecha en COSMIC Settings.

Las aplicaciones y el panel propios de COSMIC usan por defecto el esquema de colores de Roudix (`assets/cosmic/`, generado a partir de `assets/palette/Roudix.json`, instalado como valores predeterminados del sistema por `modules/system/desktop/cosmic.nix`, sin Home Manager). Elegir otro tema o acento en Ajustes > Apariencia lo sobrescribe, y una reconstrucción nunca toca tu elección. «Aplicar el tema actual a las aplicaciones de GNOME» (Ajustes > Escritorio > Apariencia > Iconos y tema de toolkits) está activado por defecto: el propio COSMIC exporta su tema, de modo que las aplicaciones GTK (navegadores, las aplicaciones de Roudix...) reciben los colores de Roudix sobre adw-gtk3, sin ningún CSS escrito por Roudix. Los iconos son Papirus-Roudix (ver `roudix.iconTheme`), y tu terminal recibe su esquema de colores de Roudix como en cualquier otro escritorio.

`system76-scheduler`, que el módulo COSMIC de nixpkgs activa, está desactivado por defecto porque Roudix tiene su propia pila de scheduler (SCX). Para conservarlo:

```nix
services.system76-scheduler.enable = true;
```

Para cambiar las aplicaciones fijadas, basta con fijar / desfijar desde el dock: tu elección prevalece sobre la predeterminada.

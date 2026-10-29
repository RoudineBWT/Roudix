[English](features.md) · [Français](features.fr.md) · **Español** · [Português (Brasil)](features.pt_BR.md) · [Русский](features.ru.md) · [简体中文](features.zh_CN.md) · [हिन्दी](features.hi.md) · [العربية](features.ar.md)

# Funcionalidades

## Kernel y rendimiento

- Kernel CachyOS con NTSync activado (módulo `ntsync`)
- Dos proveedores de kernel, elegidos automáticamente según `hardware.myGpu`:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 36 variantes (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 variantes (`hardware.myKernelChaotic`) — incluye `nvidia_cachyos`, un driver precompilado a juego con su kernel, de modo que el módulo de Nvidia no se recompila localmente en cada actualización del kernel
- También se pueden elegir kernels "planos" de nixpkgs en ambos proveedores, completamente al margen del overlay de CachyOS — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline), `xanmod-lts` / `xanmod-latest` (XanMod). En Nvidia, estos recurren a un módulo de Nvidia recompilado localmente (sin la caché de `nvidia_cachyos`)
- `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) toma únicamente esos kernels de nixpkgs desde un nixpkgs más reciente para adelantar las actualizaciones del kernel, sin tocar el resto del sistema
- ZRAM activado (100 % de la RAM, zstd, swappiness 150)
- zswap desactivado
- Microcódigo de la CPU configurado automáticamente (Intel o AMD)
- Intel: `split_lock_detect=off` se aplica automáticamente
- ananicy-cpp activado (demonio de prioridad de procesos, reglas de CachyOS)
- Soporte del scheduler SCX — cambio en caliente, sin reiniciar (bpfland, lavd, flash, p2dq, rusty…) mediante la interfaz Kernel Switcher — una sola petición de contraseña a través de `scx-switch` se encarga de detener/iniciar ananicy-cpp y de cambiar de scheduler de una vez — **nota:** SCX no persiste tras un reinicio; después de reiniciar, ananicy-cpp arranca de nuevo automáticamente y el scheduler debe volver a aplicarse desde la interfaz Kernel Switcher

## Arranque

- Bootloader Limine (por defecto) — moderno, rápido, con soporte multidisco — o systemd-boot, seleccionable mediante `roudix.boot.bootloader`
- Renombrado automático de la entrada UEFI a "Roudix"
- Menú de arranque multi-OS (Windows, otras distros Linux en ESP separadas)
- La etiqueta de arranque muestra el nombre Roudix + la versión de la release de NixOS

## Gaming

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, sesión desactivada por defecto)
- Variables de entorno de captura de OBS preconfiguradas (`OBS_VKCAPTURE` mediante `environment.sessionVariables`)
- Overlay MangoHud horizontal personalizado (etiqueta `Powered By Roudix`)
- Soporte de mandos (Steam Hardware + game-devices-udev-rules)
- Soporte de 32 bits para Wine/Steam
- Wrapper `game-performance` — cambia a un perfil de rendimiento `tuned-adm` dedicado mientras dura una partida, controlado mediante un cgroup `systemd-run --user --scope` (así sobrevive a que Steam haga re-fork o se desvincule) y se restaura al salir (uso: `game-performance %command%` en las opciones de lanzamiento de Steam) — GameMode está desactivado a propósito (incompatible aquí con ananicy-cpp)
- `ffmpegthumbnailer` disponible en todo el sistema (miniaturas de vídeo en los gestores de archivos)
- `protonup-qt` en KDE, `protonplus` en los demás entornos de escritorio
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft, o Modrinth App como alternativa — `roudix.gaming.apps.modrinth.enable`) y Vintage Story (mediante roudix-caches)
- Cada app de gaming se puede activar/desactivar individualmente mediante `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (todas `true` por defecto)
- Cliente de Steam modificado [Millennium](https://github.com/SteamClientHomebrew/Millennium) opcional (temas + plugins) — desactivado por defecto, se activa con `roudix.gaming.steam.millennium.enable = true` (o desde el instalador). Mod no oficial; el ajuste de sandbox de `game-performance` y las herramientas de compatibilidad de Proton siguen funcionando, y volver a poner `false` restaura el Steam estándar
- Modo Gaming opcional al estilo consola: `roudix.gaming.gamescopeSession.enable` añade una sesión "Steam (Gaming Mode)" en la pantalla de inicio de sesión (Steam Big Picture dentro de gamescope, VRR/HDR/MangoApp, frecuencia de refresco detectada al arrancar). "Cambiar al escritorio" en Steam abre tu escritorio, y la app "Return to Gaming Mode" vuelve al juego sin pasar por la pantalla de inicio de sesión. Basado en GLF-OS; compatible con niri, umbriel, GNOME, KDE, Hyprland y MangoWC
- Decky Loader opcional (plugins de Steam) mediante `roudix.gaming.gamescopeSession.decky.enable`, obtenido del flake input de Jovian-NixOS (`nix flake update jovian` para actualizarlo, sin sha que mantener a mano); no hay caché binaria, así que se compila localmente en la primera reconstrucción

## Escritorio (Niri)

- Niri, compositor Wayland de tiling con scroll — proporcionado mediante [niri-flake](https://github.com/epireyn/niri-flake) (epireyn), usando `niri-unstable` por defecto, con la caché binaria `niri-epireyn.cachix.org` preconfigurada
- La configuración es nativa de Nix (`programs.niri.settings`), dividida por temas (general, animations, input, layout, outputs, binds, rules) y validada en tiempo de compilación con `niri validate` — una configuración rota hace fallar la compilación en lugar de fallar el compositor al iniciar sesión
- La sincronización de tema en vivo de Noctalia/DMS (colores generados por matugen/DMS, alt-tab, blur) se conserva añadiendo un `include` a la configuración generada en lugar de incrustarla de forma estática
- Shell moderno Noctalia (v5)
- xdg-desktop-portal-gnome + gtk (portales de screencast y escritorio remoto configurados)
- Cursor Bibata Modern Ice (24 px)
- adw-gtk3 + iconos Papirus + Papirus Folders
- Element Desktop con gnome-libsecret / kwallet6 (detectado automáticamente según el entorno de escritorio)
- Agente Polkit de GNOME
- DMS Greeter (greetd)

## Escritorio (MangoWC)

- MangoWC, compositor Wayland
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- Cursor Bibata Modern Ice (24 px)
- Agente Polkit de GNOME
- Gestor de inicio de sesión Ly
- adw-gtk3 + iconos Papirus + Papirus Folders
- Animación de apertura con zoom + curvas bezier oficiales
- VRR + tearing activados en el monitor gaming (DP-1 1440p@240)
- Capturas de pantalla con grim + slurp + satty (anotación) — 3 atajos de teclado
- Selector de ventanas con rofi (Alt+Tab)
- Variables de entorno de XDG Desktop Portal preconfiguradas (captura de pantalla con Pipewire, OBS, Discord Go Live)
- force_tearing + idleinhibit_when_focus en todas las apps de gaming (Steam, Heroic, Minecraft, Lutris, Bottles)
- Opacidad de las ventanas sin foco (0.85)
- Hotarea overview (gesto del ratón en la esquina)
- Snap flotante + arrastrar de tile a tile
- Soporte de scratchpad: un pool genérico para cualquier ventana (mover/alternar/restaurar),
  más un scratchpad con nombre por app, opcional (`roudix.mangowc.scratchpadApps`), para
  Discord/Element/Telegram/Spotify — cada uno con su propia tecla de alternancia

## Escritorio (Umbriel)

- Umbriel, compositor Wayland de tiling con scroll — el compositor nativo propio de Noctalia, proporcionado mediante [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (solo con Noctalia, sin cambio de shell)
- La configuración es nativa de Nix (`programs.umbriel.settings`), dividida por temas (general, appearance, animation, input, layout, outputs, binds, rules) y validada en tiempo de compilación (`validateConfig = true`)
- La sincronización de tema en vivo de Noctalia (colores generados por matugen) se conserva gracias al mecanismo nativo `include.files` de Umbriel, sin instantánea estática de colores
- Cursor Bibata Modern Ice (24 px)
- adw-gtk3 + iconos Papirus + Papirus Folders
- Hot corners (overview al llevar el ratón a la esquina) y una vista general de workspaces (Mod+O)
- Soporte de scratchpad (mover/alternar/restaurar una ventana flotante bajo demanda)
- Ajustes de layout por workspace (p. ej. sin gap en el workspace de gaming)

## Escritorio (Hyprland)

- Hyprland, compositor Wayland de tiling dinámico lanzado mediante UWSM
- Shell moderno Noctalia
- xdg-desktop-portal-hyprland + portal gtk
- Cursor Bibata Modern Ice (24 px)
- Agente Polkit de GNOME (iniciado mediante un servicio de usuario de systemd)
- Demonio de fondos de pantalla awww
- Capturas de pantalla con grim + slurp + satty (anotación) — 3 atajos de teclado

## Escritorio (GNOME)

- GNOME (sigue la rama nixos-unstable)
- Conjunto curado de extensiones (blur, tiling, vitals, arcmenu...) — activadas mediante dconf
- ArcMenu con el logo de Roudix como icono del botón de menú
- Bloatware eliminado mediante `environment.gnome.excludePackages`
- Tema de iconos Papirus-Dark
- Tema GTK adw-gtk3-dark (modo oscuro por defecto)
- Cursor Bibata Modern Ice (24 px)
- Fondo de pantalla de Roudix (claro/oscuro según el tema del sistema)
- `color-scheme = prefer-dark` aplicado mediante dconf
- Ajustes de las extensiones (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) preconfigurados mediante `modules/home/desktop/gnome/_extensions.nix`
- Añade o quita extensiones sin editar los archivos principales mediante `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- Sobrescribe el fondo de pantalla, el tema, los iconos y el cursor en `modules/home/local.nix`

## Escritorio (KDE)

- KDE Plasma 6 con plasma-login-manager (Plasma 6.6+, nixpkgs unstable)
- KDE Connect activado
- xdg-desktop-portal-kde
- Tema de iconos Papirus-Dark
- Look & feel y esquema de colores Breeze Dark
- Fondo de pantalla Roudix Dark en la pantalla de inicio de sesión y en el escritorio
- Paquetes curados: partitionmanager, kcalc, digikam, vlc...
- Bloatware eliminado (Discover excluido)
- Sobrescribe el fondo de pantalla, los paneles y el tema de iconos en `modules/home/local.nix`

## Música

Elige uno mediante `roudix.musicPlayer` — `"spotify"` (por defecto), `"ytmdesktop"`,
`"sonora"` o `"none"`.

- `"spotify"` — Spotify parcheado con Spicetify. Tema local, "colorful" por
  defecto (o "comfy"), además de las extensiones de adblock y de ocultar podcasts — ver
  los interruptores más abajo.
- `"ytmdesktop"` — YouTube Music Desktop App (cliente de YouTube Music no oficial,
  basado en Electron).
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora), un cliente nativo
  (Rust/GPUI) para Spotify, YouTube Music, Apple Music, Deezer y
  Subsonic en una sola app. La opción `roudix.sonora.provider` elige el
  proveedor con el que arranca (`"youtube"` = YouTube Music). No esquiva las
  suscripciones: si un servicio requiere una, Sonora también.

## Apps comunes opcionales

GIMP, Inkscape, SongRec y EasyEffects (+ rnnoise-plugin) se incluyen por defecto, pero
cada uno se puede desactivar individualmente mediante `roudix.apps.<name>.enable` (`gimp`,
`inkscape`, `songrec`, `easyeffects`).

Signal y ZapZap (un cliente de escritorio de WhatsApp no oficial y de aspecto nativo)
no tienen una alternativa real entre la que elegir, así que son simples booleanos opt-in,
desactivados por defecto: `roudix.apps.signal.enable` y `roudix.apps.zapzap.enable`.

Fluxer, una alternativa a Discord que se puede autoalojar, es el mismo tipo de booleano
opt-in: `roudix.apps.fluxer.enable`. Todavía no está en nixpkgs, así que se
obtiene directamente del paquete precompilado `fluxer-desktop` del flake input
`nix-gaming-edge`. Es deliberadamente independiente de `roudix.discord`
y de `roudix.gaming.enable` — nada te impide querer Discord
y Fluxer a la vez, o Fluxer sin ningún setup de gaming.

También hay disponibles, opt-in (desactivados por defecto), un cliente de correo y un gestor
de contraseñas: `roudix.mailClient` — `"thunderbird"` (completo),
`"betterbird"` (un fork de Thunderbird afinado, obtenido del flake input
[betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) — todavía no
está en nixpkgs) o `"geary"` (cliente ligero de GNOME);
`roudix.passwordManager` —
`"bitwarden"` (sincronizado en la nube), `"keepassxc"` (bóveda local, sin conexión) o
`"protonpass"` (sincronizado en la nube, cuenta de Proton).

También disponible, opt-in (desactivado por defecto): un cliente de torrents mediante
`roudix.torrentClient` — `"qbittorrent"` (con muchas funciones, basado en Qt),
`"fragments"` (cliente mínimo de GNOME/libadwaita), `"deluge"` (basado en plugins) o
`"none"` (por defecto).

## Spicetify

- Tema: `roudix.spicetify.theme` — `"colorful"` (por defecto, sanoojes/spicetify-colorful) o `"comfy"` (tema Comfy incluido)
- Esquema de colores: `roudix.spicetify.colorScheme` — `null` (por defecto) usa el esquema por defecto del propio tema ("noctalia" para colorful, "Comfy" para comfy)
- Extensiones activables individualmente: `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (ambas `true` por defecto)
- App personalizada Marketplace: `roudix.spicetify.marketplace.enable` (`true` por defecto)

## Navegador

- Lista de navegadores configurable mediante la opción `roudix.browsers`
- Compatible con `brave`, `helium` (mediante x13-me/helium-nix, incluye el parche DRM — la reproducción con Widevine se configura automáticamente mediante `modules/home/apps/browser/helium-widevine.nix` cuando se selecciona `helium`), `vivaldi` (con códecs ffmpeg), `firefox`, `librewolf`, `chromium`, o `[]` para ninguno
- Zen Browser disponible por separado mediante `roudix.zen.enable = true` (desactivado por defecto); el canal se elige mediante `roudix.zen.variant` — `"twilight"` (por defecto) o `"beta"`

## Otros

- Discord seleccionable mediante `roudix.discord` — `"vencord"` (cliente parcheado, por defecto), `"vanilla"` (sin parchear) o `"none"` (no instalado)
- Telegram seleccionable mediante `roudix.telegram` — `"telegram"` (Telegram Desktop oficial), `"ayugram"` (fork no oficial: modo fantasma, anti-recall, historial local de mensajes...) o `"none"` (por defecto, no instalado)
- Editor de código seleccionable mediante `roudix.editor` — `"zed"` (por defecto), `"vscode"`, `"neovim"` o `"none"` (gestiona el tuyo, p. ej. AppImage/Flatpak)
- Distribución de teclado gráfica (Wayland) mediante `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB, p. ej. `"be"` / `"intl"`) — independiente de `console.keyMap`, que solo cubre el TTY antes de que arranque la sesión gráfica; no tiene efecto en GNOME/KDE, que gestionan su propia distribución
- Pila de keyring + xdg-desktop-portal para compositores "desnudos" (Niri, Hyprland, MangoWC, Umbriel) seleccionable mediante `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, por defecto) o `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent, y las apps de GNOME sustituidas por Kate / Gwenview / KDE Partition Manager / Dolphin; se mantienen adw-gtk3, nwg-look, qt6ct y gvfs para que las apps GTK conserven el tema); no tiene efecto en las sesiones de GNOME/KDE, que conservan su pila nativa
- `nix-ld` activado en todo el sistema — ejecuta binarios dinámicos sin parchear sin necesidad de un entorno FHS (preconfigurado con bibliotecas habituales: glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib y más)
- OBS Studio, activable individualmente mediante `roudix.contentCreation.obs.enable` (`true` por defecto), con plugins activables uno a uno mediante `roudix.contentCreation.obs.plugins.<name>.enable` (`vkcapture` + `pipewireAudioCapture` activados por defecto; también disponibles: `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- Editor de vídeo seleccionable mediante `roudix.contentCreation.videoEditor` — `"kdenlive"` (por defecto), `"davinci-resolve"` (gratuito), `"davinci-resolve-studio"` (de pago, requiere licencia), `"shotcut"` o `"none"`; DaVinci Resolve recibe automáticamente un ICD de OpenCL para AMD cuando `hardware.myGpu = "amd"`
- Cámara virtual `v4l2loopback` configurada automáticamente para OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`, `true` por defecto)
- Cliente de chat de Twitch Chatterino2, opt-in mediante `roudix.contentCreation.streaming.chatterino.enable`
- Todo el grupo de creación de contenido se puede activar/desactivar mediante `roudix.contentCreation.enable`
- GPU Screen Recorder
- Opción Mesa Git para AMD — activa un Mesa experimental/de última hora mediante `roudix.mesa.useGit = true` en `local.nix` (por defecto: Mesa estable de nixpkgs) — ⚠️ **experimental**, la compilación puede fallar según el estado de nixpkgs
- Parámetros del kernel para la estabilidad de las GPU AMD aplicados automáticamente (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — corrigen bloqueos aleatorios y problemas al despertar de la suspensión en RDNA2/RDNA3
- Controlador RGB seleccionable mediante `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander, actualizado automáticamente mediante CI), `openrgb` (multimarca: Razer, ASUS, MSI…) o `none`
- La interfaz web de OpenLinkHub está disponible en [http://127.0.0.1:27003](http://127.0.0.1:27003) una vez que el servicio está en marcha
- Control RGB de la RAM DDR4/DDR5 mediante OpenLinkHub — se activa con `roudix.memory.enable = true`, y se configuran `roudix.memory.type`, `roudix.memory.smBus` y `roudix.memory.sku` (ver `installation.es.md`)
- PipeWire con supresión de ruido estéreo rnnoise (nofail, compatibilidad de LADSPA_PATH 26.05/26.11)
- Flatpak con el remote de Flathub + actualización automática diaria (mediante nix-flatpak)
- Gestor de Bluetooth Blueman
- Cliente Matrix — configurable mediante `roudix.matrixClient` (`element`, `cinny` o `none`) — Element selecciona automáticamente kwallet6 en KDE y gnome-libsecret en el resto
- Reproductor de vídeo seleccionable mediante `roudix.videoPlayer` — `"vlc"` (el mayor soporte de formatos, por defecto), `"clapper"` (reproductor moderno en GTK4), `"mpv"` (+ yt-dlp, mínimo/streaming), `"celluloid"` (interfaz GTK para mpv) o `"none"`; se aplica en todos los escritorios (antes era Clapper fijo solo en los compositores desnudos, más un interruptor de mpv independiente del entorno de escritorio)
- Soporte de AppImage activado mediante `appimage.nix`
- Waydroid (contenedor de Android) — opcional, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (opcional, `roudix.virtualization.enable`)
- vm-curator (opcional, `roudix.virtualization.vmCurator.enable`) — alternativa TUI en Rust a virt-manager, controla QEMU directamente (sin libvirt), con aceleración 3D y soporte de GPU passthrough; se puede activar de forma independiente o junto con la pila de libvirt
- Módulo de optimizaciones para invitados de VM (portapapeles compartido, redimensionado automático, agente QEMU, Spice)

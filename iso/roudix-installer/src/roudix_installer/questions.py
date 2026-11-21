"""
The wizard's option questions, as data. No GTK, no terminal code here.

A front-end walks `build()` in order and, for each question, asks only what
`applicable()` / `multi_items()` let through. The TUI does exactly that (tui.py).
The GTK options page still builds its own widgets (pages/options.py): when an
option is added or a visibility rule changes, change *both* until the GTK page
is rebuilt on top of this file. The lists of choices themselves already come
from choices.py for both.

Visibility has two layers, same as the GTK page:
  * the host profile (host_profile.py): a profile that opts in to
    `# roudix-installer: only-listed` only gets the options its
    local.nix.example lists — `Q.keys` / `Item.keys` are those nix options;
  * dependencies between answers (`when`): no Nvidia questions on an AMD GPU…
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

from roudix_installer import host_defaults, host_profile
from roudix_installer.choices import (
    LATEST_DESKTOPS, LATEST_SHELLS,
    _boot_aspects, _boot_resolutions, _mark_detected, _bootloaders, _branches, _brave_variants, _browsers, _cpus,
    _default_shells, _desktop_integrations, _desktops, _discord, _eac_vendors, _editors,
    _file_managers, _fluxer_channel, _gfx_keyboard_layouts, _gpus, _kernels, _kernels_chaotic,
    _keymaps, _laptop_backends, _latest_title, _locales, _mail_client, _matrix, _memory_types,
    _mesa_git_sources, _music_player, _nvidia_driver_sources, _nvidia_kernel_sources, _office,
    _password_manager, _plymouth_themes, _rgb_options, _shells, _spicetify_themes, _telegram,
    _terminals, _timezones, _torrent_client, _video_editors, _video_player, _zen_variants,
    seed_allowed,
)
from roudix_installer.config_gen import OFFICE_DICTIONARIES
from roudix_installer.hardware_detect import (
    detect_cpu, detect_gpu, detect_laptop, detect_main_screen, detect_ram_sku, detect_screen_count,
    detect_smbus, detect_thinkpad, detect_vm, is_bios_boot,
)
from roudix_installer.i18n import tr, tr_noop
from roudix_installer.state import safe_nix_text

SHELL_DESKTOPS = ("niri", "hyprland", "mangowc", "umbriel")   # compositors with a separate shell (bar/UI)
SKIP = object()   # `force` result: do not ask, do not touch the value


# ── Context ───────────────────────────────────────────────────────────────

@dataclass
class Ctx:
    """Facts about this run the questions depend on."""
    listed: Optional[set] = None        # options the host profile lists (None = every question)
    bios: bool = False                  # booted in legacy BIOS mode
    existing: bool = False              # converting an installed NixOS
    gpu_detected: str = ""
    cpu_detected: str = ""
    screen_res: str = ""
    screen_count: int = 0
    asked: set = field(default_factory=set)   # ids of the questions actually put to the user
    _cache: dict = field(default_factory=dict)

    def cached(self, key, fn):
        """Slow detections (dmidecode, i2cdetect) run once, and only if needed."""
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]


def make_ctx(state, existing: bool) -> Ctx:
    res, _aspect = detect_main_screen()
    return Ctx(listed=host_profile.listed_options(state.hostname or "roudix"), bios=is_bios_boot(),
               existing=existing, screen_res=res or "", screen_count=detect_screen_count())


def prepare(state, ctx: Ctx) -> dict:
    """Pre-fill the answers: the profile's example values first, then what the
    hardware says (a detected GPU/CPU wins over the example, which describes one
    specific machine). Returns {attribute: value} applied from the profile.
    Call once, after the profile is chosen and before the first question."""
    seeded = host_defaults.seed_state(state, state.hostname, allowed=seed_allowed())
    gpu, nvidia_laptop = detect_gpu()
    cpu = detect_cpu()
    ctx.gpu_detected, ctx.cpu_detected = gpu or "", cpu or ""
    if gpu:
        state.gpu = gpu
        state.nvidia_laptop = nvidia_laptop
    if cpu:
        state.cpu = cpu
    if nvidia_laptop or detect_laptop():
        state.laptop = True
    if detect_thinkpad():
        state.laptop = True
        state.laptop_thinkpad = True
    _res, aspect = detect_main_screen()
    if aspect:
        state.boot_aspect = aspect
    if ctx.screen_res and ctx.screen_count >= 2:
        state.boot_resolution = ctx.screen_res
    if detect_vm():
        state.vm_guest = True
    return seeded


def finalize(state, ctx: Ctx) -> None:
    """What the GTK page does after the last answer: drop stale answers."""
    # Only the compositor / shell actually chosen (and asked about) keep their
    # "latest (flake)" switch; the others fall back to nixpkgs.
    for name in ("niri", "mangowc", "umbriel", "noctalia", "dms", "caelestia"):
        keep = (("latest_de" in ctx.asked and state.desktop == name and name in LATEST_DESKTOPS)
                or ("latest_shell" in ctx.asked and state.desktop in SHELL_DESKTOPS
                    and state.desktop_shell == name and name in LATEST_SHELLS))
        if not keep:
            setattr(state, f"latest_{name}", False)
    # UEFI-only features are never wanted in legacy BIOS mode, whatever the profile says.
    if ctx.bios:
        state.secure_boot = False
        state.eac_enable = False


# ── Question model ────────────────────────────────────────────────────────

@dataclass
class Item:
    """One yes/no entry of a checklist."""
    attr: str
    label: str                          # msgid (translated when shown)
    keys: tuple = ()
    when: Optional[Callable] = None


@dataclass
class Q:
    id: str
    section: str                        # msgid
    title: object                       # msgid, or callable(state) -> str (already translated)
    kind: str                           # choice | bool | text | list | multi
    attr: str = ""
    choices: Optional[Callable] = None  # (state, ctx) -> [(value, label)]
    items: tuple = ()
    keys: tuple = ()                    # nix options (host profile filter)
    when: Optional[Callable] = None     # (state, ctx) -> bool
    get: Optional[Callable] = None      # (state, ctx) -> current value
    set: Optional[Callable] = None      # (state, value)
    default: Optional[Callable] = None  # (state, ctx) -> text default
    validate: Optional[Callable] = None  # (value) -> error message | None
    force: Optional[Callable] = None    # (state, ctx) -> value | SKIP | None
    note: Optional[Callable] = None     # (state, ctx) -> text shown with a forced value
    after: Optional[Callable] = None    # (state, ctx) -> text shown after the answer | None
    hint: str = ""                      # msgid shown under the title

    def title_text(self, state) -> str:
        return self.title(state) if callable(self.title) else tr(self.title)

    def current(self, state, ctx):
        return self.get(state, ctx) if self.get else getattr(state, self.attr)

    def store(self, state, value):
        (self.set or (lambda s, v: setattr(s, self.attr, v)))(state, value)


def in_profile(keys, ctx: Ctx) -> bool:
    return ctx.listed is None or any(k in ctx.listed for k in keys)


def applicable(q: Q, state, ctx: Ctx) -> bool:
    if q.kind == "multi":
        return bool(multi_items(q, state, ctx))
    if q.when and not q.when(state, ctx):
        return False
    return in_profile(q.keys, ctx)


def multi_items(q: Q, state, ctx: Ctx) -> list:
    if q.when and not q.when(state, ctx):
        return []
    return [it for it in q.items
            if in_profile(it.keys, ctx) and (it.when is None or it.when(state, ctx))]


def _safe_text(value: str):
    return None if safe_nix_text(value) else tr("Only letters, digits and . _ + - : , @ / are allowed here.")


def _safe_list(values: list):
    return next((m for v in values if (m := _safe_text(v))), None)


def _dictionaries(values: list):
    bad = [v for v in values if v not in OFFICE_DICTIONARIES]
    return tr("Allowed: {codes}").format(codes=", ".join(OFFICE_DICTIONARIES)) if bad else None


def _interval(value: str):
    return _safe_text(value) or (tr("Can't be empty.") if not value.strip() else None)


def _use_chaotic(s) -> bool:
    return s.gpu == "nvidia" and s.nvidia_kernel_source == "chaotic"


def _file_manager_force(s, _ctx):
    return {"gnome": "nautilus", "kde": "dolphin", "cinnamon": "nemo", "cosmic": SKIP}.get(s.desktop)


def _laptop_gaming_note(s, _ctx):
    if s.laptop and s.gaming and s.laptop_backend == "tlp":
        return tr("Disables tuned in favor of TLP: if gaming is also enabled, "
                  "game-performance will still launch games normally but "
                  "without the roudix-gaming CPU profile. On a gaming laptop, "
                  "pick tuned above instead.")
    return None


def _latest_note(s, _ctx):
    return tr("⚠ Roudix configurations are written for the flake (latest) "
              "versions first. On the nixpkgs version, a configuration error "
              "saying that an option, a setting or a key \"does not exist\" is "
              "normal: it was added after the nixpkgs version. Wait for nixpkgs "
              "to catch up, or turn the latest version on.")


def _gfx_get(s, _ctx):
    return f"{s.keyboard_layout}:{s.keyboard_variant}"


def _gfx_set(s, value):
    s.keyboard_layout, s.keyboard_variant = value.split(":", 1)


def _browser_set(s, value):
    # Keep the Brave variant already chosen when "Brave" is confirmed again.
    s.browser = s.browser if value == "brave" and s.browser.startswith("brave") else value


def _latest_shell_attr(s):
    return f"latest_{s.desktop_shell}"


def _latest_shell_visible(s, _ctx):
    return s.desktop in SHELL_DESKTOPS and s.desktop_shell in LATEST_SHELLS


def _latest_de_visible(s, _ctx):
    return s.desktop in LATEST_DESKTOPS


_LATEST_KEYS = ("roudix.desktop.latest.noctalia", "roudix.desktop.latest.dms",
                "roudix.desktop.latest.caelestia")
_OBS = ("roudix.contentCreation.obs.enable",)


def build() -> list:
    """Every question, in the order they are asked."""
    H, B, D, S, R, E, A, C = (tr_noop("Hardware"), tr_noop("Browser"), tr_noop("Desktop"),
                              tr_noop("System"), "RGB", tr_noop("Extras"), "Apps",
                              tr_noop("Content Creation"))
    nvidia = lambda s, c: s.gpu == "nvidia"                       # noqa: E731
    limine = lambda s, c: s.bootloader == "limine"                # noqa: E731
    shelled = lambda s, c: s.desktop in SHELL_DESKTOPS            # noqa: E731
    return [
        # ── Hardware ──
        Q("gpu", H, "GPU", "choice", "gpu", keys=("hardware.myGpu",),
          choices=lambda s, c: _mark_detected(_gpus(), c.gpu_detected)),
        Q("nvidia_laptop", H, tr_noop("Optimus laptop (Intel/AMD + NVIDIA dGPU)"), "bool", "nvidia_laptop",
          keys=("hardware.nvidiaLaptop",), when=nvidia),
        Q("laptop", H, tr_noop("Laptop (TLP)"), "bool", "laptop", keys=("roudix.laptop.enable",)),
        Q("laptop_backend", H, tr_noop("Laptop power manager"), "choice", "laptop_backend",
          keys=("roudix.laptop.backend",), when=lambda s, c: s.laptop, choices=lambda s, c: _laptop_backends()),
        Q("laptop_thinkpad", H, tr_noop("ThinkPad (40/80% battery charge thresholds)"), "bool", "laptop_thinkpad",
          keys=("roudix.laptop.thinkpad",), when=lambda s, c: s.laptop),
        Q("undervolt", H, tr_noop("AMD GPU undervolting (lact, amdgpu.ppfeaturemask)"), "bool", "undervolt_enable",
          keys=("roudix.undervolt.only-amd.enable",), when=lambda s, c: s.gpu in ("amd", "amd-legacy")),
        Q("cpu", H, "CPU", "choice", "cpu", keys=("hardware.myCpu",),
          choices=lambda s, c: _mark_detected(_cpus(), c.cpu_detected)),
        Q("nvidia_kernel_source", H, tr_noop("Kernel source (Nvidia)"), "choice", "nvidia_kernel_source",
          keys=("hardware.nvidiaKernelSource",), when=nvidia, choices=lambda s, c: _nvidia_kernel_sources(),
          hint=tr_noop("Chaotic-Nyx: precompiled Nvidia module. xddxdd: more kernels, Nvidia module built locally.")),
        Q("nvidia_driver_source", H, tr_noop("Nvidia driver source"), "choice", "nvidia_driver_source",
          keys=("hardware.nvidiaDriverSource",), when=nvidia, choices=lambda s, c: _nvidia_driver_sources(),
          hint=tr_noop("nixpkgs: always built locally against your kernel.")),
        Q("nvidia_open", H, tr_noop("Open kernel modules"), "bool", "nvidia_open", keys=("hardware.nvidiaOpen",),
          when=nvidia, hint=tr_noop("RTX 20xx and newer. Turn off for GTX 10xx / 16xx cards.")),
        Q("nvidia_beta", H, tr_noop("Nvidia beta driver (built locally)"), "bool", "nvidia_beta",
          keys=("hardware.nvidiaBeta",), when=nvidia),
        Q("kernel", H,
          lambda s: tr("Kernel (Chaotic-Nyx)") if _use_chaotic(s) else tr("Kernel (xddxdd)"), "choice",
          keys=("hardware.myKernel", "hardware.myKernelChaotic"),
          choices=lambda s, c: _kernels_chaotic() if _use_chaotic(s) else _kernels(),
          get=lambda s, c: s.kernel_chaotic if _use_chaotic(s) else s.kernel,
          set=lambda s, v: setattr(s, "kernel_chaotic" if _use_chaotic(s) else "kernel", v)),
        # ── Browser ──
        Q("browser", B, tr_noop("Browser"), "choice", keys=("roudix.browsers",),
          choices=lambda s, c: _browsers(),
          get=lambda s, c: "brave" if s.browser.startswith("brave") else s.browser, set=lambda s, v: _browser_set(s, v)),
        Q("brave_variant", B, tr_noop("Brave variant"), "choice", keys=("roudix.browsers",),
          when=lambda s, c: s.browser.startswith("brave"), choices=lambda s, c: _brave_variants(),
          get=lambda s, c: s.browser if s.browser.startswith("brave") else "brave",
          set=lambda s, v: setattr(s, "browser", v)),
        Q("zen", B, tr_noop("Also install Zen Browser"), "bool", "zen_browser", keys=("roudix.zen.enable",)),
        Q("zen_variant", B, tr_noop("Zen channel"), "choice", "zen_variant", keys=("roudix.zen.variant",),
          when=lambda s, c: s.zen_browser, choices=lambda s, c: _zen_variants()),
        Q("zen_mods", B, tr_noop("Zen mods (comma-separated)"), "list", "zen_mods", keys=("roudix.zen.mods",),
          when=lambda s, c: s.zen_browser, validate=_safe_list),
        Q("zen_sine", B, tr_noop("Enable Sine (Zen mod engine)"), "bool", "zen_sine_enable",
          keys=("roudix.zen.sine.enable",), when=lambda s, c: s.zen_browser),
        Q("zen_sine_mods", B, tr_noop("Sine mods (comma-separated)"), "list", "zen_sine_mods",
          keys=("roudix.zen.sine.mods",), when=lambda s, c: s.zen_browser and s.zen_sine_enable,
          validate=_safe_list),
        # ── Desktop ──
        Q("desktop", D, tr_noop("Compositor / desktop"), "choice", "desktop", keys=("roudix.desktop.type",),
          choices=lambda s, c: _desktops()),
        Q("shell", D, tr_noop("Graphical shell (bar/UI)"), "choice", "desktop_shell", keys=("roudix.desktop.shell",),
          when=shelled, choices=lambda s, c: _shells(s.desktop)),
        Q("latest_de", D, lambda s: _latest_title(LATEST_DESKTOPS.get(s.desktop, s.desktop)), "bool", keys=(),
          when=_latest_de_visible, get=lambda s, c: getattr(s, f"latest_{s.desktop}", False),
          set=lambda s, v: setattr(s, f"latest_{s.desktop}", v), after=_latest_note),
        Q("latest_shell", D, lambda s: _latest_title(LATEST_SHELLS.get(s.desktop_shell, s.desktop_shell)), "bool",
          keys=_LATEST_KEYS, when=_latest_shell_visible,
          get=lambda s, c: getattr(s, _latest_shell_attr(s), False),
          set=lambda s, v: setattr(s, _latest_shell_attr(s), v), after=_latest_note),
        Q("default_shell", D, tr_noop("Default shell"), "choice", "default_shell", keys=("roudix.shell",),
          choices=lambda s, c: _default_shells()),
        Q("terminal", D, tr_noop("Terminal"), "choice", "terminal", keys=("roudix.terminal",),
          choices=lambda s, c: _terminals()),
        Q("file_manager", D, tr_noop("File manager"), "choice", "file_manager", keys=("roudix.fileManager",),
          choices=lambda s, c: _file_managers(s.desktop_shell), force=_file_manager_force),
        Q("editor", D, tr_noop("Code editor"), "choice", "editor", keys=("roudix.editor",),
          choices=lambda s, c: _editors()),
        Q("desktop_integration", D, tr_noop("Keyring / xdg-desktop-portal"), "choice", "desktop_integration",
          keys=("roudix.desktopIntegration",), when=shelled, choices=lambda s, c: _desktop_integrations()),
        # ── System ──
        Q("vm_guest", S, tr_noop("Installing inside a VM"), "bool", "vm_guest", keys=("roudix.vmGuest.enable",)),
        Q("gaming", S, tr_noop("Gaming packages (Steam, Wine, Lutris…)"), "bool", "gaming",
          keys=("roudix.gaming.enable",), after=_laptop_gaming_note),
        Q("gaming_extras", S, tr_noop("Gaming extras"), "multi", when=lambda s, c: s.gaming, items=(
            Item("ananicy_enable", tr_noop("Ananicy (automatic gaming scheduling)"), ("roudix.gaming.ananicy.enable",)),
            Item("gaming_steam_millennium", tr_noop("Millennium (modded Steam client: themes and plugins)"),
                 ("roudix.gaming.steam.millennium.enable",)),
            Item("gaming_apps_lutris", tr_noop("Lutris"), ("roudix.gaming.apps.lutris.enable",)),
            Item("gaming_apps_heroic", tr_noop("Heroic Games Launcher (Epic/GOG/Amazon)"),
                 ("roudix.gaming.apps.heroic.enable",)),
            Item("gaming_apps_faugus", tr_noop("Faugus Launcher"), ("roudix.gaming.apps.faugus.enable",)),
            Item("gaming_apps_prismlauncher", tr_noop("Prism Launcher (Minecraft)"),
                 ("roudix.gaming.apps.prismlauncher.enable",)),
            Item("gaming_apps_modrinth", tr_noop("Modrinth App (alternative to Prism)"),
                 ("roudix.gaming.apps.modrinth.enable",)),
            Item("gaming_apps_vintagestory", tr_noop("Vintage Story"), ("roudix.gaming.apps.vintagestory.enable",)),
            Item("gaming_apps_mangohud", tr_noop("MangoHud (in-game perf overlay)"),
                 ("roudix.gaming.apps.mangohud.enable",)),
        )),
        Q("mesa_git", S, tr_noop("Mesa git (bleeding-edge graphics drivers)"), "bool", "mesa_use_git",
          keys=("roudix.mesa.useGit",)),
        Q("mesa_git_source", S, tr_noop("Mesa git source"), "choice", "mesa_git_source", keys=("roudix.mesa.gitSource",),
          when=lambda s, c: s.mesa_use_git, choices=lambda s, c: _mesa_git_sources()),
        Q("timezone", S, tr_noop("Timezone"), "choice", "timezone", keys=("time.timeZone",),
          choices=lambda s, c: _timezones()),
        Q("locale", S, tr_noop("System language"), "choice", "locale", keys=("i18n.defaultLocale",),
          choices=lambda s, c: _locales()),
        Q("keymap", S, tr_noop("Keyboard layout (console)"), "choice", "keymap", keys=("console.keyMap",),
          choices=lambda s, c: _keymaps()),
        Q("gfx_keyboard", S, tr_noop("Graphical keyboard layout (Wayland)"), "choice", keys=("roudix.keyboardLayout",),
          choices=lambda s, c: _gfx_keyboard_layouts(), get=_gfx_get, set=_gfx_set),
        # ── RGB ──
        Q("rgb", R, tr_noop("RGB controller"), "choice", "rgb", keys=("roudix.rgb",),
          choices=lambda s, c: _rgb_options(),
          hint=tr_noop("SMBus / RAM SKU aren't auto-detected — find them via "
                       "\"i2cdetect -l\" and \"sudo dmidecode -t memory | grep 'Part Number'\".")),
        Q("memory_rgb", R, tr_noop("RAM RGB (Corsair DDR4/DDR5)"), "bool", "memory_rgb_enable",
          keys=("roudix.memory.enable",), when=lambda s, c: s.rgb == "openlinkhub"),
        Q("memory_type", R, tr_noop("RAM type"), "choice", "memory_type", keys=("roudix.memory.type",),
          when=lambda s, c: s.rgb == "openlinkhub" and s.memory_rgb_enable, choices=lambda s, c: _memory_types()),
        Q("memory_smbus", R, tr_noop("SMBus (e.g. i2c-1)"), "text", "memory_smbus", keys=("roudix.memory.smBus",),
          when=lambda s, c: s.rgb == "openlinkhub" and s.memory_rgb_enable, validate=_safe_text,
          default=lambda s, c: s.memory_smbus or c.cached("smbus", detect_smbus) or "i2c-0"),
        Q("memory_sku", R, tr_noop("RAM SKU (part number)"), "text", "memory_sku", keys=("roudix.memory.sku",),
          when=lambda s, c: s.rgb == "openlinkhub" and s.memory_rgb_enable, validate=_safe_text,
          default=lambda s, c: s.memory_sku or c.cached("sku", detect_ram_sku)),
        # ── Extras ──
        Q("features", E, tr_noop("Features"), "multi", items=(
            Item("gta_fix", tr_noop("GTA Online fix (blocks the Linux anti-cheat IP)"), ("roudix.hosts.gtaFix.enable",)),
            Item("flatpak", "Flatpak", ("roudix.flatpak.enable",)),
            Item("virtualization", tr_noop("Virtualization (libvirt, virt-manager)"), ("roudix.virtualization.enable",)),
            Item("printing_enable", tr_noop("Printing (CUPS)"), ("roudix.printing.enable",)),
            Item("printing_scanners", tr_noop("Scanners (SANE)"), ("roudix.printing.scanners.enable",)),
            Item("vpn_openvpn", tr_noop("OpenVPN (NetworkManager plugin)"), ("roudix.vpn.openvpn.enable",)),
            Item("waydroid_enable", "Waydroid (Android)", ("roudix.waydroid.enable",)),
        )),
        Q("autoupdate", E, tr_noop("Automatic updates"), "bool", "autoupdate", keys=("roudix.autoupdate.enable",)),
        Q("autoupdate_interval", E, tr_noop("Interval (e.g. 1h, 6h, 24h)"), "text", "autoupdate_interval",
          keys=("roudix.autoupdate.interval",), when=lambda s, c: s.autoupdate, validate=_interval),
        Q("branch", E, tr_noop("Branch (install + updates)"), "choice", "branch", keys=("roudix.autoupdate.branch",),
          choices=lambda s, c: _branches()),
        Q("bootloader", E, tr_noop("Bootloader"), "choice", "bootloader", keys=("roudix.boot.bootloader",),
          choices=lambda s, c: _bootloaders()),
        Q("plymouth", E, tr_noop("Boot splash"), "choice", "plymouth_theme", keys=("roudix.boot.plymouth.theme",),
          choices=lambda s, c: _plymouth_themes()),
        Q("boot_aspect", E, tr_noop("Boot wallpaper format (Limine)"), "choice", "boot_aspect",
          keys=("roudix.boot.wallpaperAspect",), when=limine,
          choices=lambda s, c: _mark_detected(_boot_aspects(), detect_main_screen()[1])),
        Q("boot_resolution", E, tr_noop("Limine menu resolution"), "choice", "boot_resolution",
          keys=("roudix.boot.menuResolution",),
          when=lambda s, c: s.bootloader == "limine" and len(_boot_resolutions(c.screen_res)) > 1,
          choices=lambda s, c: _boot_resolutions(c.screen_res)),
        Q("secure_boot", E, tr_noop("Secure Boot (sign the bootloader)"), "bool", "secure_boot",
          keys=("roudix.boot.secureBoot.enable",), when=lambda s, c: not c.bios,
          hint=tr_noop("Keys are created during the install; enrolling them in the firmware is "
                       "done afterwards (docs/secure-boot-eac.md).")),
        Q("eac", E, tr_noop("EAC Linux v2 boot entry (experimental)"), "bool", "eac_enable",
          keys=("roudix.boot.eac.enable",), when=lambda s, c: s.bootloader == "limine" and not c.bios,
          hint=tr_noop("Separate “NixOS EAC” entry on a Fedora/Bazzite-signed kernel. Needs Secure Boot "
                       "and a TPM 2.0; Epic has not confirmed it accepts this yet.")),
        Q("eac_vendor", E, tr_noop("EAC kernel"), "choice", "eac_vendor", keys=("roudix.boot.eac.vendor",),
          when=lambda s, c: s.bootloader == "limine" and not c.bios and s.eac_enable,
          choices=lambda s, c: _eac_vendors(),
          force=lambda s, c: "bazzite" if s.gpu == "nvidia" else None,
          note=lambda s, c: tr("NVIDIA GPU: only Bazzite ships signed NVIDIA modules")),
        Q("matrix", E, tr_noop("Matrix client"), "choice", "matrix_client", keys=("roudix.matrixClient",),
          choices=lambda s, c: _matrix()),
        Q("discord", E, tr_noop("Discord"), "choice", "discord", keys=("roudix.discord",),
          choices=lambda s, c: _discord()),
        Q("telegram", E, "Telegram", "choice", "telegram", keys=("roudix.telegram",),
          choices=lambda s, c: _telegram()),
        Q("video_player", E, tr_noop("Video player"), "choice", "video_player", keys=("roudix.videoPlayer",),
          choices=lambda s, c: _video_player()),
        Q("torrent_client", E, tr_noop("Torrent client"), "choice", "torrent_client", keys=("roudix.torrentClient",),
          choices=lambda s, c: _torrent_client()),
        Q("music_player", E, tr_noop("Music player"), "choice", "music_player", keys=("roudix.musicPlayer",),
          choices=lambda s, c: _music_player()),
        Q("mail_client", E, tr_noop("Mail client"), "choice", "mail_client", keys=("roudix.mailClient",),
          choices=lambda s, c: _mail_client()),
        Q("password_manager", E, tr_noop("Password manager"), "choice", "password_manager",
          keys=("roudix.passwordManager",), choices=lambda s, c: _password_manager()),
        Q("office", E, tr_noop("Office suite"), "choice", "office", keys=("roudix.office",),
          choices=lambda s, c: _office()),
        Q("office_dictionaries", E, tr_noop("Office dictionaries (comma-separated: en, fr, es, de, it, pt)"), "list",
          "office_dictionaries", keys=("roudix.officeDictionaries",), when=lambda s, c: s.office != "none",
          validate=_dictionaries),
        # ── Apps ──
        Q("apps", A, tr_noop("Turn on the ones you want preinstalled."), "multi", items=(
            Item("app_gimp", "GIMP", ("roudix.apps.gimp.enable",)),
            Item("app_inkscape", "Inkscape", ("roudix.apps.inkscape.enable",)),
            Item("app_songrec", "SongRec", ("roudix.apps.songrec.enable",)),
            Item("app_easyeffects", "EasyEffects (+ rnnoise)", ("roudix.apps.easyeffects.enable",)),
            Item("app_signal", "Signal", ("roudix.apps.signal.enable",)),
            Item("app_zapzap", "ZapZap", ("roudix.apps.zapzap.enable",)),
            Item("app_fluxer", "Fluxer", ("roudix.apps.fluxer.enable",)),
            Item("app_cressida", "Cressida", ("roudix.apps.cressida.enable",)),
        )),
        Q("fluxer_channel", A, tr_noop("Fluxer channel"), "choice", "app_fluxer_channel",
          keys=("roudix.apps.fluxer.channel",), when=lambda s, c: s.app_fluxer,
          choices=lambda s, c: _fluxer_channel()),
        Q("spicetify_theme", A, tr_noop("Spicetify theme"), "choice", "spicetify_theme",
          keys=("roudix.spicetify.theme",), when=lambda s, c: s.music_player == "spotify",
          choices=lambda s, c: _spicetify_themes()),
        Q("spicetify_color_scheme", A, tr_noop("Spicetify color scheme (empty = theme default)"), "text",
          "spicetify_color_scheme", keys=("roudix.spicetify.colorScheme",),
          when=lambda s, c: s.music_player == "spotify", validate=_safe_text),
        Q("spicetify_toggles", A, "Spicetify", "multi", when=lambda s, c: s.music_player == "spotify", items=(
            Item("spicetify_adblock", tr_noop("Adblock extension (Spicetify)"),
                 ("roudix.spicetify.extensions.adblock.enable",)),
            Item("spicetify_hide_podcasts", tr_noop("Hide podcasts (Spicetify)"),
                 ("roudix.spicetify.extensions.hidePodcasts.enable",)),
            Item("spicetify_marketplace", "Spicetify Marketplace", ("roudix.spicetify.marketplace.enable",)),
        )),
        # ── Content creation ──
        Q("content_creation", C, tr_noop("Enable content-creation tooling"), "bool", "content_creation_enable",
          keys=("roudix.contentCreation.enable",)),
        Q("cc_tools", C, tr_noop("Content-creation tools"), "multi", when=lambda s, c: s.content_creation_enable, items=(
            Item("obs_enable", "OBS Studio", ("roudix.contentCreation.obs.enable",)),
            Item("virtual_camera_enable", tr_noop("Virtual camera (v4l2loopback)"),
                 ("roudix.contentCreation.virtualCamera.enable",)),
            Item("chatterino_enable", tr_noop("Chatterino2 (third-party Twitch chat)"),
                 ("roudix.contentCreation.streaming.chatterino.enable",)),
        )),
        Q("obs_plugins", C, tr_noop("OBS plugins"), "multi",
          when=lambda s, c: s.content_creation_enable and s.obs_enable, items=(
            Item("obs_plugin_vkcapture", tr_noop("VKCapture (Vulkan/OpenGL game capture)"), _OBS),
            Item("obs_plugin_pipewire_audio_capture", tr_noop("Pipewire Audio Capture (per-app audio)"), _OBS),
            Item("obs_plugin_background_removal", tr_noop("Background Removal (AI virtual background)"), _OBS),
            Item("obs_plugin_move_transition", tr_noop("Move Transition (source animations)"), _OBS),
            Item("obs_plugin_aitum_multistream", tr_noop("Aitum Multistream (multi-platform streaming)"), _OBS),
            Item("obs_plugin_gstreamer", tr_noop("GStreamer (extra sources/outputs)"), _OBS),
            Item("obs_plugin_composite_blur", tr_noop("Composite Blur (blur/glass filters)"), _OBS),
            Item("obs_plugin_advanced_scene_switcher", tr_noop("Advanced Scene Switcher (automated scene switching)"), _OBS),
            Item("obs_plugin_input_overlay", tr_noop("Input Overlay (on-screen keyboard/mouse/gamepad)"), _OBS),
            Item("obs_plugin_waveform", tr_noop("Waveform (audio waveform/spectrum)"), _OBS),
        )),
        Q("video_editor", C, tr_noop("Video editor"), "choice", "video_editor",
          keys=("roudix.contentCreation.videoEditor",), when=lambda s, c: s.content_creation_enable,
          choices=lambda s, c: _video_editors()),
    ]

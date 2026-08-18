import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

from gi.repository import Adw, Gdk, GLib, Gtk, Pango

from roudix_installer import btrfs_patch, config_gen, disko_gen
from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header

# Catppuccin Mocha, same palette as the rest of Roudix's theming.
_BASE = "#1e1e2e"
_MANTLE = "#181825"
_SURFACE0 = "#313244"
_TEXT = "#cdd6f4"
_BLUE = "#89b4fa"
_RED = "#f38ba8"
_YELLOW = "#f9e2af"
_GREEN = "#a6e3a1"

_TERMINAL_CSS = f"""
textview.roudix-terminal,
textview.roudix-terminal text {{
  background-color: {_BASE};
  color: {_TEXT};
  caret-color: {_TEXT};
}}
textview.roudix-terminal {{
  font-family: "JetBrainsMono Nerd Font", "Fira Code", monospace;
  font-size: 11pt;
  padding: 10px 14px;
}}
box.roudix-terminal-frame {{
  border-radius: 12px;
  border: 1px solid {_SURFACE0};
}}
box.roudix-terminal-titlebar {{
  background-color: {_MANTLE};
  padding: 8px 12px;
}}
box.roudix-term-dot {{
  border-radius: 999px;
  min-width: 11px;
  min-height: 11px;
}}
box.roudix-term-dot.dot-red {{ background-color: {_RED}; }}
box.roudix-term-dot.dot-yellow {{ background-color: {_YELLOW}; }}
box.roudix-term-dot.dot-green {{ background-color: {_GREEN}; }}
"""

_css_loaded = False


def _ensure_terminal_css():
    # Scoped by unique CSS class names, so it's safe to load once for the
    # whole app rather than per-page — guarded so repeated ProgressPage
    # construction (shouldn't happen, main.py caches pages, but just in
    # case) never stacks duplicate providers.
    global _css_loaded
    if _css_loaded:
        return
    provider = Gtk.CssProvider()
    provider.load_from_string(_TERMINAL_CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    _css_loaded = True


class ProgressPage(Adw.NavigationPage):
    def __init__(self, state):
        super().__init__(title=L("Installation", "Installation"), can_pop=False)
        self.state = state
        _ensure_terminal_css()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=32, margin_bottom=32, margin_start=32, margin_end=32,
                       vexpand=True)

        self.status_label = Gtk.Label(label=L("Préparation…", "Preparing…"), css_classes=["title-3"],
                                       halign=Gtk.Align.START)
        self.progress = Gtk.ProgressBar(show_text=False)
        box.append(self.status_label)
        box.append(self.progress)

        # ── "terminal" ────────────────────────────────────────────────────
        term_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True,
                              css_classes=["roudix-terminal-frame"])
        term_frame.set_overflow(Gtk.Overflow.HIDDEN)  # clips children to the rounded corners

        titlebar = Gtk.Box(spacing=10, css_classes=["roudix-terminal-titlebar"])
        dots = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        for dot_class in ("dot-red", "dot-yellow", "dot-green"):
            dots.append(Gtk.Box(css_classes=["roudix-term-dot", dot_class]))
        titlebar.append(dots)
        titlebar.append(Gtk.Label(label=L("Journal d'installation", "Installation log"),
                                   css_classes=["dim-label"], valign=Gtk.Align.CENTER))
        titlebar.append(Gtk.Box(hexpand=True))  # spacer, pushes the copy button to the right
        copy_btn = Gtk.Button(icon_name="edit-copy-symbolic", css_classes=["flat"],
                               valign=Gtk.Align.CENTER,
                               tooltip_text=L("Copier le journal", "Copy log"))
        copy_btn.connect("clicked", self._on_copy_log_clicked)
        titlebar.append(copy_btn)
        term_frame.append(titlebar)

        self.log_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                      css_classes=["roudix-terminal"])
        self._init_log_tags()

        self.log_scroller = Gtk.ScrolledWindow(vexpand=True, min_content_height=340)
        self.log_scroller.set_child(self.log_view)
        term_frame.append(self.log_scroller)

        box.append(term_frame)

        bottom_row = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, margin_top=4)
        self.reboot_check = Gtk.CheckButton(label=L("Redémarrer maintenant", "Reboot now"), active=True)
        self.reboot_check.set_visible(False)
        bottom_row.append(self.reboot_check)

        self.finish_btn = Gtk.Button(label=L("Terminer", "Finish"),
                                      css_classes=["suggested-action", "pill"])
        self.finish_btn.connect("clicked", self._on_finish_clicked)
        self.finish_btn.set_visible(False)
        bottom_row.append(self.finish_btn)
        box.append(bottom_row)

        self.set_child(page_with_header(L("Installation", "Installation"), box))
        self.connect("shown", lambda *_: self._start())

    def _init_log_tags(self):
        buf = self.log_view.get_buffer()
        buf.create_tag("cmd", foreground=_BLUE, weight=Pango.Weight.BOLD)
        buf.create_tag("error", foreground=_RED, weight=Pango.Weight.BOLD)
        buf.create_tag("success", foreground=_GREEN, weight=Pango.Weight.BOLD)

    def _on_copy_log_clicked(self, _btn):
        buf = self.log_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
            self.log_view.get_clipboard().set(text)
        except Exception:  # noqa: BLE001 — clipboard access is best-effort, never worth crashing over
            pass

    def _on_finish_clicked(self, _btn):
        if self.reboot_check.get_active():
            GLib.idle_add(self._log, L("Redémarrage…", "Rebooting…"))
            subprocess.Popen(self._priv(["systemctl", "reboot"]))
        else:
            self.get_root().get_application().quit()

    @staticmethod
    def _tag_for_line(text: str) -> Optional[str]:
        stripped = text.strip()
        if stripped.startswith("$ "):
            return "cmd"
        lowered = stripped.lower()
        if lowered.startswith(("erreur", "error")) or "traceback" in lowered:
            return "error"
        if "🎉" in stripped or "✓" in stripped:
            return "success"
        return None

    def _log(self, text: str):
        buf = self.log_view.get_buffer()

        # Only auto-follow the tail if the user was already scrolled to the
        # bottom before this line arrived — if they scrolled up to read
        # something, new output shouldn't yank the view back down.
        vadj = self.log_scroller.get_vadjustment()
        was_at_bottom = True
        if vadj is not None:
            was_at_bottom = vadj.get_value() >= (vadj.get_upper() - vadj.get_page_size() - 8)

        tag_name = self._tag_for_line(text)
        end_iter = buf.get_end_iter()
        if tag_name:
            buf.insert_with_tags_by_name(end_iter, text + "\n", tag_name)
        else:
            buf.insert(end_iter, text + "\n")

        if was_at_bottom:
            end_mark = buf.create_mark(None, buf.get_end_iter(), left_gravity=False)
            self.log_view.scroll_to_mark(end_mark, 0.0, True, 0.0, 1.0)
            buf.delete_mark(end_mark)

    def _set_status(self, label: str, fraction: float):
        self.status_label.set_label(label)
        self.progress.set_fraction(fraction)

    def _start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            self._step_partition()
            self._step_config()
            self._step_install()
            GLib.idle_add(self._set_status, L("Installation terminée 🎉", "Installation complete 🎉"), 1.0)
            GLib.idle_add(self.reboot_check.set_visible, True)
            GLib.idle_add(self.finish_btn.set_visible, True)
        except Exception as exc:  # noqa: BLE001
            GLib.idle_add(self._log, f"{L('Erreur', 'Error')}: {exc}")
            GLib.idle_add(self._set_status, L("Échec de l'installation", "Installation failed"), 0.0)
            GLib.idle_add(self.reboot_check.set_active, False)
            GLib.idle_add(self.finish_btn.set_visible, True)

    def _priv(self, cmd: list[str]) -> list[str]:
        """
        Prefix with sudo when not already root. The autostart .desktop entry
        already launches roudix-installer through `sudo --preserve-env`, so
        this is a no-op there — it only matters when testing via `nix run`
        as the plain live user (no root -> disko/mount/nixos-install would
        otherwise fail with "Error is 13").
        """
        if os.geteuid() == 0:
            return cmd
        return ["sudo", "-n"] + cmd

    def _run_cmd(self, cmd: list[str]):
        full = self._priv(cmd)
        GLib.idle_add(self._log, f"$ {' '.join(full)}")
        proc = subprocess.Popen(
            full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            # Without this, a child reading stdin (waiting for input a GUI
            # app can never provide) hangs forever instead of failing fast —
            # gets EOF immediately instead.
            stdin=subprocess.DEVNULL,
        )
        for line in proc.stdout:
            GLib.idle_add(self._log, line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} {L('a échoué', 'failed')} (code {proc.returncode})")

    def _run_cmd_with_input(self, cmd: list[str], input_text: str):
        """Like _run_cmd, but actually feeds stdin — for chpasswd."""
        full = self._priv(cmd)
        GLib.idle_add(self._log, f"$ {' '.join(cmd)}")  # never log input_text
        proc = subprocess.run(full, input=input_text, capture_output=True, text=True)
        if proc.stdout:
            GLib.idle_add(self._log, proc.stdout.rstrip())
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} {L('a échoué', 'failed')} (code {proc.returncode}): {proc.stderr.strip()}")

    # ── Partitioning ──────────────────────────────────────────────────────

    def _step_partition(self):
        mode = self.state.disk.mode
        if mode in ("simple", "advanced"):
            self._partition_disko()
        elif mode == "manual":
            self._partition_manual()
        else:
            raise ValueError(f"{L('Mode de partitionnement inconnu', 'Unknown partitioning mode')}: {mode}")

    def _partition_disko(self):
        GLib.idle_add(self._set_status, L("Partitionnement du disque…", "Partitioning the disk…"), 0.15)
        disko_nix = disko_gen.generate(self.state.disk)
        Path("/tmp/roudix-disko.nix").write_text(disko_nix)
        self._run_cmd(["disko", "--mode", "disko", "/tmp/roudix-disko.nix"])

    def _partition_manual(self):
        """
        Partitions were already made by hand in GParted. We just mount them
        in the right order — root first, then boot, then swap — same result
        as Calamares' manual partitioning, but via plain mount(8).
        """
        GLib.idle_add(self._set_status, L("Montage des partitions…", "Mounting partitions…"), 0.2)
        mapping = self.state.disk.manual_partitions
        root = next((dev for dev, mp in mapping.items() if mp == "/"), None)
        if not root:
            raise ValueError(L("Aucune partition assignée à / — impossible de continuer", "No partition assigned to / — cannot continue"))

        self._run_cmd(["mount", root, "/mnt"])

        boot = next((dev for dev, mp in mapping.items() if mp == "/boot"), None)
        if boot:
            self._run_cmd(["mkdir", "-p", "/mnt/boot"])
            self._run_cmd(["mount", boot, "/mnt/boot"])

        swap = next((dev for dev, mp in mapping.items() if mp == "swap"), None)
        if swap:
            self._run_cmd(["swapon", swap])

    # ── Configuration ─────────────────────────────────────────────────────

    def _step_config(self):
        GLib.idle_add(self._set_status, L("Copie de la configuration…", "Copying the configuration…"), 0.4)
        self._run_cmd(["mkdir", "-p", "/mnt/etc/nixos"])

        if Path("/iso-cfg").is_dir():
            self._run_cmd(["cp", "-r", "/iso-cfg/.", "/mnt/etc/nixos/"])
        else:
            # /iso-cfg only exists inside an ISO actually built with the
            # current iso-configuration.nix (isoImage.contents embeds it).
            # Booted an older ISO, or testing outside one entirely? Fall
            # back to a plain clone — same source roudix-installer.sh used
            # before there was an ISO pipeline at all.
            GLib.idle_add(
                self._log,
                L(
                    "/iso-cfg introuvable (ISO pas (encore) reconstruite avec "
                    "isoImage.contents, ou test hors ISO) — clone direct depuis GitHub à la place.",
                    "/iso-cfg not found (ISO not (yet) rebuilt with isoImage.contents, "
                    "or testing outside an ISO) — cloning straight from GitHub instead.",
                ),
            )
            self._run_cmd(["git", "clone", "https://github.com/RoudineBWT/Roudix", "/mnt/etc/nixos"])

        GLib.idle_add(self._set_status, L("Détection du matériel…", "Detecting hardware…"), 0.5)
        # Generate into the default location then copy — same as
        # roudix-installer.sh, which does this specifically to avoid
        # stdout-capture truncation on btrfs. Manual mode already mounted
        # the real target filesystems, so this picks them up like it
        # would on physical hardware; disko modes work the same way
        # since disko has already mounted everything by this point.
        self._run_cmd(["nixos-generate-config", "--root", "/mnt"])
        hw_config = Path("/mnt/etc/nixos/hosts/roudix/hardware-configuration.nix")
        self._run_cmd(["cp", "/mnt/etc/nixos/hardware-configuration.nix", str(hw_config)])

        patched = btrfs_patch.patch_hardware_config(hw_config)
        if patched:
            GLib.idle_add(
                self._log,
                L(
                    f"btrfs détecté — options de montage auto-patchées pour: {', '.join(patched)}",
                    f"btrfs detected — mount options auto-patched for: {', '.join(patched)}",
                ),
            )

        GLib.idle_add(self._set_status, L("Génération de local.nix / username.nix…", "Generating local.nix / username.nix…"), 0.6)
        config_gen.write_config(self.state, Path("/mnt/etc/nixos"))
        GLib.idle_add(self._log, L("hosts/roudix/local.nix, username.nix, home/local.nix écrits.", "hosts/roudix/local.nix, username.nix, home/local.nix written."))

        # nixos-install --flake resolves /mnt/etc/nixos through Nix's
        # git+file fetcher whenever that directory is a git repo (always
        # true in the clone-fallback case, and also true if /iso-cfg was
        # ever a git checkout at some point). That fetcher only sees
        # *tracked* files. Plain `git add -A` respects .gitignore, and the
        # repo very likely ignores hardware-configuration.nix on purpose
        # (it's machine-specific) — so it gets silently skipped unless we
        # force-add the exact generated files.
        self._run_cmd([
            "bash", "-c",
            "if [ -d /mnt/etc/nixos/.git ]; then "
            "git -C /mnt/etc/nixos add -A; "
            "for f in hosts/roudix/hardware-configuration.nix hosts/roudix/local.nix "
            "hosts/roudix/username.nix home/local.nix modules/system/boot.local.nix; do "
            "[ -f \"/mnt/etc/nixos/$f\" ] && git -C /mnt/etc/nixos add -f \"$f\"; "
            "done; "
            "fi",
        ])

    # ── Install ───────────────────────────────────────────────────────────

    def _step_install(self):
        GLib.idle_add(self._set_status, L("Installation du système…", "Installing the system…"), 0.75)
        self._run_cmd([
            "nixos-install",
            "--flake", "/mnt/etc/nixos#roudix",
            "--no-root-passwd",
            "--option", "accept-flake-config", "true",
        ])

        if self.state.password:
            GLib.idle_add(self._set_status, L("Configuration du mot de passe…", "Setting the password…"), 0.9)
            # Sets it directly in the installed system's /etc/shadow via
            # chroot — same place any other distro's installer would put
            # it — rather than baking a password hash into the declarative
            # config that ends up committed to git.
            self._run_cmd_with_input(
                ["nixos-enter", "--root", "/mnt", "-c", "chpasswd"],
                f"{self.state.username}:{self.state.password}\n",
            )

        GLib.idle_add(self._set_status, L("Copie de la config pour nh os switch…", "Copying config for nh os switch…"), 0.95)
        config_dir = f"/mnt/home/{self.state.username}/.config/roudix"
        self._run_cmd(["mkdir", "-p", config_dir])
        self._run_cmd(["cp", "-r", "/mnt/etc/nixos/.", config_dir])
        self._run_cmd(["chown", "-R", "1000:1000", f"/mnt/home/{self.state.username}/.config"])

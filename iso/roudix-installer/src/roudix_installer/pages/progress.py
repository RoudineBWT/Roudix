import os
import subprocess
import threading
from pathlib import Path

from gi.repository import Adw, GLib, Gtk

from roudix_installer import btrfs_patch, config_gen, disko_gen
from roudix_installer.i18n import L
from roudix_installer.ui_helpers import page_with_header


class ProgressPage(Adw.NavigationPage):
    def __init__(self, state):
        super().__init__(title=L("Installation", "Installation"), can_pop=False)
        self.state = state

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=48, margin_bottom=48, margin_start=48, margin_end=48,
                       valign=Gtk.Align.CENTER)

        self.status_label = Gtk.Label(label=L("Préparation…", "Preparing…"), css_classes=["title-3"])
        self.progress = Gtk.ProgressBar(show_text=False)
        self.log_view = Gtk.TextView(editable=False, monospace=True)
        scroller = Gtk.ScrolledWindow(min_content_height=220)
        scroller.set_child(self.log_view)

        for w in (self.status_label, self.progress, scroller):
            box.append(w)

        self.set_child(page_with_header(L("Installation", "Installation"), box))
        self.connect("shown", lambda *_: self._start())

    def _log(self, text: str):
        buf = self.log_view.get_buffer()
        buf.insert(buf.get_end_iter(), text + "\n")

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
        except Exception as exc:  # noqa: BLE001
            GLib.idle_add(self._log, f"{L('Erreur', 'Error')}: {exc}")
            GLib.idle_add(self._set_status, L("Échec de l'installation", "Installation failed"), 0.0)

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
        proc = subprocess.Popen(full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            GLib.idle_add(self._log, line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} {L('a échoué', 'failed')} (code {proc.returncode})")

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
        # *tracked* files — anything just written above (hardware-config,
        # local.nix, username.nix...) is invisible to the flake until
        # staged, even uncommitted. Skipping this step is exactly what
        # produced "path ... does not exist" on nixos-install.
        self._run_cmd([
            "bash", "-c",
            "if [ -d /mnt/etc/nixos/.git ]; then git -C /mnt/etc/nixos add -A; fi",
        ])

    # ── Install ───────────────────────────────────────────────────────────

    def _step_install(self):
        GLib.idle_add(self._set_status, L("Installation du système…", "Installing the system…"), 0.75)
        self._run_cmd([
            "nixos-install",
            "--flake", "/mnt/etc/nixos#roudix",
            "--no-root-passwd",
        ])

        GLib.idle_add(self._set_status, L("Copie de la config pour nh os switch…", "Copying config for nh os switch…"), 0.95)
        config_dir = f"/mnt/home/{self.state.username}/.config/roudix"
        self._run_cmd(["mkdir", "-p", config_dir])
        self._run_cmd(["cp", "-r", "/mnt/etc/nixos/.", config_dir])
        self._run_cmd(["chown", "-R", "1000:1000", f"/mnt/home/{self.state.username}/.config"])

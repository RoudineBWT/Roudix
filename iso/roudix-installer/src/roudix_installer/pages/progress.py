import subprocess
import threading
from pathlib import Path

from gi.repository import Adw, GLib, Gtk

from roudix_installer import config_gen, disko_gen

STEPS = [
    ("disko", "Partitionnement du disque"),
    ("config", "Génération de la configuration"),
    ("install", "Installation du système (nixos-install)"),
    ("done", "Terminé"),
]


class ProgressPage(Adw.NavigationPage):
    def __init__(self, state):
        super().__init__(title="Installation", can_pop=False)
        self.state = state

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=48, margin_bottom=48, margin_start=48, margin_end=48,
                       valign=Gtk.Align.CENTER)

        self.status_label = Gtk.Label(label="Préparation…", css_classes=["title-3"])
        self.progress = Gtk.ProgressBar(show_text=False)
        self.log_view = Gtk.TextView(editable=False, monospace=True)
        scroller = Gtk.ScrolledWindow(min_content_height=220)
        scroller.set_child(self.log_view)

        for w in (self.status_label, self.progress, scroller):
            box.append(w)

        self.set_child(box)
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
            self._step_disko()
            self._step_config()
            self._step_install()
            GLib.idle_add(self._set_status, "Installation terminée 🎉", 1.0)
        except Exception as exc:  # noqa: BLE001
            GLib.idle_add(self._log, f"Erreur: {exc}")
            GLib.idle_add(self._set_status, "Échec de l'installation", 0.0)

    def _run_cmd(self, cmd: list[str]):
        GLib.idle_add(self._log, f"$ {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            GLib.idle_add(self._log, line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} a échoué (code {proc.returncode})")

    def _step_disko(self):
        GLib.idle_add(self._set_status, "Partitionnement du disque…", 0.15)
        disko_nix = disko_gen.generate(self.state.disk)
        Path("/tmp/roudix-disko.nix").write_text(disko_nix)
        self._run_cmd([
            "disko", "--mode", "disko",
            "/tmp/roudix-disko.nix",
        ])

    def _step_config(self):
        GLib.idle_add(self._set_status, "Copie de la configuration…", 0.4)
        # Récupère le flake principal embarqué dans l'ISO (iso/roudix-cfg
        # au build time -> /iso-cfg sur le live env, cf isoImage.contents)
        Path("/mnt/etc/nixos").mkdir(parents=True, exist_ok=True)
        self._run_cmd(["cp", "-r", "/iso-cfg/.", "/mnt/etc/nixos/"])

        GLib.idle_add(self._set_status, "Détection du matériel…", 0.5)
        self._run_cmd([
            "nixos-generate-config", "--root", "/mnt", "--no-filesystems",
        ])

        GLib.idle_add(self._set_status, "Génération de la configuration…", 0.6)
        cfg = config_gen.generate(self.state)
        Path("/mnt/etc/nixos/roudix-options.nix").write_text(cfg)
        GLib.idle_add(self._log, cfg)

    def _step_install(self):
        GLib.idle_add(self._set_status, "Installation du système…", 0.75)
        self._run_cmd([
            "nixos-install",
            "--flake", "/mnt/etc/nixos#roudix",
            "--no-root-passwd",
        ])

        GLib.idle_add(self._set_status, "Copie de la config pour nh os switch…", 0.95)
        config_dir = f"/mnt/home/{self.state.username}/.config/roudix"
        self._run_cmd(["mkdir", "-p", config_dir])
        self._run_cmd(["cp", "-r", "/mnt/etc/nixos/.", config_dir])
        self._run_cmd(["chown", "-R", "1000:1000", f"/mnt/home/{self.state.username}/.config"])

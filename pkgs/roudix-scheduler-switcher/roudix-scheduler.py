#!/usr/bin/env python3
# roudix-scheduler — GTK4/Adwaita standalone SCX scheduler picker.
#
# Séparé de roudix-kernel-switcher : cette app ne fait qu'une chose, choisir
# et appliquer un scheduler SCX (façon "CachyOS Configure sched-ext"), avec
# en plus un champ de flags extra et la persistance du dernier choix (même
# non appliqué) entre deux lancements.
#
# Toute la logique root passe par un seul appel `pkexec scx-switch`
# (installé par scx.nix) → un seul prompt de mot de passe par action.

import gi  # noqa: I001 — ordre requis : require_version() AVANT l'import du repository, ne pas trier
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango  # noqa: I001

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading

# ── Paths ─────────────────────────────────────────────────────────────────────

CONFIG_DIR  = os.path.expanduser("~/.config/roudix-scheduler")
CONFIG_FILE = os.path.join(CONFIG_DIR, "state.json")

LOG_DIR  = os.path.expanduser("~/.local/share/roudix-scheduler")
LOG_FILE = os.path.join(LOG_DIR, "scheduler.log")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


log = logging.getLogger("roudix-scheduler")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


# ── Scheduler catalogue ────────────────────────────────────────────────────────
# (identique à roudix-kernel-switcher — source : nixpkgs scx.rustscheds
#  passthru.schedulers + scx-loader configuration.md)

SCX_PROFILES = ["Auto", "Gaming", "LowLatency", "PowerSave", "Server"]

PROFILE_MODE = {
    "Auto":       None,
    "Gaming":     "gaming",
    "LowLatency": "lowlatency",
    "PowerSave":  "powersave",
    "Server":     "server",
}

SCX_SCHEDULERS = {
    "none":       ("None",       "Default kernel scheduler — CFS/EEVDF",
                   SCX_PROFILES[:1]),
    "bpfland":    ("bpfland",    ("vruntime-based, interactive-first — best all-around "
                                  "(gaming, desktop, heavy load); cache-topology aware"),
                   SCX_PROFILES),
    "lavd":       ("lavd",       ("Latency-Aware Virtual Deadline — gaming + interactive; "
                                  "core compaction at low load; autopilot adjusts mode automatically"),
                   SCX_PROFILES[:4]),
    "flash":      ("flash",      ("Fairness-focused, low-latency — good for mixed "
                                  "desktop + compile workloads"),
                   SCX_PROFILES),
    "p2dq":       ("p2dq",      ("Pick-2 load balancing, two-level queue — "
                                  "general purpose; good cache locality"),
                   SCX_PROFILES),
    "rusty":      ("rusty",     ("Multi-domain load balancer — scales well on large/NUMA systems; "
                                  "no per-mode tuning"),
                   SCX_PROFILES[:1]),
    "rustland":   ("rustland",   ("Userspace Rust scheduler (proof-of-concept) — "
                                  "no per-mode tuning"),
                   SCX_PROFILES[:1]),
    "cosmos":     ("cosmos",     ("Lightweight locality-first — successor to bpfland, "
                                  "in active development"),
                   SCX_PROFILES),
    "beerland":   ("beerland",   ("Experimental — in active development; "
                                  "no per-mode tuning"),
                   SCX_PROFILES[:1]),
    "tickless":   ("tickless",   ("Server/HPC-oriented — reduces OS noise via tick suppression; "
                                  "requires nohz_full kernel param; NOT for desktop/gaming"),
                   SCX_PROFILES),
    "layered":    ("layered",    ("Layer-based — classify tasks into cgroups and apply a "
                                  "different policy per layer; highly configurable via TOML"),
                   SCX_PROFILES[:1]),
    "cake":       ("cake",       ("Profile-driven — simple Gaming/Esports/Battery profiles; "
                                  "in active development"),
                   SCX_PROFILES),
    "chaos":      ("chaos",      ("Stress-test / debugging only — amplifies race conditions; "
                                  "NOT for production use"),
                   SCX_PROFILES[:1]),
    "mitosis":    ("mitosis",    ("Experimental cell-division scheduler — "
                                  "in active development"),
                   SCX_PROFILES[:1]),
    "pandemonium": ("pandemonium", ("Experimental — in active development; "
                                    "no per-mode tuning"),
                   SCX_PROFILES[:1]),
    "rlfifo":     ("rlfifo",     ("Round-robin FIFO userspace scheduler — "
                                  "educational / proof-of-concept"),
                   SCX_PROFILES[:1]),
    "wd40":       ("wd40",       ("Experimental fork of rusty using BPF arenas — "
                                  "in active development"),
                   SCX_PROFILES[:1]),
    "flow":       ("flow",       ("Task-budget driven — every decision derived directly "
                                  "from budget, no Gaming/PowerSave/etc. profiles"),
                   SCX_PROFILES[:1]),
    "forge":      ("forge",      ("AI-agent-oriented — tuned via scx_forge_agent and a "
                                  "spec.toml optimization loop rather than manual profiles"),
                   SCX_PROFILES[:1]),
}

SCHED_IDS = list(SCX_SCHEDULERS.keys())


# ── Default per-scheduler/per-mode flags ────────────────────────────────────────
# Source de vérité : sched-ext/scx-loader, crates/scx_loader/src/config.rs,
# fonction get_default_scx_flags_for_mode() (commit main, cf. licence GPL-2.0,
# © 2024-2025 Vladislav Nepogodin/CachyOS). Reproduit ici pour l'auto-fill du
# champ "extra flags", façon "CachyOS Configure sched-ext" (cf. screenshot
# scx_bpfland + Powersave → "-m powersave").
#
# Clés : identique à PROFILE_MODE ("auto", "gaming", "lowlatency", "powersave",
# "server"). Schedulers absents de cette table (rusty, rustland, beerland,
# pandemonium, flash, chaos, mitosis, wd40, rlfifo, layered) n'ont pas de
# tuning par mode côté scx_loader — le champ reste vide/laissé tel quel.

SCX_DEFAULT_FLAGS = {
    "bpfland": {
        "auto":       ["-m", "auto"],
        "gaming":     ["-m", "all"],
        "lowlatency": ["-m", "performance", "-w"],
        "powersave":  ["-s", "20000", "-m", "powersave", "-I", "100", "-t", "100"],
        "server":     ["-s", "20000", "-S"],
    },
    "lavd": {
        "auto":       ["--autopilot", "--pinned-slice-us", "500"],
        "gaming":     ["--performance", "--pinned-slice-us", "500"],
        "lowlatency": ["--performance", "--pinned-slice-us", "500"],
        "powersave":  ["--powersave", "--pinned-slice-us", "500"],
        "server":     ["--performance", "--slice-min-us", "3000",
                        "--slice-max-us", "10000", "--pinned-slice-us", "3000"],
    },
    "p2dq": {
        "auto":       ["--sched-mode", "default"],
        "gaming":     ["--task-slice", "true", "-f", "--sched-mode", "performance"],
        "lowlatency": ["-y", "-f", "--task-slice", "true"],
        "powersave":  ["--sched-mode", "efficiency"],
        "server":     ["--keep-running"],
    },
    "tickless": {
        "auto":       [],
        "gaming":     ["-f", "5000", "-s", "5000"],
        "lowlatency": ["-f", "5000", "-s", "1000"],
        "powersave":  ["-f", "50"],
        "server":     ["-f", "100"],
    },
    "cosmos": {
        "auto":       [],
        "gaming":     ["-s", "700"],
        "lowlatency": ["-s", "700", "-m", "performance", "-w"],
        "powersave":  ["-m", "powersave"],
        "server":     [],
    },
    "cake": {
        "auto":       ["--profile", "default"],
        "gaming":     ["--profile", "gaming"],
        "lowlatency": ["--profile", "esports"],
        "powersave":  ["--profile", "battery"],
        "server":     ["--profile", "gaming"],
    },
}


def default_flags_for(scheduler: str, profile: str) -> str | None:
    """Retourne les flags par défaut (façon scx_loader) pour un couple
    scheduler/profil donné, ou None si ce scheduler n'a pas de tuning par
    mode (auto-fill à ne pas déclencher dans ce cas)."""
    mode = PROFILE_MODE.get(profile) or "auto"
    sched_flags = SCX_DEFAULT_FLAGS.get(scheduler)
    if sched_flags is None:
        return None
    flags = sched_flags.get(mode)
    if flags is None:
        return None
    return " ".join(flags)


# ── Backend detection ──────────────────────────────────────────────────────────

def has_scxctl() -> bool:
    return shutil.which("scxctl") is not None


def has_scx_switch() -> bool:
    return shutil.which("scx-switch") is not None


def available_sched_ids() -> list[str]:
    """Filtre SCHED_IDS pour ne garder que 'none' + les schedulers dont le
    binaire scx_<id> est réellement présent dans le PATH (donc buildé dans
    le scx.full de roudix-caches à l'instant T). Évite de proposer dans le
    dropdown des schedulers (ex: scx_forge, pas encore packagé partout) qui
    échoueraient à l'Apply avec une erreur peu claire côté scxctl."""
    available = ["none"]
    missing: list[str] = []
    for sched_id in SCHED_IDS:
        if sched_id == "none":
            continue
        if shutil.which(f"scx_{sched_id}"):
            available.append(sched_id)
        else:
            missing.append(sched_id)
    if missing:
        log.info("Schedulers absents du PATH (masqués du dropdown) : %s",
                  ", ".join(missing))
    return available


# ── Persisted UI state (survives across launches, independent of what's applied) ──

def load_state() -> dict[str, str]:
    default: dict[str, str] = {"scheduler": "none", "profile": "Auto", "extra": ""}
    try:
        with open(CONFIG_FILE) as f:
            data: dict[str, str] = json.load(f)
        default["scheduler"] = data.get("scheduler", "none")
        default["profile"]   = data.get("profile", "Auto")
        default["extra"]     = data.get("extra", "")
        if default["scheduler"] not in SCX_SCHEDULERS:
            default["scheduler"] = "none"
        if default["profile"] not in SCX_PROFILES:
            default["profile"] = "Auto"
    except (OSError, json.JSONDecodeError):
        pass
    return default


def save_state(scheduler: str, profile: str, extra: str):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"scheduler": scheduler, "profile": profile, "extra": extra}, f)
    except OSError as e:
        log.warning("Could not save state: %s", e)


# ── Current running state (live, read-only) ───────────────────────────────────
# `scxctl get` renvoie du texte simple : "running <sched> in <mode> mode"
# (ex: "running bpfland in auto mode"), et "running unknown in auto mode"
# quand rien ne tourne (CurrentScheduler D-Bus vaut "unknown"). Pas de
# sous-commande `status` ni de flag `--json` chez scxctl — à ne pas inventer.

_SCXCTL_GET_RE = re.compile(r"running\s+(\S+)\s+in\s+(\S+)\s+mode", re.IGNORECASE)


def get_current_scx() -> tuple[str, str]:
    if not has_scxctl():
        return "none", "Auto"
    try:
        out = subprocess.check_output(
            ["scxctl", "get"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception as e:
        log.debug("scxctl get failed: %s", e)
        return "none", "Auto"

    m = _SCXCTL_GET_RE.search(out)
    if not m:
        log.debug("scxctl get: unrecognized output: %r", out)
        return "none", "Auto"

    sched = m.group(1).strip().lower().removeprefix("scx_")
    mode  = m.group(2).strip().lower()

    if sched in ("unknown", "none", ""):
        return "none", "Auto"
    if sched not in SCX_SCHEDULERS:
        log.debug("scxctl get: unrecognized scheduler name: %r", sched)
        return "none", "Auto"

    mode_map = {v: k for k, v in PROFILE_MODE.items() if v}
    profile = mode_map.get(mode, "Auto")
    return sched, profile


def is_ananicy_enabled() -> bool:
    try:
        r = subprocess.run(["systemctl", "is-enabled", "ananicy-cpp"],
                           capture_output=True, text=True)
        return r.stdout.strip() == "enabled"
    except Exception:
        return False


def is_ananicy_active() -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", "ananicy-cpp"],
                           capture_output=True, text=True)
        return r.stdout.strip() == "active"
    except Exception:
        return False


# ── Apply — single pkexec call via scx-switch ──────────────────────────────────

def apply_scx(scheduler: str, profile: str, extra: str) -> tuple[bool, str]:
    if not has_scx_switch():
        return False, "scx-switch introuvable dans le PATH (module scx.nix non chargé ?)."
    try:
        if scheduler == "none":
            cmd = ["pkexec", "scx-switch", "unset"]
        else:
            mode = PROFILE_MODE.get(profile) or ""
            cmd = ["pkexec", "scx-switch", "set", scheduler, mode, extra.strip()]
        log.info("Running: %s", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            if scheduler == "none":
                return True, "SCX désactivé — retour au scheduler par défaut (CFS/EEVDF)."
            extra_note = f" · flags: {extra}" if extra.strip() else ""
            return True, f"scx_{scheduler} actif ({profile}){extra_note}."
        err = strip_ansi((r.stderr or r.stdout).strip())
        log.error("scx-switch failed: %s", err)
        return False, err or f"scx-switch a échoué (code {r.returncode})"
    except FileNotFoundError:
        return False, "pkexec introuvable."
    except Exception as e:
        return False, str(e)


# ── UI ──────────────────────────────────────────────────────────────────────────

class SchedulerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Roudix Scheduler")
        self.set_default_size(560, 480)

        state = load_state()
        self._scheduler = state["scheduler"]
        self._profile   = state["profile"]
        self._extra     = state["extra"]

        # Ne propose que les schedulers dont le binaire est vraiment présent
        # (cf. available_sched_ids) — évite un Apply qui échoue silencieusement
        # sur un scheduler pas encore packagé (ex: scx_forge).
        self._sched_ids = available_sched_ids()
        if self._scheduler not in self._sched_ids:
            # binaire disparu depuis le dernier lancement (rebuild, etc.)
            self._scheduler = "none"

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)
        toolbar_view.add_top_bar(Adw.HeaderBar())

        clamp = Adw.Clamp()
        clamp.set_maximum_size(520)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        toolbar_view.set_content(clamp)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(body)

        # ── Running scheduler (live, read-only) ──
        self._running_row = Adw.ActionRow()
        self._running_row.set_title("Running scheduler")
        self._running_row.add_css_class("card")
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_valign(Gtk.Align.CENTER)
        refresh_btn.add_css_class("flat")
        refresh_btn.connect("clicked", lambda _b: self._refresh_running())
        self._running_row.add_suffix(refresh_btn)
        body.append(self._running_row)

        # ── Scheduler dropdown ──
        select_lb = Gtk.ListBox()
        select_lb.set_selection_mode(Gtk.SelectionMode.NONE)
        select_lb.add_css_class("boxed-list")
        body.append(select_lb)

        sched_row = Adw.ActionRow()
        sched_row.set_title("Select scheduler")
        sched_labels = [SCX_SCHEDULERS[s][0] for s in self._sched_ids]
        self._sched_combo = Gtk.DropDown.new_from_strings(sched_labels)
        self._sched_combo.set_valign(Gtk.Align.CENTER)
        self._sched_combo.set_selected(self._sched_ids.index(self._scheduler))
        self._sched_combo.connect("notify::selected", self._on_sched_changed)
        sched_row.add_suffix(self._sched_combo)
        select_lb.append(sched_row)

        # description of currently selected scheduler
        self._sched_desc = Gtk.Label()
        self._sched_desc.set_wrap(True)
        self._sched_desc.set_xalign(0)
        self._sched_desc.add_css_class("dim-label")
        self._sched_desc.add_css_class("caption")
        self._sched_desc.set_margin_start(12)
        self._sched_desc.set_margin_end(12)
        self._sched_desc.set_margin_bottom(4)
        body.append(self._sched_desc)

        # ── Profile dropdown ──
        profile_row = Adw.ActionRow()
        profile_row.set_title("Select profile")
        self._profile_combo = Gtk.DropDown()
        self._profile_combo.set_model(Gtk.StringList.new(SCX_PROFILES))
        self._profile_combo.set_valign(Gtk.Align.CENTER)
        self._profile_combo.set_selected(SCX_PROFILES.index(self._profile))
        self._profile_combo.connect("notify::selected", self._on_profile_changed)
        profile_row.add_suffix(self._profile_combo)
        select_lb.append(profile_row)

        # ── Extra flags ──
        extra_row = Adw.EntryRow()
        extra_row.set_title("Extra scheduler flags")
        extra_row.set_text(self._extra)
        extra_row.connect("changed", self._on_extra_changed)
        self._extra_row = extra_row
        select_lb.append(extra_row)

        # ── ananicy-cpp status (read-only info) ──
        self._ananicy_row = Adw.ActionRow()
        self._ananicy_row.set_title("ananicy-cpp")
        self._ananicy_row.add_css_class("card")
        body.append(self._ananicy_row)

        body.append(Gtk.Box(vexpand=True))  # spacer

        # ── Bottom bar: Disable / Apply ──
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        body.append(bar)

        self._status_lbl = Gtk.Label(label="")
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._status_lbl.add_css_class("dim-label")
        bar.append(self._status_lbl)

        disable_btn = Gtk.Button(label="Disable")
        disable_btn.add_css_class("destructive-action")
        disable_btn.connect("clicked", self._on_disable)
        bar.append(disable_btn)

        self._apply_btn = Gtk.Button(label="Apply")
        self._apply_btn.add_css_class("suggested-action")
        self._apply_btn.connect("clicked", self._on_apply)
        bar.append(self._apply_btn)

        self._update_sched_desc()
        self._update_profile_sensitivity()
        self._refresh_running()
        self._refresh_ananicy()

        if not has_scx_switch():
            self._status_lbl.set_label(
                "⚠ scx-switch introuvable — vérifie que scx.nix est bien appliqué."
            )
            self._apply_btn.set_sensitive(False)
            disable_btn.set_sensitive(False)

    # ── refresh helpers ──

    def _refresh_running(self):
        sched, profile = get_current_scx()
        if sched == "none":
            self._running_row.set_subtitle("None — CFS/EEVDF")
        else:
            label = SCX_SCHEDULERS.get(sched, (sched, "", []))[0]
            self._running_row.set_subtitle(f"{label} · {profile}")

    def _refresh_ananicy(self):
        if not is_ananicy_enabled():
            self._ananicy_row.set_subtitle(
                "Disabled — your scheduler choice will persist after reboot"
            )
            return
        if is_ananicy_active():
            self._ananicy_row.set_subtitle(
                "Running — will be stopped automatically when a scheduler is applied"
            )
        else:
            self._ananicy_row.set_subtitle(
                "Stopped — will be restarted automatically when switching back to None"
            )

    def _update_sched_desc(self):
        _, desc, _ = SCX_SCHEDULERS.get(self._scheduler, ("", "", []))
        self._sched_desc.set_label(desc)

    def _update_profile_sensitivity(self):
        _, _, profiles = SCX_SCHEDULERS.get(self._scheduler, ("", "", SCX_PROFILES[:1]))
        has_profiles = len(profiles) > 1
        self._profile_combo.set_sensitive(has_profiles)
        if not has_profiles and self._profile != "Auto":
            self._profile = "Auto"
            self._profile_combo.set_selected(0)

    # ── signal handlers ──

    def _on_sched_changed(self, combo, _param):
        idx = combo.get_selected()
        self._scheduler = self._sched_ids[idx] if idx < len(self._sched_ids) else "none"
        self._update_sched_desc()
        self._update_profile_sensitivity()
        self._autofill_extra()
        save_state(self._scheduler, self._profile, self._extra)
        self._status_lbl.set_label("")

    def _on_profile_changed(self, combo, _param):
        idx = combo.get_selected()
        self._profile = SCX_PROFILES[idx] if idx < len(SCX_PROFILES) else "Auto"
        self._autofill_extra()
        save_state(self._scheduler, self._profile, self._extra)
        self._status_lbl.set_label("")

    def _autofill_extra(self):
        """Pré-remplit le champ 'extra flags' avec le template par défaut du
        couple scheduler/profil (façon CachyOS Configure sched-ext). Écrase
        volontairement toute valeur précédente — comme dans l'app CachyOS,
        le champ reste ensuite éditable à la main avant Apply. Ne touche à
        rien si ce scheduler n'a pas de tuning par mode connu (rusty, etc.)."""
        flags = default_flags_for(self._scheduler, self._profile)
        if flags is None:
            return
        self._extra = flags
        self._extra_row.set_text(flags)

    def _on_extra_changed(self, entry_row):
        self._extra = entry_row.get_text()
        save_state(self._scheduler, self._profile, self._extra)

    def _on_disable(self, _btn):
        self._set_busy("Disabling...")
        threading.Thread(target=self._run_apply, args=("none", "Auto", ""), daemon=True).start()

    def _on_apply(self, _btn):
        self._set_busy("Applying...")
        threading.Thread(
            target=self._run_apply, args=(self._scheduler, self._profile, self._extra), daemon=True
        ).start()

    def _set_busy(self, msg):
        self._apply_btn.set_sensitive(False)
        self._status_lbl.set_label(msg)

    def _run_apply(self, scheduler, profile, extra):
        ok, msg = apply_scx(scheduler, profile, extra)
        GLib.idle_add(self._finish, ok, f"{'✓' if ok else '✗'} {msg}")

    def _finish(self, ok, msg):
        self._status_lbl.set_label(msg)
        self._apply_btn.set_sensitive(True)
        self._refresh_running()
        self._refresh_ananicy()


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.roudix.scheduler",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        # L'icône (io.roudix.scheduler.svg) est résolue automatiquement par le
        # compositeur/DE via l'application_id ↔ le .desktop installé par le
        # package Nix, à condition qu'il matche bien "io.roudix.scheduler".
        self.connect("activate", lambda app: SchedulerWindow(app).present())


def main():
    setup_logging()
    log.info("=== Roudix Scheduler started ===")
    log.info("scxctl available: %s", has_scxctl())
    log.info("scx-switch available: %s", has_scx_switch())
    log.info("scx schedulers detected: %s", ", ".join(available_sched_ids()))
    App().run(sys.argv)


if __name__ == "__main__":
    main()

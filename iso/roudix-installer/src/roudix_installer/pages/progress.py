import os
import pwd
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional

from gi.repository import Adw, Gdk, GLib, Gtk, Pango

from roudix_installer import btrfs_patch, config_gen, disko_gen, existing_nixos, host_profile
from roudix_installer.i18n import tr
from roudix_installer.ui_helpers import page_with_header

# Roudix palette (Roudix.json, dark), same as the rest of Roudix's theming.
_BASE = "#211a15"
_MANTLE = "#17120f"
_SURFACE0 = "#2a211b"
_TEXT = "#eadbcb"
_BLUE = "#7fa3b5"
_RED = "#e5604d"
_YELLOW = "#f2b05e"
_GREEN = "#a8b86a"

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
        super().__init__(title=tr("Installation"), can_pop=False)
        self.state = state
        self._existing = state.mode == existing_nixos.MODE_EXISTING
        _ensure_terminal_css()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_top=32, margin_bottom=32, margin_start=32, margin_end=32,
                       vexpand=True)

        self.status_label = Gtk.Label(label=tr("Preparing…"), css_classes=["title-3"],
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
        titlebar.append(Gtk.Label(label=tr("Installation log"),
                                   css_classes=["dim-label"], valign=Gtk.Align.CENTER))
        titlebar.append(Gtk.Box(hexpand=True))  # spacer, pushes the copy button to the right
        copy_btn = Gtk.Button(icon_name="edit-copy-symbolic", css_classes=["flat"],
                               valign=Gtk.Align.CENTER,
                               tooltip_text=tr("Copy log"))
        copy_btn.connect("clicked", self._on_copy_log_clicked)
        titlebar.append(copy_btn)
        term_frame.append(titlebar)

        self.log_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                      css_classes=["roudix-terminal"])
        self._init_log_tags()

        self.log_scroller = Gtk.ScrolledWindow(vexpand=True, min_content_height=340)
        self.log_scroller.set_child(self.log_view)
        term_frame.append(self.log_scroller)

        # Whether new output should auto-scroll the view to the bottom.
        # Set in _log() right before each insert (based on whether the
        # user was already at the bottom), then actually applied once the
        # adjustment's `upper` catches up with the new content — see
        # _on_log_extent_changed().
        self._log_follow_tail = True
        log_vadj = self.log_scroller.get_vadjustment()
        if log_vadj is not None:
            log_vadj.connect("notify::upper", self._on_log_extent_changed)

        box.append(term_frame)

        bottom_row = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, margin_top=4)
        self.reboot_check = Gtk.CheckButton(label=tr("Reboot now"), active=True)
        self.reboot_check.set_visible(False)
        bottom_row.append(self.reboot_check)

        self.finish_btn = Gtk.Button(label=tr("Finish"),
                                      css_classes=["suggested-action", "pill"])
        self.finish_btn.connect("clicked", self._on_finish_clicked)
        self.finish_btn.set_visible(False)
        bottom_row.append(self.finish_btn)

        # Shown after a simulation: nothing was installed, so go back to Summary.
        self.back_btn = Gtk.Button(label=tr("Back to summary"), css_classes=["pill"])
        self.back_btn.connect("clicked", self._on_back_clicked)
        self.back_btn.set_visible(False)
        bottom_row.append(self.back_btn)
        box.append(bottom_row)

        self.set_child(page_with_header(tr("Installation"), box))
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

    def _on_back_clicked(self, _btn):
        nav = self.get_ancestor(Adw.NavigationView)
        if nav is not None:
            nav.pop()

    def _on_finish_clicked(self, _btn):
        if self.reboot_check.get_active():
            GLib.idle_add(self._log, tr("Rebooting…"))
            # Installed NixOS: logind lets the active session reboot without root.
            subprocess.Popen(self._priv(["systemctl", "reboot"],
                                        root=not self._existing))
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
        if vadj is not None:
            self._log_follow_tail = vadj.get_value() >= (vadj.get_upper() - vadj.get_page_size() - 8)

        tag_name = self._tag_for_line(text)
        end_iter = buf.get_end_iter()
        if tag_name:
            buf.insert_with_tags_by_name(end_iter, text + "\n", tag_name)
        else:
            buf.insert(end_iter, text + "\n")

        # Try scrolling right away — this works when the view's layout is
        # already up to date. If it isn't yet (GTK only recomputes
        # vadj.upper on its next layout pass, which can lag when nothing
        # else is forcing a redraw — e.g. the mouse never enters the
        # terminal), _on_log_extent_changed() below catches it the moment
        # the adjustment actually grows, so the log never looks stuck.
        if self._log_follow_tail and vadj is not None:
            self._scroll_log_to_bottom()

    def _on_log_extent_changed(self, _vadj, _pspec):
        if self._log_follow_tail:
            self._scroll_log_to_bottom()

    def _scroll_log_to_bottom(self):
        vadj = self.log_scroller.get_vadjustment()
        if vadj is not None:
            vadj.set_value(max(0.0, vadj.get_upper() - vadj.get_page_size()))

    def _set_status(self, label: str, fraction: float):
        self.status_label.set_label(label)
        self.progress.set_fraction(fraction)

    def _start(self):
        threading.Thread(target=self._run, daemon=True).start()

    # ── Dry run ("Simulate" button, or ROUDIX_INSTALLER_DRY_RUN=1) ─────────

    def _is_dry_run(self) -> bool:
        return bool(self.state.dry_run or os.environ.get("ROUDIX_INSTALLER_DRY_RUN"))

    def _report_config(self, root: Path, host: str, example_text: str):
        """Log what write_config() produced: diff vs the example, the verification
        of every written option, then the full file."""
        import difflib

        result = (root / f"hosts/{host}/local.nix").read_text()
        username = (root / f"hosts/{host}/username.nix").read_text().strip()
        GLib.idle_add(self._log, f"[dry-run] hosts/{host}/username.nix = {username}")
        GLib.idle_add(self._log, f"[dry-run] hosts/{host}/local.nix — lines changed vs local.nix.example:")
        changed = [l for l in difflib.unified_diff(example_text.splitlines(), result.splitlines(),
                                                   "local.nix.example", "local.nix", n=0, lineterm="")
                   if not l.startswith(("---", "+++", "@@"))]
        for line in changed or ["(none)"]:
            GLib.idle_add(self._log, line)
        self._log_verification(example_text, result)
        GLib.idle_add(self._log, f"[dry-run] hosts/{host}/local.nix — full result:")
        for line in result.splitlines():
            GLib.idle_add(self._log, line)

    def _log_verification(self, example_text: str, result_text: str):
        """Same safety net as roudix-installer.sh's check_opt(): a substitution
        that did not match is a silent no-op, so check the values landed."""
        missing = config_gen.verify_local_nix(self.state, example_text, result_text)
        if missing:
            GLib.idle_add(self._log, tr("Warning: these options were NOT confirmed in local.nix — "
                                          "review the file before rebooting: {keys}").format(keys=", ".join(missing)))
        else:
            GLib.idle_add(self._log, tr("✓ every chosen option was written to local.nix."))

    def _dry_run(self):
        """Never partition, mount or install — only generate the config the wizard
        *would* write (into a temp dir) and show it, so the wizard can be checked
        on a normal desktop."""
        import tempfile

        host = self.state.hostname
        GLib.idle_add(self._set_status, tr("Dry run — nothing is written to disk"), 0.5)
        src = host_profile.find_config_root(host)
        if src is None:
            raise RuntimeError(tr("hosts/{host}/local.nix.example not found (try ROUDIX_CFG_ROOT=<path to the repo>)").format(host=host))
        GLib.idle_add(self._log, f"[dry-run] host={host}  branch={self.state.branch}  config from {src}")
        with tempfile.TemporaryDirectory(prefix="roudix-dry-run-") as tmp:
            tmp = Path(tmp)
            for rel in (f"hosts/{host}/local.nix.example", "modules/home/local.nix.example",
                        "modules/system/boot/boot.local.nix.example"):
                if (src / rel).is_file():
                    (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src / rel, tmp / rel)
            config_gen.write_config(self.state, tmp)
            example_text = (tmp / f"hosts/{host}/local.nix.example").read_text()
            self._report_config(tmp, host, example_text)
        GLib.idle_add(self._set_status, tr("Dry run finished — nothing was changed"), 1.0)

    def _dry_run_existing(self):
        """Simulation on an installed NixOS: fetch the config into a temp dir, run
        the same generation as the real run, then make Nix *evaluate* the whole
        system (what `just check` does). Catches an option combination that does
        not build, without touching /etc/nixos, ~/.config or the bootloader."""
        s = self.state
        host = s.hostname
        GLib.idle_add(self._set_status, tr("Simulation — nothing is written"), 0.05)
        facts = existing_nixos.read_facts()
        self._log_preflight(facts)

        with tempfile.TemporaryDirectory(prefix="roudix-dry-run-") as tmp:
            repo = Path(tmp) / "roudix"
            GLib.idle_add(self._set_status, tr("Fetching the Roudix configuration…"), 0.2)
            branch = self._resolve_branch(existing_nixos.REPO_URL, s.branch)
            s.branch = branch
            try:
                self._run_cmd(["git", "clone", "--depth", "1", "--branch", branch,
                               existing_nixos.REPO_URL, str(repo)], root=False)
            except RuntimeError:
                src = host_profile.find_config_root(host)
                if src is None:
                    raise
                GLib.idle_add(self._log, tr("Clone failed — simulating with the local copy of the profiles."))
                shutil.copytree(src, repo, ignore=shutil.ignore_patterns(".git"))
            self._verify_config_layout(branch, repo)

            GLib.idle_add(self._set_status, tr("Detecting hardware…"), 0.35)
            self._install_hardware_config(repo, host)

            GLib.idle_add(self._set_status, tr("Generating local.nix / username.nix…"), 0.45)
            config_gen.write_config(s, repo)
            example_text = (repo / f"hosts/{host}/local.nix.example").read_text()
            self._report_config(repo, host, example_text)

            GLib.idle_add(self._set_status, tr("Evaluating the whole system with Nix…"), 0.6)
            self._run_cmd([
                "nix", "--extra-experimental-features", "nix-command flakes",
                "eval", "--raw", "--accept-flake-config", "--no-write-lock-file",
                f"path:{repo}#nixosConfigurations.{host}.config.system.build.toplevel.drvPath",
            ], root=False)
            GLib.idle_add(self._log, tr("✓ the configuration evaluates: Nix can build this system."))
        GLib.idle_add(self._set_status, tr("Simulation finished — nothing was changed"), 1.0)

    def _run(self):
        dry = self._is_dry_run()
        try:
            if dry:
                (self._dry_run_existing if self._existing else self._dry_run)()
                GLib.idle_add(self.back_btn.set_visible, True)
                return
            if self._existing:
                self._run_existing()
            else:
                self._step_partition()
                self._step_config()
                self._step_install()
            GLib.idle_add(self._set_status, tr("Installation complete 🎉"), 1.0)
            GLib.idle_add(self.reboot_check.set_visible, True)
            GLib.idle_add(self.finish_btn.set_visible, True)
        except Exception as exc:  # noqa: BLE001
            GLib.idle_add(self._log, tr("Error") + f": {exc}")
            GLib.idle_add(self._set_status, tr("Simulation failed") if dry else tr("Installation failed"), 0.0)
            GLib.idle_add(self.reboot_check.set_active, False)
            if dry:
                GLib.idle_add(self.back_btn.set_visible, True)
            else:
                GLib.idle_add(self.finish_btn.set_visible, True)

    def _priv(self, cmd: list[str], root: bool = True) -> list[str]:
        """
        Run `cmd` as root when `root` is set. Already root -> as is.
          * live ISO: the autostart .desktop entry launches the installer through
            `sudo --preserve-env`, so this is a no-op there; as the plain live user
            (`nix run`) `sudo -n` works because the live user has passwordless sudo.
          * installed NixOS: `sudo -n` would just fail (password needed, no tty),
            so use pkexec (polkit shows the usual password dialog). pkexec resets
            the environment and nixos-rebuild needs `nix`/`git` in PATH, hence `env`.
        """
        if not root or os.geteuid() == 0:
            return cmd
        if self._existing and shutil.which("pkexec"):
            return ["pkexec", "env", f"PATH={os.environ.get('PATH', '')}"] + cmd
        return ["sudo", "-n"] + cmd

    def _run_cmd(self, cmd: list[str], root: bool = True):
        full = self._priv(cmd, root)
        shown = ["pkexec"] + cmd if full[:1] == ["pkexec"] else full
        GLib.idle_add(self._log, f"$ {' '.join(shown)}")
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
        if full[:1] == ["pkexec"] and proc.returncode in (126, 127):
            raise RuntimeError(tr("Authentication was cancelled or refused."))
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} " + tr("failed") + f" (code {proc.returncode})")

    def _run_cmd_with_input(self, cmd: list[str], input_text: str):
        """Like _run_cmd, but actually feeds stdin — for chpasswd."""
        full = self._priv(cmd)
        GLib.idle_add(self._log, f"$ {' '.join(cmd)}")  # never log input_text
        proc = subprocess.run(full, input=input_text, capture_output=True, text=True)
        if proc.stdout:
            GLib.idle_add(self._log, proc.stdout.rstrip())
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} " + tr("failed") + f" (code {proc.returncode}): {proc.stderr.strip()}")

    # ── Partitioning ──────────────────────────────────────────────────────

    def _step_partition(self):
        mode = self.state.disk.mode
        if mode in ("simple", "advanced"):
            self._partition_disko()
        elif mode == "manual":
            self._partition_manual()
        else:
            raise ValueError(tr("Unknown partitioning mode") + f": {mode}")

    def _partition_disko(self):
        GLib.idle_add(self._set_status, tr("Partitioning the disk…"), 0.15)
        disko_nix = disko_gen.generate(self.state.disk)
        Path("/tmp/roudix-disko.nix").write_text(disko_nix)
        self._run_cmd(["disko", "--mode", "disko", "/tmp/roudix-disko.nix"])

    def _partition_manual(self):
        """
        Partitions were already made by hand in GParted. We just mount them
        in the right order — root first, then boot, then swap — same result
        as Calamares' manual partitioning, but via plain mount(8).
        """
        GLib.idle_add(self._set_status, tr("Mounting partitions…"), 0.2)
        mapping = self.state.disk.manual_partitions
        root = next((dev for dev, mp in mapping.items() if mp == "/"), None)
        if not root:
            raise ValueError(tr("No partition assigned to / — cannot continue"))

        self._run_cmd(["mount", root, "/mnt"])

        boot = next((dev for dev, mp in mapping.items() if mp == "/boot"), None)
        if boot:
            self._run_cmd(["mkdir", "-p", "/mnt/boot"])
            self._run_cmd(["mount", boot, "/mnt/boot"])

        swap = next((dev for dev, mp in mapping.items() if mp == "swap"), None)
        if swap:
            self._run_cmd(["swapon", swap])

    # ── Configuration ─────────────────────────────────────────────────────

    def _resolve_branch(self, repo_url: str, branch: str) -> str:
        """
        Confirms the chosen branch actually exists on the remote before we
        rely on it, via a plain `git ls-remote` (no clone needed for that).
        Best-effort: this is a convenience check, not a hard requirement —
        if it can't run at all (e.g. `git` not up yet, DNS not ready this
        early), we just proceed with the branch as chosen and let the real
        clone/checkout below report any actual failure.
        """
        GLib.idle_add(self._log, tr("Checking branch '{branch}'…").format(branch=branch))
        try:
            # Read-only network query: never needs root (and must not trigger a
            # polkit prompt on an installed system).
            proc = subprocess.run(
                ["git", "ls-remote", "--exit-code", "--heads", repo_url, branch],
                capture_output=True, text=True, stdin=subprocess.DEVNULL,
            )
        except Exception:  # noqa: BLE001 — no git / no network yet: skip the check, don't fail on it
            return branch

        if proc.returncode == 0 and proc.stdout.strip():
            return branch

        if branch != "main":
            GLib.idle_add(
                self._log,
                tr("Branch '{branch}' not found on {repo_url} — falling back to 'main'.").format(branch=branch, repo_url=repo_url),
            )
            return "main"
        # main itself didn't answer (likely no network at all): let the
        # clone/copy step below surface that failure clearly instead of
        # guessing further here.
        return branch

    def _clone_and_checkout(self, repo_url: str, branch: str):
        """
        Explicit clone + checkout (rather than a single `git clone --branch`)
        so the checkout is its own visible, loggable step and failures are
        unambiguous: a bad clone fails at "git clone", a branch that vanished
        between the ls-remote check above and now fails at "git checkout"
        with git's own error in the log.
        """
        self._run_cmd(["git", "clone", repo_url, "/mnt/etc/nixos"])
        self._run_cmd(["git", "-C", "/mnt/etc/nixos", "checkout", branch])

    def _verify_config_layout(self, branch: str, root: Path = Path("/mnt/etc/nixos")):
        """
        Best-effort sanity check that the branch we just checked out still
        has the files config_gen.write_config() below expects at their usual
        path. `testing`/`dev` can restructure the repo ahead of `main` — this
        never blocks the install (that's the "only if possible" part), it
        just puts a clear warning in the log instead of a confusing failure
        a few steps later.
        """
        host = self.state.hostname
        example = root / f"hosts/{host}/local.nix.example"
        if not example.is_file():
            GLib.idle_add(
                self._log,
                tr("Warning: hosts/{host}/local.nix.example not found on branch '{branch}' — local.nix generation may fail.").format(host=host, branch=branch),
            )

    def _step_config(self):
        GLib.idle_add(self._set_status, tr("Copying the configuration…"), 0.4)
        self._run_cmd(["mkdir", "-p", "/mnt/etc/nixos"])

        repo_url = "https://github.com/RoudineBWT/Roudix"
        branch = self._resolve_branch(repo_url, self.state.branch)
        self.state.branch = branch  # keep local.nix / autoupdate.branch and the summary in sync
                                     # with whatever branch we actually end up using (fallback included)

        # /iso-cfg is a snapshot of `main` taken when the ISO was built, so it
        # only matches the default choice. Any other branch is cloned from
        # GitHub (needs network in the live session).
        if Path("/iso-cfg").is_dir() and branch == "main":
            self._run_cmd(["cp", "-r", "/iso-cfg/.", "/mnt/etc/nixos/"])
        else:
            if Path("/iso-cfg").is_dir():
                GLib.idle_add(
                    self._log,
                    tr("Branch '{branch}' selected — cloning from GitHub (the ISO only embeds main).").format(branch=branch),
                )
            else:
                # /iso-cfg only exists inside an ISO actually built with the
                # current iso-configuration.nix (isoImage.contents embeds it).
                # Booted an older ISO, or testing outside one entirely? Fall
                # back to a plain clone — same source roudix-installer.sh used
                # before there was an ISO pipeline at all.
                GLib.idle_add(
                    self._log,
                    tr("/iso-cfg not found (ISO not (yet) rebuilt with isoImage.contents, "
                        "or testing outside an ISO) — cloning straight from GitHub instead."),
                )
            self._clone_and_checkout(repo_url, branch)

        self._verify_config_layout(branch)

        GLib.idle_add(self._set_status, tr("Detecting hardware…"), 0.5)
        # Generate into the default location then copy — same as
        # roudix-installer.sh, which does this specifically to avoid
        # stdout-capture truncation on btrfs. Manual mode already mounted
        # the real target filesystems, so this picks them up like it
        # would on physical hardware; disko modes work the same way
        # since disko has already mounted everything by this point.
        self._run_cmd(["nixos-generate-config", "--root", "/mnt"])
        hw_config = Path(f"/mnt/etc/nixos/hosts/{self.state.hostname}/hardware-configuration.nix")
        self._run_cmd(["cp", "/mnt/etc/nixos/hardware-configuration.nix", str(hw_config)])

        patched = btrfs_patch.patch_hardware_config(hw_config)
        if patched:
            GLib.idle_add(
                self._log,
                tr("btrfs detected — mount options auto-patched for: {patched}").format(patched=', '.join(patched)),
            )

        GLib.idle_add(self._set_status, tr("Generating local.nix / username.nix…"), 0.6)
        config_gen.write_config(self.state, Path("/mnt/etc/nixos"))
        GLib.idle_add(self._log, tr("hosts/{hostname}/local.nix, username.nix, home/local.nix written.").format(hostname=self.state.hostname))

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
            f"for f in hosts/{self.state.hostname}/hardware-configuration.nix hosts/{self.state.hostname}/local.nix "
            f"hosts/{self.state.hostname}/username.nix modules/home/local.nix modules/system/boot/boot.local.nix; do "
            "[ -f \"/mnt/etc/nixos/$f\" ] && git -C /mnt/etc/nixos add -f \"$f\"; "
            "done; "
            "fi",
        ])

    # ── Existing NixOS: convert in place ─────────────────────────────────

    def _log_preflight(self, facts):
        texts = {
            "boot_space": tr("Warning: only {free} MiB free in /boot ({need} MiB recommended) — "
                              "nixos-rebuild may fail on a small EFI partition."),
            "store_space": tr("Warning: only {free} GiB free for the Nix store ({need} GiB recommended)."),
            "state_version": tr("Warning: your configuration uses system.stateVersion {old}, Roudix sets {new}. "
                                 "Services that keep data (databases…) deserve a look before booting it."),
            "bootloader_change": tr("Note: Roudix will use the {new} bootloader (yours: {old}). If it ever fails to "
                                     "start, RESTORE.txt in the backup explains how to put your old configuration back."),
        }
        for key, args in existing_nixos.preflight(facts, self.state.bootloader):
            GLib.idle_add(self._log, texts[key].format(**args))

    def _install_hardware_config(self, repo: Path, host: str):
        """hosts/<host>/hardware-configuration.nix. The file that already boots this
        machine (/etc/nixos) is reused as is; only when it is missing is one generated —
        into a temp dir (`--dir`), never over /etc/nixos."""
        hw = repo / "hosts" / host / "hardware-configuration.nix"
        current = Path("/etc/nixos/hardware-configuration.nix")
        try:
            shutil.copy(current, hw)
            GLib.idle_add(self._log, tr("Reusing /etc/nixos/hardware-configuration.nix (the one that boots this machine)."))
        except OSError:
            out = tempfile.mkdtemp(prefix="roudix-hw-")
            self._run_cmd(["nixos-generate-config", "--dir", out], root=False)
            shutil.copy(Path(out) / "hardware-configuration.nix", hw)
            shutil.rmtree(out, ignore_errors=True)
        patched = btrfs_patch.patch_hardware_config(hw)
        if patched:
            GLib.idle_add(
                self._log,
                tr("btrfs detected — mount options auto-patched for: {patched}").format(patched=', '.join(patched)),
            )

    def _run_existing(self):
        s = self.state
        host = s.hostname
        cfg = existing_nixos.config_dir_for(s.username)

        GLib.idle_add(self._set_status, tr("Checking this system…"), 0.05)
        facts = existing_nixos.read_facts()
        self._log_preflight(facts)

        # ── Configuration: ~/.config/roudix, where autoupdate / nh / roudix-update look
        GLib.idle_add(self._set_status, tr("Fetching the Roudix configuration…"), 0.15)
        branch = self._resolve_branch(existing_nixos.REPO_URL, s.branch)
        s.branch = branch  # keep local.nix / autoupdate.branch and the summary in sync
        if cfg.exists():
            # Never delete anything of the user's: an earlier checkout is moved aside.
            aside = cfg.with_name(f"roudix.before-installer-{facts.date}")
            GLib.idle_add(self._log, tr("{cfg} already exists — moving it to {aside}.").format(cfg=cfg, aside=aside))
            self._run_cmd(["mv", str(cfg), str(aside)], root=False)
        cfg.parent.mkdir(parents=True, exist_ok=True)
        self._run_cmd(["git", "clone", "--branch", branch, existing_nixos.REPO_URL, str(cfg)], root=False)
        self._verify_config_layout(branch, cfg)

        GLib.idle_add(self._set_status, tr("Detecting hardware…"), 0.35)
        self._install_hardware_config(cfg, host)

        GLib.idle_add(self._set_status, tr("Generating local.nix / username.nix…"), 0.45)
        config_gen.write_config(s, cfg)
        example_text = (cfg / f"hosts/{host}/local.nix.example").read_text()
        self._log_verification(example_text, (cfg / f"hosts/{host}/local.nix").read_text())
        GLib.idle_add(self._log, tr("hosts/{hostname}/local.nix, username.nix, home/local.nix written.").format(hostname=host))
        if os.geteuid() == 0:  # started with sudo: the checkout must belong to the user
            pw = pwd.getpwnam(s.username)
            self._run_cmd(["chown", "-R", f"{pw.pw_uid}:{pw.pw_gid}", str(cfg)])

        # ── Backup, BEFORE anything touches the system
        if Path("/etc/nixos").is_dir():
            GLib.idle_add(self._set_status, tr("Backing up /etc/nixos…"), 0.55)
            dest = existing_nixos.backup_dir(facts)
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
                t.write(existing_nixos.restore_text(facts, dest))
            try:
                self._run_cmd(existing_nixos.backup_command(facts, Path(t.name)))
            finally:
                os.unlink(t.name)
            GLib.idle_add(self._log, tr("✓ backup done: {dest} (see RESTORE.txt in it).").format(dest=dest))

        # ── Build + schedule for next boot. `boot`, not `switch`: changing desktop /
        # display manager under a running session is risky, and the previous
        # generation stays in the boot menu. --no-write-lock-file: root must not
        # leave a root-owned flake.lock in the user's checkout (breaks `git pull`).
        GLib.idle_add(self._set_status, tr("Building Roudix — this can take a while…"), 0.7)
        self._run_cmd([
            "nixos-rebuild", "boot",
            "--flake", f"path:{cfg}#{host}",
            "--accept-flake-config", "--no-write-lock-file",
        ])
        GLib.idle_add(self._log, tr("✓ Roudix is built. Reboot to start it; your previous system stays in the boot menu."))

    # ── Install ───────────────────────────────────────────────────────────

    def _step_install(self):
        GLib.idle_add(self._set_status, tr("Installing the system…"), 0.75)
        self._run_cmd([
            "nixos-install",
            "--flake", f"/mnt/etc/nixos#{self.state.hostname}",
            "--no-root-passwd",
            "--option", "accept-flake-config", "true",
        ])

        if self.state.password:
            GLib.idle_add(self._set_status, tr("Setting the password…"), 0.9)
            # Sets it directly in the installed system's /etc/shadow via
            # chroot — same place any other distro's installer would put
            # it — rather than baking a password hash into the declarative
            # config that ends up committed to git.
            self._run_cmd_with_input(
                ["nixos-enter", "--root", "/mnt", "-c", "chpasswd"],
                f"{self.state.username}:{self.state.password}\n",
            )

        GLib.idle_add(self._set_status, tr("Copying config for nh os switch…"), 0.95)
        config_dir = f"/mnt/home/{self.state.username}/.config/roudix"
        self._run_cmd(["mkdir", "-p", config_dir])
        self._run_cmd(["cp", "-r", "/mnt/etc/nixos/.", config_dir])
        self._run_cmd(["chown", "-R", "1000:1000", f"/mnt/home/{self.state.username}/.config"])

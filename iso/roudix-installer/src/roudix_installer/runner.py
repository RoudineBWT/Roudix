"""
The installation itself — partition, write the config, nixos-install / nixos-rebuild.

Shared by every front-end (GTK progress page, TUI). No GTK in here: a front-end
gives two callbacks and runs `InstallRunner.run()` (blocking, so from a worker
thread when it has a main loop to keep alive):

    log(text)                 one line for the log view
    status(label, fraction)   headline + progress bar (0.0 .. 1.0)

Both are called from whichever thread runs `run()`: a GTK front-end must hop to
its main loop (GLib.idle_add) inside its callbacks.
"""
import os
import pwd
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from roudix_installer import btrfs_patch, config_gen, disko_gen, existing_nixos, host_profile
from roudix_installer.i18n import tr


def classify_line(text: str) -> Optional[str]:
    """"cmd" | "error" | "success" | None — how a front-end may colour a log line."""
    stripped = text.strip()
    if stripped.startswith("$ "):
        return "cmd"
    lowered = stripped.lower()
    if lowered.startswith(("erreur", "error")) or "traceback" in lowered:
        return "error"
    if "🎉" in stripped or "✓" in stripped:
        return "success"
    return None


class InstallRunner:
    def __init__(self, state, log: Callable[[str], None],
                 status: Callable[[str, float], None], use_pkexec: bool = True):
        """`use_pkexec`: on an installed NixOS, ask for the password through polkit
        (a graphical session). A terminal front-end passes False and gets `sudo`,
        after having cached the credentials itself (`sudo -v`)."""
        self.state = state
        self.log = log
        self.status = status
        self.use_pkexec = use_pkexec
        self.existing = state.mode == existing_nixos.MODE_EXISTING

    # ── Entry point ───────────────────────────────────────────────────────

    def run(self) -> bool:
        """The whole install, or the simulation. Never raises: a failure is logged,
        shown through status() and reported by the return value."""
        dry = self.is_dry_run()
        try:
            # Before anything destructive (partitioning): the username/hostname reach
            # root shell commands, chpasswd input and generated Nix files.
            config_gen.check_identity(self.state)
            if dry:
                (self._dry_run_existing if self.existing else self._dry_run)()
                return True
            if self.existing:
                self._run_existing()
            else:
                self._step_partition()
                self._step_config()
                self._step_install()
            self.status(tr("Installation complete 🎉"), 1.0)
            return True
        except Exception as exc:  # noqa: BLE001
            self.log(tr("Error") + f": {exc}")
            self.status(tr("Simulation failed") if dry else tr("Installation failed"), 0.0)
            return False

    def priv(self, cmd: list[str], root: bool = True) -> list[str]:
        """
        Run `cmd` as root when `root` is set. Already root -> as is.
          * live ISO: the autostart .desktop entry launches the installer through
            `sudo --preserve-env`, so this is a no-op there; as the plain live user
            (`nix run`) `sudo -n` works because the live user has passwordless sudo.
          * installed NixOS, graphical: `sudo -n` would just fail (password needed, no
            tty), so use pkexec (polkit shows the usual password dialog).
          * installed NixOS, terminal: sudo, with credentials cached beforehand.
        `env PATH=…` because both pkexec and sudo reset the environment, and
        nixos-rebuild needs `nix`/`git` (and the wrapper's disko…) in PATH.
        """
        if not root or os.geteuid() == 0:
            return cmd
        path = f"PATH={os.environ.get('PATH', '')}"
        if self.existing and self.use_pkexec and shutil.which("pkexec"):
            return ["pkexec", "env", path] + cmd
        return ["sudo", "-n", "env", path] + cmd

    # ── Dry run ("Simulate", or ROUDIX_INSTALLER_DRY_RUN=1) ───────────────

    def is_dry_run(self) -> bool:
        return bool(self.state.dry_run or os.environ.get("ROUDIX_INSTALLER_DRY_RUN"))

    def _report_config(self, root: Path, host: str, example_text: str):
        """Log what write_config() produced: diff vs the example, the verification
        of every written option, then the full file."""
        import difflib

        result = (root / f"hosts/{host}/local.nix").read_text()
        username = (root / f"hosts/{host}/username.nix").read_text().strip()
        self.log(f"[dry-run] hosts/{host}/username.nix = {username}")
        self.log(f"[dry-run] hosts/{host}/local.nix — lines changed vs local.nix.example:")
        changed = [l for l in difflib.unified_diff(example_text.splitlines(), result.splitlines(),
                                                   "local.nix.example", "local.nix", n=0, lineterm="")
                   if not l.startswith(("---", "+++", "@@"))]
        for line in changed or ["(none)"]:
            self.log(line)
        self._log_verification(example_text, result)
        self.log(f"[dry-run] hosts/{host}/local.nix — full result:")
        for line in result.splitlines():
            self.log(line)

    def _log_verification(self, example_text: str, result_text: str):
        """Same safety net as the old bash installer's check_opt(): a substitution
        that did not match is a silent no-op, so check the values landed."""
        missing = config_gen.verify_local_nix(self.state, example_text, result_text)
        if missing:
            self.log(tr("Warning: these options were NOT confirmed in local.nix — "
                                          "review the file before rebooting: {keys}").format(keys=", ".join(missing)))
        else:
            self.log(tr("✓ every chosen option was written to local.nix."))

    def _dry_run(self):
        """Never partition, mount or install — only generate the config the wizard
        *would* write (into a temp dir) and show it, so the wizard can be checked
        on a normal desktop."""
        import tempfile

        host = self.state.hostname
        self.status(tr("Dry run — nothing is written to disk"), 0.5)
        src = host_profile.find_config_root(host)
        if src is None:
            raise RuntimeError(tr("hosts/{host}/local.nix.example not found (try ROUDIX_CFG_ROOT=<path to the repo>)").format(host=host))
        self.log(f"[dry-run] host={host}  branch={self.state.branch}  config from {src}")
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
        self.status(tr("Dry run finished — nothing was changed"), 1.0)

    def _dry_run_existing(self):
        """Simulation on an installed NixOS: fetch the config into a temp dir, run
        the same generation as the real run, then make Nix *evaluate* the whole
        system (what `just check` does). Catches an option combination that does
        not build, without touching /etc/nixos, ~/.config or the bootloader."""
        s = self.state
        host = s.hostname
        self.status(tr("Simulation — nothing is written"), 0.05)
        facts = existing_nixos.read_facts()
        self._log_preflight(facts)

        with tempfile.TemporaryDirectory(prefix="roudix-dry-run-") as tmp:
            repo = Path(tmp) / "roudix"
            self.status(tr("Fetching the Roudix configuration…"), 0.2)
            branch = self._resolve_branch(existing_nixos.REPO_URL, s.branch)
            s.branch = branch
            try:
                self._run_cmd(["git", "clone", "--depth", "1", "--branch", branch,
                               existing_nixos.REPO_URL, str(repo)], root=False)
            except RuntimeError:
                src = host_profile.find_config_root(host)
                if src is None:
                    raise
                self.log(tr("Clone failed — simulating with the local copy of the profiles."))
                shutil.copytree(src, repo, ignore=shutil.ignore_patterns(".git"))
            self._verify_config_layout(branch, repo)

            self.status(tr("Detecting hardware…"), 0.35)
            self._install_hardware_config(repo, host)

            self.status(tr("Generating local.nix / username.nix…"), 0.45)
            config_gen.write_config(s, repo)
            example_text = (repo / f"hosts/{host}/local.nix.example").read_text()
            self._report_config(repo, host, example_text)

            self.status(tr("Evaluating the whole system with Nix…"), 0.6)
            self._run_cmd([
                "nix", "--extra-experimental-features", "nix-command flakes",
                "eval", "--raw", "--accept-flake-config", "--no-write-lock-file",
                f"path:{repo}#nixosConfigurations.{host}.config.system.build.toplevel.drvPath",
            ], root=False)
            self.log(tr("✓ the configuration evaluates: Nix can build this system."))
        self.status(tr("Simulation finished — nothing was changed"), 1.0)

    def _run_cmd(self, cmd: list[str], root: bool = True):
        full = self.priv(cmd, root)
        shown = full[:1] + cmd if full[:1] in (["pkexec"], ["sudo"]) else cmd  # no env/-n noise in the log
        self.log(f"$ {' '.join(shown)}")
        proc = subprocess.Popen(
            full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            # Without this, a child reading stdin (waiting for input a GUI
            # app can never provide) hangs forever instead of failing fast —
            # gets EOF immediately instead.
            stdin=subprocess.DEVNULL,
        )
        for line in proc.stdout:
            self.log(line.rstrip())
        proc.wait()
        if full[:1] == ["pkexec"] and proc.returncode in (126, 127):
            raise RuntimeError(tr("Authentication was cancelled or refused."))
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd[0]} " + tr("failed") + f" (code {proc.returncode})")

    def _run_cmd_with_input(self, cmd: list[str], input_text: str):
        """Like _run_cmd, but actually feeds stdin — for chpasswd."""
        full = self.priv(cmd)
        self.log(f"$ {' '.join(cmd)}")  # never log input_text
        proc = subprocess.run(full, input=input_text, capture_output=True, text=True)
        if proc.stdout:
            self.log(proc.stdout.rstrip())
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
        self.status(tr("Partitioning the disk…"), 0.15)
        disko_nix = disko_gen.generate(self.state.disk)
        # mkdtemp → private (0700) dir, no predictable /tmp path another process could pre-create
        disko_dir = Path(tempfile.mkdtemp(prefix="roudix-disko-"))
        try:
            disko_file = disko_dir / "roudix-disko.nix"
            disko_file.write_text(disko_nix)
            self._run_cmd(["disko", "--mode", "disko", str(disko_file)])
        finally:
            shutil.rmtree(disko_dir, ignore_errors=True)

    def _partition_manual(self):
        """
        Partitions were already made by hand in GParted. We just mount them
        in the right order — root first, then boot, then swap — same result
        as Calamares' manual partitioning, but via plain mount(8).
        """
        self.status(tr("Mounting partitions…"), 0.2)
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
        self.log(tr("Checking branch '{branch}'…").format(branch=branch))
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
            self.log(tr("Branch '{branch}' not found on {repo_url} — falling back to 'main'.").format(branch=branch, repo_url=repo_url),
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
            self.log(tr("Warning: hosts/{host}/local.nix.example not found on branch '{branch}' — local.nix generation may fail.").format(host=host, branch=branch),
            )

    def _step_config(self):
        self.status(tr("Copying the configuration…"), 0.4)
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
                self.log(tr("Branch '{branch}' selected — cloning from GitHub (the ISO only embeds main).").format(branch=branch),
                )
            else:
                # /iso-cfg only exists inside an ISO actually built with the
                # current iso-configuration.nix (isoImage.contents embeds it).
                # Booted an older ISO, or testing outside one entirely? Fall
                # back to a plain clone — same source the old bash installer used
                # before there was an ISO pipeline at all.
                self.log(tr("/iso-cfg not found (ISO not (yet) rebuilt with isoImage.contents, "
                        "or testing outside an ISO) — cloning straight from GitHub instead."),
                )
            self._clone_and_checkout(repo_url, branch)

        self._verify_config_layout(branch)

        self.status(tr("Detecting hardware…"), 0.5)
        # Generate into the default location then copy — same as
        # the old bash installer, which does this specifically to avoid
        # stdout-capture truncation on btrfs. Manual mode already mounted
        # the real target filesystems, so this picks them up like it
        # would on physical hardware; disko modes work the same way
        # since disko has already mounted everything by this point.
        self._run_cmd(["nixos-generate-config", "--root", "/mnt"])
        hw_config = Path(f"/mnt/etc/nixos/hosts/{self.state.hostname}/hardware-configuration.nix")
        self._run_cmd(["cp", "/mnt/etc/nixos/hardware-configuration.nix", str(hw_config)])

        patched = btrfs_patch.patch_hardware_config(hw_config)
        if patched:
            self.log(tr("btrfs detected — mount options auto-patched for: {patched}").format(patched=', '.join(patched)),
            )

        self.status(tr("Generating local.nix / username.nix…"), 0.6)
        config_gen.write_config(self.state, Path("/mnt/etc/nixos"))
        self.log(tr("hosts/{hostname}/local.nix, username.nix, home/local.nix written.").format(hostname=self.state.hostname))

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
            self.log(texts[key].format(**args))

    def _install_hardware_config(self, repo: Path, host: str):
        """hosts/<host>/hardware-configuration.nix. The file that already boots this
        machine (/etc/nixos) is reused as is; only when it is missing is one generated —
        into a temp dir (`--dir`), never over /etc/nixos."""
        hw = repo / "hosts" / host / "hardware-configuration.nix"
        current = Path("/etc/nixos/hardware-configuration.nix")
        try:
            shutil.copy(current, hw)
            self.log(tr("Reusing /etc/nixos/hardware-configuration.nix (the one that boots this machine)."))
        except OSError:
            out = tempfile.mkdtemp(prefix="roudix-hw-")
            self._run_cmd(["nixos-generate-config", "--dir", out], root=False)
            shutil.copy(Path(out) / "hardware-configuration.nix", hw)
            shutil.rmtree(out, ignore_errors=True)
        patched = btrfs_patch.patch_hardware_config(hw)
        if patched:
            self.log(tr("btrfs detected — mount options auto-patched for: {patched}").format(patched=', '.join(patched)),
            )

    def _run_existing(self):
        s = self.state
        host = s.hostname
        cfg = existing_nixos.config_dir_for(s.username)

        self.status(tr("Checking this system…"), 0.05)
        facts = existing_nixos.read_facts()
        self._log_preflight(facts)

        # ── Configuration: ~/.config/roudix, where autoupdate / nh / roudix-update look
        self.status(tr("Fetching the Roudix configuration…"), 0.15)
        branch = self._resolve_branch(existing_nixos.REPO_URL, s.branch)
        s.branch = branch  # keep local.nix / autoupdate.branch and the summary in sync
        if cfg.exists():
            # Never delete anything of the user's: an earlier checkout is moved aside.
            aside = cfg.with_name(f"roudix.before-installer-{facts.date}")
            self.log(tr("{cfg} already exists — moving it to {aside}.").format(cfg=cfg, aside=aside))
            self._run_cmd(["mv", str(cfg), str(aside)], root=False)
        cfg.parent.mkdir(parents=True, exist_ok=True)
        self._run_cmd(["git", "clone", "--branch", branch, existing_nixos.REPO_URL, str(cfg)], root=False)
        self._verify_config_layout(branch, cfg)

        self.status(tr("Detecting hardware…"), 0.35)
        self._install_hardware_config(cfg, host)

        self.status(tr("Generating local.nix / username.nix…"), 0.45)
        config_gen.write_config(s, cfg)
        example_text = (cfg / f"hosts/{host}/local.nix.example").read_text()
        self._log_verification(example_text, (cfg / f"hosts/{host}/local.nix").read_text())
        self.log(tr("hosts/{hostname}/local.nix, username.nix, home/local.nix written.").format(hostname=host))
        if os.geteuid() == 0:  # started with sudo: the checkout must belong to the user
            pw = pwd.getpwnam(s.username)
            self._run_cmd(["chown", "-R", f"{pw.pw_uid}:{pw.pw_gid}", str(cfg)])

        # ── Backup, BEFORE anything touches the system
        if Path("/etc/nixos").is_dir():
            self.status(tr("Backing up /etc/nixos…"), 0.55)
            dest = existing_nixos.backup_dir(facts)
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
                t.write(existing_nixos.restore_text(facts, dest))
            try:
                self._run_cmd(existing_nixos.backup_command(facts, Path(t.name)))
            finally:
                os.unlink(t.name)
            self.log(tr("✓ backup done: {dest} (see RESTORE.txt in it).").format(dest=dest))

        # ── Build + schedule for next boot. `boot`, not `switch`: changing desktop /
        # display manager under a running session is risky, and the previous
        # generation stays in the boot menu. --no-write-lock-file: root must not
        # leave a root-owned flake.lock in the user's checkout (breaks `git pull`).
        self.status(tr("Building Roudix — this can take a while…"), 0.7)
        self._run_cmd([
            "nixos-rebuild", "boot",
            "--flake", f"path:{cfg}#{host}",
            "--accept-flake-config", "--no-write-lock-file",
        ])
        self.log(tr("✓ Roudix is built. Reboot to start it; your previous system stays in the boot menu."))

    # ── Install ───────────────────────────────────────────────────────────

    def _step_install(self):
        self.status(tr("Installing the system…"), 0.75)
        self._run_cmd([
            "nixos-install",
            "--flake", f"/mnt/etc/nixos#{self.state.hostname}",
            "--no-root-passwd",
            "--option", "accept-flake-config", "true",
        ])

        if self.state.password:
            self.status(tr("Setting the password…"), 0.9)
            # Sets it directly in the installed system's /etc/shadow via
            # chroot — same place any other distro's installer would put
            # it — rather than baking a password hash into the declarative
            # config that ends up committed to git.
            self._run_cmd_with_input(
                ["nixos-enter", "--root", "/mnt", "-c", "chpasswd"],
                f"{self.state.username}:{self.state.password}\n",
            )

        self.status(tr("Copying config for nh os switch…"), 0.95)
        config_dir = f"/mnt/home/{self.state.username}/.config/roudix"
        self._run_cmd(["mkdir", "-p", config_dir])
        self._run_cmd(["cp", "-r", "/mnt/etc/nixos/.", config_dir])
        self._run_cmd(["chown", "-R", "1000:1000", f"/mnt/home/{self.state.username}/.config"])

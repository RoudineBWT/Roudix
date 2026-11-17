"""
Terminal front-end of the installer — what `roudix-installer.sh` used to be.

Plain prompts on stdin/stdout, standard library only: it works on a bare TTY, over
SSH, on a serial console and on a machine where GTK is not installed (nothing in
here, nor in the modules it imports, imports `gi`). Same wizard as the GTK one:

    language -> profile -> [disk] -> user -> options -> summary -> install

The questions come from questions.py, the lists of choices from choices.py, the
summary from summary_rows.py and the install itself from runner.py: the two
front-ends differ only in how they ask.

Answers are never lost on a typo: Enter keeps the default shown in [brackets],
a number picks from a list, text filters a long list. After the summary you can
go back over every option ("Edit the options") with the answers as defaults.
"""
import getpass
import os
import re
import shutil
import subprocess
import sys
from typing import Callable, Optional

try:   # line editing for input(); also makes the prompt markers in Console._styled_prompt effective
    import readline  # noqa: F401
except ImportError:
    pass

try:   # raw key reading for the arrow-key lists (POSIX terminals only)
    import select
    import termios
    import tty
except ImportError:   # pragma: no cover
    termios = None

import unicodedata

from roudix_installer import existing_nixos, host_profile, i18n, multiboot, questions
from roudix_installer.choices import host_label, host_note, welcome_text
from roudix_installer.disks import MOUNTPOINT_VALUES, list_disks, list_partitions
from roudix_installer.hardware_detect import is_bios_boot
from roudix_installer.i18n import tr, trc
from roudix_installer.runner import InstallRunner, classify_line
from roudix_installer.state import InstallState, valid_username
from roudix_installer.summary_rows import summary_rows

# The Linux virtual console cannot draw most scripts or symbols: offer the languages
# it can, and replace the few symbols the texts use.
_CONSOLE_LANGS = ("en", "fr", "es", "pt_BR")
_CONSOLE_SYMBOLS = {"✓": "[ok]", "⚠": "[!]", "🎉": "", "→": "->", "—": "-", "…": "...", "“": '"', "”": '"',
                    "’": "'", "·": "-", "›": ">"}
_YES = {"y", "yes", "o", "oui", "s", "si", "sí", "sim", "j", "ja", "1"}
_NO = {"n", "no", "non", "nao", "não", "nein", "0"}


class Aborted(Exception):
    """The user quit (Ctrl-C, Ctrl-D, or chose to)."""


class Console:
    """Everything that reads or writes the terminal — replaceable in tests."""

    def __init__(self, input_fn: Optional[Callable] = None, secret_fn: Optional[Callable] = None,
                 out=None, color: Optional[bool] = None):
        self._input = input_fn or input
        self._secret = secret_fn or getpass.getpass
        self.out = out or sys.stdout
        isatty = getattr(self.out, "isatty", lambda: False)()
        self.color = (isatty and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
                      if color is None else color)
        self.vt = os.environ.get("TERM") == "linux"   # kernel virtual console

    # ── output ──
    def _fmt(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color and code else text

    def say(self, text: str = "", style: str = ""):
        if self.vt:
            for sym, rep in _CONSOLE_SYMBOLS.items():
                text = text.replace(sym, rep)
        codes = {"bold": "1", "dim": "2", "red": "1;31", "green": "1;32", "yellow": "33", "blue": "1;34",
                 "cyan": "36"}
        print(self._fmt(text, codes.get(style, "")), file=self.out, flush=True)

    def heading(self, text: str):
        self.say()
        self.say(f"══ {text} ══", "cyan")

    def note(self, text: str):
        self.say(f"  {text}", "dim")

    # ── input ──
    def _styled_prompt(self, prompt: str) -> str:
        """Bold prompt. With GNU readline (the builtin input() on a tty) the escape codes must be
        wrapped in \\001…\\002 so it does not count them as printable characters: otherwise it
        mis-measures the line and redraws garbage in front of the prompt (a stray "oldm")."""
        if not self.color:
            return prompt
        if self._input is input and "readline" in sys.modules:
            return f"\001\033[1m\002{prompt}\001\033[0m\002"
        return self._fmt(prompt, "bold")

    def ask(self, prompt: str) -> str:
        try:
            if self.vt:
                for sym, rep in _CONSOLE_SYMBOLS.items():
                    prompt = prompt.replace(sym, rep)
            return self._input(self._styled_prompt(prompt)).strip()
        except (EOFError, KeyboardInterrupt):
            print(file=self.out)
            raise Aborted

    def secret(self, prompt: str) -> str:
        try:
            return self._secret(prompt)
        except (EOFError, KeyboardInterrupt):
            print(file=self.out)
            raise Aborted

    # ── arrow-key lists ──
    def arrows_ok(self) -> bool:
        """Arrow keys only on the real terminal: not with a scripted input (tests), a pipe,
        a dumb terminal, or where termios is missing. Everything else keeps the numbered prompt."""
        return bool(termios and self._input is input and self.out is sys.stdout
                    and sys.stdin.isatty() and sys.stdout.isatty()
                    and os.environ.get("TERM", "dumb") != "dumb"
                    and os.environ.get("ROUDIX_INSTALLER_NO_ARROWS") is None)

    @staticmethod
    def _read_key() -> str:
        """One key from the terminal (already in cbreak mode): 'up', 'down', 'home', 'end',
        'enter', or the character typed; "" for anything else."""
        fd = sys.stdin.fileno()
        data = os.read(fd, 1)
        if data == b"\x1b":
            while select.select([fd], [], [], 0.05)[0]:   # the rest of an escape sequence
                data += os.read(fd, 1)
                if (len(data) > 2 and data[-1:].isalpha()) or data[-1:] == b"~":
                    break
        else:   # a multi-byte UTF-8 character
            first = data[:1]
            need = 3 if first >= b"\xf0" else 2 if first >= b"\xe0" else 1 if first >= b"\xc0" else 0
            while need:
                data += os.read(fd, 1)
                need -= 1
        if data == b"\x03":
            raise KeyboardInterrupt
        if data in (b"\x04", b""):
            raise EOFError
        if data in (b"\r", b"\n"):
            return "enter"
        keys = {b"\x1b[A": "up", b"\x1bOA": "up", b"\x1b[B": "down", b"\x1bOB": "down",
                b"\x1b[H": "home", b"\x1b[1~": "home", b"\x1bOH": "home",
                b"\x1b[F": "end", b"\x1b[4~": "end", b"\x1bOF": "end"}
        if data in keys:
            return keys[data]
        if data[:1] == b"\x1b":
            return ""
        return data.decode("utf-8", "replace")

    @staticmethod
    def _clip(text: str, width: int) -> str:
        """Cut `text` to `width` terminal cells (wide CJK characters count for two)."""
        out, used = [], 0
        for ch in text:
            w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 0 if unicodedata.combining(ch) else 1
            if used + w > width:
                break
            out.append(ch)
            used += w
        return "".join(out)

    def _list_lines(self, active: list, cursor: int, default) -> list:
        width = max(20, shutil.get_terminal_size((80, 24)).columns - 1)
        lines = []
        for i, (value, label) in enumerate(active):
            mark = ">" if i == cursor else "*" if value == default else " "
            text = self._clip(f" {mark}{i + 1:>2}) {label}", width)
            if self.vt:
                for sym, rep in _CONSOLE_SYMBOLS.items():
                    text = text.replace(sym, rep)
            lines.append(self._fmt(text, "1;32" if i == cursor else "32" if value == default else ""))
        return lines

    def _pick_arrows(self, active: list, default, prompt: str):
        """Up/Down move the highlight, Enter picks it, Home/End jump. A digit or a letter
        switches to the usual line prompt with that character already typed, so numbers and
        the filter work as before. Returns ("index", i) or ("text", raw)."""
        cursor = next((i for i, (v, _) in enumerate(active) if v == default), 0)
        out = self.out
        drawn = 0
        label = "  " + prompt.rstrip(": ") + " \u2191\u2193: "
        if self.vt:
            label = label.replace("\u2191\u2193", "up/down")
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)   # keys arrive one by one and are not echoed
            while True:
                if drawn:
                    out.write(f"\033[{drawn}A\r\033[J")
                lines = self._list_lines(active, cursor, default)
                out.write("\n".join(lines) + "\n" + self._fmt(label, "1"))
                out.flush()
                drawn = len(lines)
                key = self._read_key()
                if key == "up":
                    cursor = (cursor - 1) % len(active)
                elif key == "down":
                    cursor = (cursor + 1) % len(active)
                elif key == "home":
                    cursor = 0
                elif key == "end":
                    cursor = len(active) - 1
                elif key == "enter":
                    out.write(f"\r\033[K{self._fmt(label, '1')}{cursor + 1}\n")
                    out.flush()
                    return ("index", cursor)
                elif key and key.isprintable() and not key.isspace():
                    # Typed text: the same prompt as without arrows, first character already in.
                    termios.tcsetattr(fd, termios.TCSADRAIN, saved)
                    out.write("\r\033[K")
                    out.flush()
                    readline.set_startup_hook(lambda: (readline.insert_text(key), readline.redisplay()))
                    try:
                        raw = input(self._styled_prompt("  " + prompt)).strip()
                    finally:
                        readline.set_startup_hook(None)
                    return ("text", raw)
        except (EOFError, KeyboardInterrupt):
            print(file=out)
            raise Aborted
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)

    def choice(self, title: str, pairs: list, default=None, hint: str = ""):
        """Pick one value of [(value, label)]. Arrow keys + Enter, or a number, or any other
        text to filter the list (long lists). Enter alone = the default. Returns the value."""
        active = list(pairs)
        self.say()
        self.say(title, "bold")
        if hint:
            self.note(hint)
        arrows = self.arrows_ok() and "readline" in sys.modules
        while True:
            shown_default = next((i for i, (v, _) in enumerate(active, 1) if v == default), None)
            filter_hint = tr(" or type to filter") if len(pairs) > 9 else ""
            prompt = tr("Choice") + (f" [{shown_default}]" if shown_default else "") + filter_hint + ": "
            if arrows:
                kind, picked = self._pick_arrows(active, default, prompt)
                if kind == "index":
                    return active[picked][0]
                raw = picked
            else:
                for i, (value, label) in enumerate(active, 1):
                    mark = "*" if value == default else " "
                    self.say(f" {mark}{i:>2}) {label}", "green" if value == default else "")
                raw = self.ask("  " + prompt)
            if not raw:
                if shown_default:
                    return default
                self.say(tr("Choose one of the entries."), "red")
            elif raw.isdigit():
                if 1 <= int(raw) <= len(active):
                    return active[int(raw) - 1][0]
                self.say(tr("Out of range."), "red")
            else:
                needle = raw.lower()
                found = [(v, l) for v, l in pairs if needle in f"{v} {l}".lower()]
                if not found:
                    self.say(tr("No match."), "red")
                elif len(found) == 1:
                    return found[0][0]
                else:
                    active = found

    def yes_no(self, title: str, default: bool, hint: str = "") -> bool:
        if hint:
            self.note(hint)
        suffix = trc("yes/no prompt, yes is the default", "[Y/n]") if default \
            else trc("yes/no prompt, no is the default", "[y/N]")
        while True:
            raw = self.ask(f"{title} {suffix} ").lower()
            if not raw:
                return default
            if raw in _YES:
                return True
            if raw in _NO:
                return False
            self.say(tr("Answer yes or no."), "red")

    def text(self, title: str, default: str = "", validate: Optional[Callable] = None, hint: str = "") -> str:
        if hint:
            self.note(hint)
        while True:
            raw = self.ask(f"{title}" + (f" [{default}]" if default else "") + ": ")
            value = raw if raw else default
            error = validate(value) if validate else None
            if not error:
                return value
            self.say(error, "red")

    def text_list(self, title: str, default: list, validate: Optional[Callable] = None) -> list:
        def parse(s):
            return [p.strip() for p in s.split(",") if p.strip()]
        shown = ", ".join(default)
        while True:
            raw = self.ask(f"{title}" + (f" [{shown}]" if shown else "") + ": ")
            value = parse(raw) if raw else list(default)
            if raw == "-":      # explicit "nothing"
                value = []
            error = validate(value) if validate else None
            if not error:
                return value
            self.say(error, "red")

    def checklist(self, title: str, items: list) -> dict:
        """items: [(key, label, checked)] -> {key: bool}. Numbers toggle, Enter validates."""
        state = {k: bool(c) for k, _l, c in items}
        self.say()
        self.say(title, "bold")
        while True:
            for i, (key, label, _c) in enumerate(items, 1):
                on = state[key]
                self.say(f"  [{'x' if on else ' '}] {i:>2}) {label}", "green" if on else "")
            raw = self.ask("  " + tr("Toggle: numbers separated by spaces, a = all, n = none, Enter = continue") + ": ")
            if not raw:
                return state
            for tok in raw.replace(",", " ").split():
                if tok.lower() == "a":
                    state = {k: True for k in state}
                elif tok.lower() == "n":
                    state = {k: False for k in state}
                elif tok.isdigit() and 1 <= int(tok) <= len(items):
                    key = items[int(tok) - 1][0]
                    state[key] = not state[key]
                else:
                    self.say(tr("Out of range.") + f" ({tok})", "red")


# ── Steps ─────────────────────────────────────────────────────────────────

def choose_language(con: Console, lang: Optional[str] = None):
    langs = list(i18n.LANGUAGES)
    if con.vt:
        langs = [l for l in langs if l[0] in _CONSOLE_LANGS]
    codes = [c for c, _n, _p in langs]
    if lang in {c for c, _n, _p in i18n.LANGUAGES}:
        i18n.set_lang(lang)
        return
    con.say(" · ".join(p for _c, _n, p in langs))
    pairs = [(c, n) for c, n, _p in langs]
    i18n.set_lang(con.choice("\N{GLOBE WITH MERIDIANS}", pairs, default=i18n.LANG if i18n.LANG in codes else codes[0]))


def choose_host(con: Console, state: InstallState):
    hosts = host_profile.available_hosts()
    if state.hostname not in hosts:
        state.hostname = hosts[0]
    if len(hosts) > 1:
        state.hostname = con.choice(tr("Profile to install"), [(h, host_label(h)) for h in hosts],
                                    default=state.hostname)
    con.note(host_note(state.hostname))


def ensure_privileges(con: Console) -> bool:
    """Root, or `sudo` credentials cached now (the install runs unattended afterwards)."""
    if os.geteuid() == 0:
        return True
    if not shutil.which("sudo"):
        con.say(tr("Administrator rights are needed and sudo is not available: run the installer as root."), "red")
        return False
    con.say(tr("Administrator rights are needed: enter your password if asked."))
    return subprocess.run(["sudo", "-v"]).returncode == 0


def _disk_label(d: dict) -> str:
    return f"{d['path']} — {d['model']} ({d['size']})"


def step_disk(con: Console, state: InstallState):
    disk = state.disk
    disk.bios = is_bios_boot()
    con.heading(tr("Disk"))
    disk.mode = con.choice(tr("Partitioning mode"), [
        ("simple", tr("Simple (EFI + swap + root, wipes everything)")),
        ("advanced", tr("Advanced (custom disko.nix file)")),
        ("manual", tr("Manual (partition it yourself)")),
    ], default=disk.mode)
    try:
        disks = list_disks()
    except Exception:  # noqa: BLE001 — no lsblk: say so below
        disks = []
    if not disks:
        raise RuntimeError(tr("No disk found."))
    disk_pairs = [(d["path"], _disk_label(d)) for d in disks]

    if disk.mode == "simple":
        con.say(tr("⚠ The selected disk will be completely wiped (simple mode)"), "yellow")
        disk.device = con.choice(tr("Choose a disk"), disk_pairs, default=disk.device or None)
        disk.filesystem = con.choice(tr("Filesystem"), [
            ("ext4", tr("ext4 (simple)")),
            ("btrfs", tr("btrfs (@, @home, @nix, @log subvolumes + zstd)")),
        ], default=disk.filesystem)
        disk.boot_size_gb = _ask_int(con, tr("/boot size (GB)"), disk.boot_size_gb, 2, 16,
                                     hint=tr("4G recommended with CachyOS + multiple Limine generations — 2G minimum"))
        disk.enable_swap = con.yes_no(tr("Add a swap partition"), disk.enable_swap,
                                      hint=tr("Off by default — zram already covers this"))
        if disk.enable_swap:
            disk.swap_size_gb = _ask_int(con, tr("Swap size (GB)"), disk.swap_size_gb, 1, 64)
    elif disk.mode == "advanced":
        disk.advanced_disko_path = con.text(
            tr("Select a disko.nix"), disk.advanced_disko_path,
            validate=lambda p: None if os.path.isfile(os.path.expanduser(p)) else tr("File not found."))
        disk.advanced_disko_path = os.path.expanduser(disk.advanced_disko_path)
    else:
        _manual_partitions(con, state, disks, disk_pairs)

    if disk.bios and disk.mode != "simple":
        # Legacy BIOS: Limine goes on the disk itself, whatever the partitioning mode.
        disk.device = con.choice(tr("Disk to partition"), disk_pairs, default=disk.device or None)


def _ask_int(con: Console, title: str, default: int, lo: int, hi: int, hint: str = "") -> int:
    def check(v):
        return None if re.fullmatch(r"\d+", str(v)) and lo <= int(v) <= hi else f"{lo}-{hi}"
    return int(con.text(title, str(default), validate=check, hint=hint))


def _manual_partitions(con: Console, state: InstallState, disks: list, disk_pairs: list):
    disk = state.disk
    dev = con.choice(tr("Disk to partition"), disk_pairs, default=disk_pairs[0][0])
    labels = [("skip", tr("Skip")), ("/", "/"), ("/boot", tr("/boot (EFI)")), ("swap", tr("swap"))]
    assert [m for m in MOUNTPOINT_VALUES] == [None, "/", "/boot", "swap"]
    while True:
        try:
            parts = list_partitions(dev)
        except Exception:  # noqa: BLE001
            parts = []
        if parts:
            break
        con.say(tr("Partition it yourself in another terminal (cfdisk, fdisk, parted…), then press Enter."))
        con.ask("  ")
    con.say(tr("Once partitioning is done, assign each partition to a mountpoint."))
    mapping = {}
    for p in parts:
        mp = con.choice(f"{p['path']} — {p['fstype']} ({p['size']})", labels, default="skip")
        if mp != "skip":
            mapping[p["path"]] = mp
    if "/" not in mapping.values():
        con.say(tr("No partition assigned to / — cannot continue"), "red")
        return _manual_partitions(con, state, disks, disk_pairs)
    disk.manual_partitions = mapping
    disk.device = dev


def step_user(con: Console, state: InstallState):
    con.heading(tr("User"))
    if state.mode == existing_nixos.MODE_EXISTING:
        # The account exists and keeps its password.
        state.password = ""
        if not existing_nixos.user_exists(state.username):
            raise RuntimeError(tr("This user doesn't exist on this system — run the installer from the account you want to keep."))
        con.say(f"{tr('Username')}: {state.username}")
        return
    state.username = con.text(
        tr("Username"), state.username,
        validate=lambda v: None if valid_username(v) else
        tr("Invalid username: use letters, digits, '_', '-' or '.', starting with a letter or '_' (max 32)."))
    while True:
        pw = con.secret(tr("Password") + ": ")
        if not pw:
            con.say(tr("Password can't be empty."), "red")
            continue
        if pw != con.secret(tr("Confirm password") + ": "):
            con.say(tr("Passwords don't match."), "red")
            continue
        state.password = pw
        return


def step_other_systems(con: Console, state: InstallState, ctx: questions.Ctx):
    """Other systems found in the firmware boot menu, offered to Limine (efibootmgr)."""
    if (state.bootloader != "limine" or ctx.bios
            or not questions.in_profile(("roudix.boot.bootloader",), ctx)):
        state.other_os = []
        return
    found = multiboot.detect()
    if not found:
        state.other_os = []
        return
    previous = {tuple(e) for e in state.other_os}
    items = [(i, f"{e.label} — {e.partuuid} {e.efi_path}", tuple(e) in previous) for i, e in enumerate(found)]
    picked = con.checklist(tr("Other systems found in the EFI NVRAM — which ones do you want to add to Limine?"), items)
    state.other_os = [tuple(found[i]) for i, on in picked.items() if on]


def ask_options(con: Console, state: InstallState, ctx: questions.Ctx):
    """Walk every question; the answers already in `state` are the defaults."""
    section = None
    ctx.asked.clear()
    for q in questions.build():
        if not questions.applicable(q, state, ctx):
            continue
        if q.force:
            forced = q.force(state, ctx)
            if forced is questions.SKIP:
                continue
            if forced is not None:
                q.store(state, forced)
                if q.note:
                    con.note(f"{q.title_text(state)}: {q.note(state, ctx)}")
                continue
        if q.section != section:
            section = q.section
            con.heading(tr(section))
        ctx.asked.add(q.id)
        title = q.title_text(state)
        hint = tr(q.hint) if q.hint else ""
        if q.kind == "choice":
            pairs = q.choices(state, ctx)
            current = q.current(state, ctx)
            q.store(state, con.choice(title, pairs, default=current if current in [v for v, _ in pairs] else pairs[0][0],
                                      hint=hint))
        elif q.kind == "bool":
            q.store(state, con.yes_no(title, bool(q.current(state, ctx)), hint=hint))
        elif q.kind == "text":
            default = q.default(state, ctx) if q.default else q.current(state, ctx)
            q.store(state, con.text(title, default, validate=q.validate, hint=hint).strip())
        elif q.kind == "list":
            q.store(state, con.text_list(title, list(q.current(state, ctx)), validate=q.validate))
        elif q.kind == "multi":
            items = questions.multi_items(q, state, ctx)
            picked = con.checklist(title, [(it.attr, tr(it.label), getattr(state, it.attr)) for it in items])
            for attr, on in picked.items():
                setattr(state, attr, on)
        if q.after and (msg := q.after(state, ctx)):
            con.note(msg)
    step_other_systems(con, state, ctx)
    questions.finalize(state, ctx)


def show_summary(con: Console, state: InstallState):
    con.heading(tr("Check before starting the install"))
    rows = summary_rows(state)
    width = min(max(len(t) for t, _v in rows), 28)
    for title, value in rows:
        con.say(f"  {title:<{width}}  {value}")


def _dry_run_forced() -> bool:
    return bool(os.environ.get("ROUDIX_INSTALLER_DRY_RUN"))


def confirm_and_run(con: Console, state: InstallState, ctx: questions.Ctx,
                    privileges: Callable[[Console], bool]) -> int:
    existing = state.mode == existing_nixos.MODE_EXISTING
    while True:
        show_summary(con, state)
        con.say()
        actions = [("go", tr("Convert this NixOS to Roudix") if existing else tr("Install Roudix")),
                   ("sim", tr("Simulate (nothing is written)")),
                   ("edit", tr("Edit the options")),
                   ("quit", tr("Quit"))]
        if _dry_run_forced():
            actions = [a for a in actions if a[0] != "go"]
        action = con.choice(tr("What now?"), actions, default="sim" if _dry_run_forced() else ("go" if existing else "sim"))
        if action == "quit":
            raise Aborted
        if action == "edit":
            ask_options(con, state, ctx)
            continue
        if action == "go":
            if not existing:
                warning = tr("⚠ The selected disk will be completely wiped (simple mode)") \
                    if state.disk.mode == "simple" else tr("Check before starting the install")
                con.say(warning, "yellow")
            if not con.yes_no(tr("Start now?"), default=existing):
                continue
        state.dry_run = action == "sim" or _dry_run_forced()
        if not state.dry_run and not privileges(con):
            return 1
        break
    return run_install(con, state)


def run_install(con: Console, state: InstallState) -> int:
    runner = InstallRunner(state, log=lambda t: _print_log(con, t), status=lambda l, f: _print_status(con, l, f),
                           use_pkexec=False)
    con.heading(tr("Installation"))
    try:
        ok = runner.run()
    except KeyboardInterrupt:
        con.say(tr("Interrupted — the installation may be incomplete."), "red")
        return 130
    if not ok:
        return 1
    if runner.is_dry_run():
        con.say(tr("Dry run finished — nothing was changed"), "green")
        return 0
    if con.yes_no(tr("Reboot now"), default=True):
        con.say(tr("Rebooting…"))
        subprocess.run(runner.priv(["systemctl", "reboot"], root=not runner.existing))
    return 0


_STYLE = {"cmd": "blue", "error": "red", "success": "green"}


def _print_log(con: Console, text: str):
    con.say(text, _STYLE.get(classify_line(text) or "", ""))


def _print_status(con: Console, label: str, fraction: float):
    con.say(f"[{int(fraction * 100):>3}%] {label}", "bold")


# ── Entry point ───────────────────────────────────────────────────────────

def run(lang: Optional[str] = None, console: Optional[Console] = None,
        privileges: Callable[[Console], bool] = ensure_privileges) -> int:
    con = console or Console()
    try:
        return _run(con, lang, privileges)
    except Aborted:
        con.say(tr("Aborted — nothing was changed."), "yellow")
        return 130
    except RuntimeError as exc:
        con.say(f"{tr('Error')}: {exc}", "red")
        return 1


def _run(con: Console, lang: Optional[str], privileges: Callable[[Console], bool]) -> int:
    choose_language(con, lang)
    state = InstallState()
    state.mode = existing_nixos.detect_mode()
    existing = state.mode == existing_nixos.MODE_EXISTING
    if existing:
        state.username = existing_nixos.current_user()
        # The profiles (hosts/<n>/local.nix.example) are not on an installed system yet.
        existing_nixos.prepare_catalog(log=lambda m: con.say(m, "dim"))
    con.heading("Roudix")
    con.say(welcome_text(existing))
    choose_host(con, state)
    if not _dry_run_forced() and not privileges(con):
        return 1
    if not existing:
        step_disk(con, state)
    step_user(con, state)
    ctx = questions.make_ctx(state, existing)
    seeded = questions.prepare(state, ctx)
    if seeded:
        con.note(tr("Answers pre-filled with the “{hostname}” profile's values.").format(hostname=state.hostname))
    ask_options(con, state, ctx)
    return confirm_and_run(con, state, ctx, privileges)

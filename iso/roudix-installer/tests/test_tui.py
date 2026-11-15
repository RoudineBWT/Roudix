"""
Tests of the terminal front-end and of the GTK-free backend it shares with the GTK one.

    python3 -m unittest discover -s iso/roudix-installer/tests -v

No GTK, no root, no network, nothing is installed: the walk-through runs in
dry-run mode (config generated into a temp dir) against the profiles of this
repository.
"""
import io
import os
import re
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]          # repository root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ["ROUDIX_CFG_ROOT"] = str(ROOT)
os.environ["ROUDIX_INSTALLER_MODE"] = "fresh"
os.environ.pop("ROUDIX_INSTALLER_DRY_RUN", None)

from roudix_installer import host_defaults, i18n, multiboot, questions, tui  # noqa: E402
from roudix_installer.state import InstallState, safe_nix_text  # noqa: E402

FAKE_DISKS = [{"path": "/dev/vda", "size": "20G", "model": "Fake disk"}]


class Scripted(tui.Console):
    """A console fed by rules: {regex on the last question title: answer}; "" = Enter."""

    def __init__(self, rules=None, secrets=("pw1234", "pw1234")):
        super().__init__(out=io.StringIO(), color=False)
        self.rules = rules or {}
        self.secrets = list(secrets)
        self.title = ""
        self.asked = []

    def say(self, text="", style=""):
        if style == "bold":
            self.title = text
        super().say(text, style)

    def ask(self, prompt):
        self.asked.append((self.title, prompt))
        if len(self.asked) > 3000:          # a wizard that loops forever must fail, not eat the memory
            raise tui.Aborted
        # a menu is identified by its title, a yes/no or text prompt by its own text
        key = self.title if prompt.lstrip().startswith("Choice") else prompt
        for pattern, reply in self.rules.items():
            if re.search(pattern, key):
                if isinstance(reply, list):  # successive answers, the last one repeats
                    return reply.pop(0) if len(reply) > 1 else reply[0]
                return reply
        return ""

    def secret(self, prompt):
        return self.secrets.pop(0)

    @property
    def transcript(self):
        return self.out.getvalue()


def walk(rules=None, **kw):
    """Whole wizard in dry-run mode; returns (exit code, console)."""
    base = {r"^Choose a disk$": "1", r"^Username": "tester"}
    base.update(rules or {})
    con = Scripted(base, **kw)
    with mock.patch.dict(os.environ, {"ROUDIX_INSTALLER_DRY_RUN": "1", "TERM": "xterm"}), \
            mock.patch.object(tui, "list_disks", return_value=FAKE_DISKS):
        return tui.run(lang="en", console=con, privileges=lambda c: True), con


class Base(unittest.TestCase):
    def has(self, needle, text):
        self.assertTrue(needle in text, f"missing {needle!r}; end of output: ...{text[-500:]!r}")

    def hasnt(self, needle, text):
        self.assertFalse(needle in text, f"unexpected {needle!r}")


class WalkThrough(Base):
    def test_full_dry_run_with_defaults(self):
        code, con = walk()
        out = con.transcript
        self.assertEqual(code, 0, out[-500:])
        self.has('username.nix = "tester"', out)
        self.has("every chosen option was written to local.nix", out)
        self.has("Dry run finished", out)
        self.hasnt("Traceback", out)

    def test_no_gtk_needed(self):
        # The TUI and everything it imports must work without PyGObject.
        mods = [m for m in sys.modules if m == "gi" or m.startswith("gi.")]
        self.assertEqual(mods, [])

    def test_answers_reach_the_config(self):
        code, con = walk({r"^Browser$": "firefox", r"^Terminal$": "kitty"})
        out = con.transcript
        self.assertEqual(code, 0, out[-500:])
        self.assertRegex(out, r'roudix\.browsers\s*=\s*\["firefox"\]')
        self.assertRegex(out, r'roudix\.terminal\s*=\s*"kitty"')

    def test_password_mismatch_is_asked_again(self):
        code, con = walk(secrets=("a", "b", "good", "good"))
        self.assertEqual(code, 0)
        self.has("Passwords don't match.", con.transcript)

    def test_invalid_username_refused(self):
        code, con = walk({r"^Username": ["root", "bad name", "tester"]})
        self.assertEqual(code, 0, con.transcript[-500:])
        self.assertEqual(con.transcript.count("Invalid username"), 2)
        self.has('username.nix = "tester"', con.transcript)

    def test_ctrl_d_aborts_cleanly(self):
        con = Scripted()
        con.ask = mock.Mock(side_effect=tui.Aborted)
        with mock.patch.dict(os.environ, {"ROUDIX_INSTALLER_DRY_RUN": "1"}):
            self.assertEqual(tui.run(lang="en", console=con, privileges=lambda c: True), 130)

    def test_edit_options_then_simulate(self):
        # "What now?" -> edit once, then simulate
        replies = iter(["e", ""])
        con = Scripted({r"^Choose a disk$": "1", r"^Username": "tester"})
        base_ask = con.ask
        con.ask = lambda p: next(replies) if "What now?" in con.title else base_ask(p)
        with mock.patch.dict(os.environ, {"ROUDIX_INSTALLER_DRY_RUN": "1"}), \
                mock.patch.object(tui, "list_disks", return_value=FAKE_DISKS):
            code = tui.run(lang="en", console=con, privileges=lambda c: True)
        self.assertEqual(code, 0, con.transcript[-500:])


class Questions(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("en")

    def ids(self, state, ctx=None):
        ctx = ctx or questions.Ctx()
        return [q.id for q in questions.build() if questions.applicable(q, state, ctx)]

    def test_every_option_has_a_question(self):
        covered = {q.attr for q in questions.build() if q.attr}
        covered |= {it.attr for q in questions.build() for it in q.items}
        covered |= {"kernel", "kernel_chaotic", "browser", "keyboard_layout", "keyboard_variant",
                    "latest_niri", "latest_mangowc", "latest_umbriel", "latest_noctalia", "latest_dms",
                    "latest_caelestia"}   # set by custom getters/setters
        expected = set(host_defaults.OPTION_TO_ATTR.values()) | set(host_defaults.LIST_ATTRS.values())
        self.assertEqual(sorted(expected - covered), [])

    def test_attributes_exist(self):
        names = {f.name for f in fields(InstallState)}
        for q in questions.build():
            for attr in ([q.attr] if q.attr else []) + [it.attr for it in q.items]:
                self.assertIn(attr, names, q.id)

    def test_nvidia_questions_only_on_nvidia(self):
        s = InstallState()
        s.gpu = "amd"
        self.assertNotIn("nvidia_beta", self.ids(s))
        s.gpu = "nvidia"
        self.assertIn("nvidia_beta", self.ids(s))
        self.assertIn("nvidia_kernel_source", self.ids(s))

    def test_dependent_questions(self):
        s = InstallState()
        s.gaming = False
        self.assertNotIn("gaming_extras", self.ids(s))
        s.gaming = True
        self.assertIn("gaming_extras", self.ids(s))
        s.music_player = "spotify"
        self.assertIn("spicetify_theme", self.ids(s))
        s.bootloader = "systemd-boot"
        self.assertNotIn("boot_aspect", self.ids(s))
        self.assertNotIn("eac", self.ids(s))

    def test_bios_hides_uefi_only_options(self):
        s = InstallState()
        ids = self.ids(s, questions.Ctx(bios=True))
        self.assertNotIn("secure_boot", ids)
        self.assertNotIn("eac", ids)
        s.secure_boot = s.eac_enable = True
        questions.finalize(s, questions.Ctx(bios=True))
        self.assertFalse(s.secure_boot or s.eac_enable)

    def test_profile_filter(self):
        s = InstallState()
        listed = questions.Ctx(listed={"hardware.myGpu"})
        self.assertEqual(self.ids(s, listed), ["gpu"])

    def test_nixie_profile_asks_fewer_questions(self):
        ctx = questions.make_ctx(InstallState(hostname="nixie"), False)
        if ctx.listed is None:
            self.skipTest("no nixie profile in this tree")
        s = InstallState(hostname="nixie")
        self.assertLess(len(self.ids(s, ctx)), len(self.ids(InstallState(), questions.Ctx())))

    def test_free_text_cannot_inject_nix(self):
        for bad in ('a"b', "a${b}", "a'b", "a\\b", "a\nb", "a`b"):
            self.assertFalse(safe_nix_text(bad), bad)
        for good in ("i2c-0", "CMH64GX5M2B5200C40", "1h", "Arc-2.0, x"):
            self.assertTrue(safe_nix_text(good), good)


class Multiboot(unittest.TestCase):
    OUT = (
        "BootCurrent: 0001\n"
        "Boot0000* Windows Boot Manager\tHD(1,GPT,3a1f2b5c-0d4e-4f60-8a7b-1c2d3e4f5a6b,0x800,0x32000)"
        "/File(\\EFI\\Microsoft\\Boot\\bootmgfw.efi)WINDOWS.........x...B.C.D.\n"
        "Boot0001* Limine\tHD(1,GPT,11111111-2222-3333-4444-555555555555,0x800,0x32000)/\\EFI\\limine\\BOOTX64.EFI\n"
        "Boot0002* NixOS\tHD(2,GPT,aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,0x1,0x2)/File(\\EFI\\nixos\\x.efi)\n"
        "Boot0003* UEFI: PXE IPv4 Intel\tPciRoot(0x0)/Pci(0x1f,0x6)/MAC(001122334455,1)\n"
        "Boot0004  Disabled\tHD(1,GPT,11111111-2222-3333-4444-555555555555,0x800,0x32000)/File(\\EFI\\x\\y.efi)\n"
        "Boot0005* Ev$il '' ${x}\tHD(1,GPT,11111111-2222-3333-4444-555555555555,0x800,0x32000)/File(\\EFI\\Evil\\a.efi)\n"
    )

    def test_parse(self):
        got = multiboot.parse(self.OUT)
        self.assertEqual([e.label for e in got][:2], ["Windows Boot Manager", "Limine"])
        self.assertEqual(got[0].efi_path, "/EFI/Microsoft/Boot/bootmgfw.efi")
        self.assertEqual(got[0].partuuid, "3a1f2b5c-0d4e-4f60-8a7b-1c2d3e4f5a6b")
        labels = " ".join(e.label for e in got)
        self.assertNotIn("NixOS", labels)       # Roudix/NixOS itself
        self.assertNotIn("PXE", labels)         # firmware tools
        self.assertNotIn("Disabled", labels)    # inactive entry

    def test_render_cannot_break_out_of_the_nix_string(self):
        text = multiboot.render(multiboot.parse(self.OUT))
        self.assertNotIn("${", text.replace("${", "", 0).split("extraEntries")[1])
        body = text.split("extraEntries = ''", 1)[1].rsplit("'';", 1)[0]
        self.assertNotIn("''", body)
        self.assertNotIn("$", body)
        self.assertIn("path: uuid(3a1f2b5c-0d4e-4f60-8a7b-1c2d3e4f5a6b):/EFI/Microsoft/Boot/bootmgfw.efi", text)

    def test_render_refuses_unsafe_entries(self):
        with self.assertRaises(ValueError):
            multiboot.render([("x", "11111111-2222-3333-4444-555555555555", "/EFI/a b/c.efi")])


class Runner(unittest.TestCase):
    def make(self, existing, pkexec=True):
        from roudix_installer import existing_nixos
        from roudix_installer.runner import InstallRunner
        s = InstallState()
        s.mode = existing_nixos.MODE_EXISTING if existing else existing_nixos.MODE_FRESH
        return InstallRunner(s, log=lambda t: None, status=lambda l, f: None, use_pkexec=pkexec)

    def test_priv_as_root_is_a_noop(self):
        with mock.patch("os.geteuid", return_value=0):
            self.assertEqual(self.make(True).priv(["ls"]), ["ls"])

    def test_priv_terminal_uses_sudo_with_path(self):
        with mock.patch("os.geteuid", return_value=1000):
            cmd = self.make(True, pkexec=False).priv(["nixos-rebuild", "boot"])
        self.assertEqual(cmd[:3], ["sudo", "-n", "env"])
        self.assertTrue(cmd[3].startswith("PATH="))
        self.assertEqual(cmd[4:], ["nixos-rebuild", "boot"])

    def test_priv_graphical_existing_uses_pkexec(self):
        with mock.patch("os.geteuid", return_value=1000), mock.patch("shutil.which", return_value="/bin/pkexec"):
            self.assertEqual(self.make(True).priv(["ls"])[0], "pkexec")

    def test_bad_username_never_reaches_a_command(self):
        from roudix_installer.runner import InstallRunner
        s = InstallState()
        s.username = "x; rm -rf /"
        logs = []
        r = InstallRunner(s, log=logs.append, status=lambda l, f: None)
        with mock.patch("subprocess.Popen") as popen:
            self.assertFalse(r.run())
        popen.assert_not_called()


class ExistingNixos(Base):
    def test_existing_mode_has_no_disk_and_no_password(self):
        con = Scripted({r"^Reboot now": "n"})
        env = {"ROUDIX_INSTALLER_MODE": "existing", "TERM": "xterm"}
        with mock.patch.dict(os.environ, env), \
                mock.patch("roudix_installer.existing_nixos.current_user", return_value="tester"), \
                mock.patch("roudix_installer.existing_nixos.user_exists", return_value=True), \
                mock.patch("roudix_installer.existing_nixos.prepare_catalog"), \
                mock.patch("roudix_installer.runner.InstallRunner.run", return_value=True) as run:
            code = tui.run(lang="en", console=con, privileges=lambda c: True)
        out = con.transcript
        self.assertEqual(code, 0, out[-500:])
        run.assert_called_once()
        self.hasnt("Choose a disk", out)
        self.hasnt("Confirm password", out)
        self.has("Convert this NixOS to Roudix", out)
        self.has("This machine already runs NixOS", out)

    def test_unknown_user_is_refused(self):
        con = Scripted()
        with mock.patch.dict(os.environ, {"ROUDIX_INSTALLER_MODE": "existing", "TERM": "xterm"}), \
                mock.patch("roudix_installer.existing_nixos.current_user", return_value="ghost"), \
                mock.patch("roudix_installer.existing_nixos.user_exists", return_value=False), \
                mock.patch("roudix_installer.existing_nixos.prepare_catalog"):
            code = tui.run(lang="en", console=con, privileges=lambda c: True)
        self.assertEqual(code, 1)
        self.has("doesn't exist on this system", con.transcript)


class EntryPoint(Base):
    def run_main(self, argv, env=None):
        from roudix_installer import main as entry
        with mock.patch.dict(os.environ, env or {}, clear=False), \
                mock.patch("roudix_installer.tui.run", return_value=0) as tui_run:
            code = entry.main(argv)
        return code, tui_run

    def test_tui_flag(self):
        code, tui_run = self.run_main(["--tui", "--lang", "fr"])
        self.assertEqual(code, 0)
        tui_run.assert_called_once_with(lang="fr")

    def test_no_display_means_tui(self):
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY", "ROUDIX_INSTALLER_UI")}
        with mock.patch.dict(os.environ, env, clear=True):
            code, tui_run = self.run_main([])
        tui_run.assert_called_once()

    def test_gui_requested_without_gtk_fails_clearly(self):
        # PyGObject is not installed here (that is the point of the TUI)
        with mock.patch.dict(sys.modules, {"roudix_installer.gui": None}):
            code, tui_run = self.run_main(["--gui"])
        self.assertEqual(code, 1)
        tui_run.assert_not_called()

    def test_dry_run_flag_reaches_the_runner(self):
        from roudix_installer import main as entry
        seen = []
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ROUDIX_INSTALLER_DRY_RUN", None)
            with mock.patch("roudix_installer.tui.run",
                            side_effect=lambda **kw: seen.append(os.environ.get("ROUDIX_INSTALLER_DRY_RUN")) or 0):
                entry.main(["--tui", "--dry-run"])
        self.assertEqual(seen, ["1"])



class LiveDetection(unittest.TestCase):
    LIVE = "25 1 0:22 / / rw - tmpfs tmpfs rw\n30 25 7:0 / /nix/.ro-store ro - squashfs /dev/loop0 ro\n"
    INSTALLED = "25 1 259:2 / / rw - ext4 /dev/nvme0n1p2 rw\n26 25 259:1 / /boot rw - vfat /dev/nvme0n1p1 rw\n"
    IMPERMANENCE = "25 1 0:22 / / rw - tmpfs tmpfs rw\n26 25 259:2 / /nix rw - ext4 /dev/nvme0n1p2 rw\n"

    def test_stock_or_roudix_iso_is_live(self):
        from roudix_installer import existing_nixos
        self.assertTrue(existing_nixos.is_live_system(self.LIVE))

    def test_installed_system_is_not_live(self):
        from roudix_installer import existing_nixos
        self.assertFalse(existing_nixos.is_live_system(self.INSTALLED))
        self.assertFalse(existing_nixos.is_live_system(self.IMPERMANENCE))


if __name__ == "__main__":
    unittest.main()

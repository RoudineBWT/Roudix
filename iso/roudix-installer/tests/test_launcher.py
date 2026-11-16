"""Re-running the installer as root must go through the same launcher (Nix wrapper)."""
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from roudix_installer import main as entry  # noqa: E402


def _exe(path: Path):
    path.write_text("#!/bin/sh\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Launcher(unittest.TestCase):
    def test_nix_wrapped_script_goes_back_through_the_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp)
            _exe(bindir / "roudix-installer")
            _exe(bindir / ".roudix-installer-wrapped")
            with mock.patch.object(sys, "argv", [str(bindir / ".roudix-installer-wrapped"), "--tui"]):
                self.assertEqual(entry._launcher(), [str(bindir / "roudix-installer")])

    def test_wrapper_launch_is_used_as_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / "roudix-installer"
            _exe(wrapper)
            with mock.patch.object(sys, "argv", [str(wrapper)]):
                self.assertEqual(entry._launcher(), [str(wrapper)])

    def test_source_checkout_falls_back_to_the_interpreter(self):
        with mock.patch.object(sys, "argv", ["/x/src/roudix_installer/main.py"]), \
                mock.patch("shutil.which", return_value=None):
            cmd = entry._launcher()
        self.assertEqual(cmd[-3:], [sys.executable, "-m", "roudix_installer.main"])
        self.assertTrue(cmd[1].startswith("PYTHONPATH="))

    def test_command_runs_the_launcher_under_sudo(self):
        with mock.patch("shutil.which", return_value="/usr/bin/sudo"), \
                mock.patch.object(entry, "_launcher", return_value=["/nix/store/x/bin/roudix-installer"]), \
                mock.patch.dict(os.environ, {"PATH": "/p", "HOME": "/home/nixos"}, clear=True), \
                mock.patch("os.execvp") as ex:
            entry._reexec_as_root(["--tui"])
        cmd = ex.call_args[0][1]
        self.assertEqual(cmd[:2], ["sudo", "env"])
        self.assertIn("PATH=/p", cmd)
        self.assertNotIn("HOME=/home/nixos", cmd)
        self.assertEqual(cmd[-2:], ["/nix/store/x/bin/roudix-installer", "--tui"])


if __name__ == "__main__":
    unittest.main()

"""
Tiny helpers to read system facts. No GTK here.
"""
import os
import shutil
import subprocess


def run_maybe_root(cmd: list[str], timeout: int = 10) -> str:
    """stdout of `cmd`, or "" when it is missing / fails.

    Tries as the current user first, then through `sudo -n` (which only works
    if credentials are already cached — never prompts, never hangs). Meant for
    best-effort detection (efibootmgr, dmidecode, i2cdetect): a missing answer
    just means "ask the user", it is never an error."""
    exe = shutil.which(cmd[0])
    if exe is None:
        return ""
    attempts = [[exe, *cmd[1:]]]
    if os.geteuid() != 0 and shutil.which("sudo"):
        attempts.append(["sudo", "-n", exe, *cmd[1:]])
    for full in attempts:
        try:
            proc = subprocess.run(full, capture_output=True, text=True, timeout=timeout,
                                  stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
    return ""

"""Managed block in Roudix's local.nix files (the only thing roudix-store writes).

user   -> ~/.config/roudix/modules/home/local.nix   roudix.store.packages
system -> ~/.config/roudix/hosts/<host>/local.nix   roudix.store.systemPackages
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import tempfile

NH_FLAKE = os.path.expanduser("~/.config/roudix")
HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
FILES = {
    "home": (os.path.join(NH_FLAKE, "modules/home/local.nix"), "roudix.store.packages"),
    "system": (os.path.join(NH_FLAKE, "hosts", HOST, "local.nix"), "roudix.store.systemPackages"),
}
BACKUP_DIR = os.path.expanduser("~/.cache/roudix-store")
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")
BEGIN = "# >>> roudix-store (managed by Roudix Store, edit with care) >>>"
END = "# <<< roudix-store <<<"
BLOCK_RE = re.compile(r"\n?[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*\n?", re.S)


def read_block(path: str) -> list[str]:
    """Package names currently in the managed block (empty if none)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    m = BLOCK_RE.search(text)
    if not m:
        return []
    return [n for n in re.findall(r'"([^"\n]+)"', m.group(0)) if NAME_RE.match(n)]


def _render(key: str, names) -> str:
    items = "".join(f'    "{n}"\n' for n in sorted(set(names)))
    return f"  {BEGIN}\n  {key} = [\n{items}  ];\n  {END}\n"


def write_block(path: str, key: str, names) -> bool | str:
    """Replace/insert/remove the managed block. True, or an error string."""
    names = list(names)
    bad = [n for n in names if not NAME_RE.match(n)]
    if bad:
        return f"invalid package name: {bad[0]!r}"
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        text = "{ ... }:\n{\n}\n"
    except OSError as exc:
        return str(exc)
    body = _render(key, names) if names else ""
    if BLOCK_RE.search(text):
        new = BLOCK_RE.sub(lambda _m: ("\n" + body) if body else "", text, count=1)
    elif not names:
        return True
    else:
        i = text.rstrip().rfind("}")
        if i < 0:
            return "no closing '}' found in " + path
        new = text[:i].rstrip("\n") + "\n\n" + body + text[i:]
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".store-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new)
        os.replace(tmp, path)
    except OSError as exc:
        return str(exc)
    return True


def backup_files() -> dict[str, str | None]:
    """Copy both local.nix files outside the repo (gitwatch must not see them)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    saved: dict[str, str | None] = {}
    for scope, (path, _key) in FILES.items():
        dst = os.path.join(BACKUP_DIR, f"{scope}.local.nix.bak")
        if os.path.exists(path):
            shutil.copy2(path, dst)
            saved[scope] = dst
        else:
            saved[scope] = None
    return saved


def restore_files(saved: dict[str, str | None]) -> None:
    for scope, bak in saved.items():
        path = FILES[scope][0]
        if bak:
            shutil.copy2(bak, path)
        elif os.path.exists(path):
            os.remove(path)

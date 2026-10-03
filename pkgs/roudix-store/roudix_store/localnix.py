"""Managed block in Roudix's local.nix files (the only thing roudix-store writes).

Scopes and where they live (hosts/*/local.nix and modules/home/local.nix are
already gitignored, so nothing here ever gets committed or pulled over):
  home    -> ~/.config/roudix/modules/home/local.nix  roudix.store.packages
  system  -> ~/.config/roudix/hosts/<host>/local.nix  roudix.store.systemPackages
  flatpak -> ~/.config/roudix/hosts/<host>/local.nix  roudix.store.flatpaks
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import tempfile

NH_FLAKE = os.path.expanduser("~/.config/roudix")
HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
HOME_FILE = os.path.join(NH_FLAKE, "modules/home/local.nix")
HOST_FILE = os.path.join(NH_FLAKE, "hosts", HOST, "local.nix")
SCOPES = {
    "home": (HOME_FILE, "roudix.store.packages"),
    "system": (HOST_FILE, "roudix.store.systemPackages"),
    "flatpak": (HOST_FILE, "roudix.store.flatpaks"),
}
BACKUP_DIR = os.path.expanduser("~/.cache/roudix-store")
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")
BEGIN = "# >>> roudix-store (managed by Roudix Store, edit with care) >>>"
END = "# <<< roudix-store <<<"
BLOCK_RE = re.compile(r"\n?[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*\n?", re.S)
LIST_RE = re.compile(r"([A-Za-z0-9_.]+)\s*=\s*\[(.*?)\]\s*;", re.S)


def _files() -> list[str]:
    seen: list[str] = []
    for path, _key in SCOPES.values():
        if path not in seen:
            seen.append(path)
    return seen


def read_file(path: str) -> dict[str, list[str]]:
    """{nix option: [names]} found in the managed block of one file."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    m = BLOCK_RE.search(text)
    if not m:
        return {}
    return {key: [n for n in re.findall(r'"([^"\n]+)"', body) if NAME_RE.match(n)]
            for key, body in LIST_RE.findall(m.group(0))}


def read_all() -> dict[str, set[str]]:
    cache: dict[str, dict[str, list[str]]] = {}
    out: dict[str, set[str]] = {}
    for scope, (path, key) in SCOPES.items():
        out[scope] = set(cache.setdefault(path, read_file(path)).get(key, []))
    return out


def _render(lists: dict[str, list[str]]) -> str:
    body = ""
    for key, names in lists.items():
        if names:
            items = "".join(f'    "{n}"\n' for n in sorted(set(names)))
            body += f"  {key} = [\n{items}  ];\n"
    return f"  {BEGIN}\n{body}  {END}\n" if body else ""


def write_file(path: str, lists: dict[str, list[str]]) -> bool | str:
    """Replace/insert/remove the managed block of one file. True, or an error string."""
    for names in lists.values():
        bad = [n for n in names if not NAME_RE.match(n)]
        if bad:
            return f"invalid package name: {bad[0]!r}"
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        text = "{ ... }:\n{\n}\n"
    except OSError as exc:
        return str(exc)
    body = _render(lists)
    if BLOCK_RE.search(text):
        new = BLOCK_RE.sub(lambda _m: ("\n" + body) if body else "", text, count=1)
    elif not body:
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


def write_all(state: dict[str, set[str]]) -> bool | str:
    """Write every scope; each file is rewritten once with all its lists."""
    for path in _files():
        lists = {key: sorted(state.get(scope, ())) for scope, (p, key) in SCOPES.items() if p == path}
        res = write_file(path, lists)
        if res is not True:
            return res
    return True


def backup_files() -> dict[str, str | None]:
    """Copy the local.nix files outside the repo (gitwatch must not see them)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    saved: dict[str, str | None] = {}
    for i, path in enumerate(_files()):
        dst = os.path.join(BACKUP_DIR, f"{i}.local.nix.bak")
        if os.path.exists(path):
            shutil.copy2(path, dst)
            saved[path] = dst
        else:
            saved[path] = None
    return saved


def restore_files(saved: dict[str, str | None]) -> None:
    for path, bak in saved.items():
        if bak:
            shutil.copy2(bak, path)
        elif os.path.exists(path):
            os.remove(path)

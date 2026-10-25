# roudix_firewall_core — logic of roudix-firewall, no GTK in here.
#
# The app owns ONE file: hosts/<host>/firewall.local.nix. It is gitignored
# (like local.nix), so `git pull` / roudix-autoupdate never overwrite it and a
# local edit can never block a fast-forward. configuration.nix imports it when
# it exists (lib.optional (builtins.pathExists …)).
#
# The file carries its own state as one JSON comment line (rule names,
# disabled rules…), followed by the generated Nix. A SHA-256 of the Nix body is
# stored next to it: if someone edits the Nix by hand, the hash no longer
# matches and the file is read back from the Nix itself instead, so a manual
# edit is never silently ignored.

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import tempfile
from dataclasses import dataclass, field

# ── Paths ─────────────────────────────────────────────────────────────────────

NH_FLAKE = os.environ.get("NH_FLAKE", os.path.expanduser("~/.config/roudix"))
# The machine's hostname is also its hosts/<name>/ directory (same convention
# as roudix-kernel-switcher and roudix-switcher).
ROUDIX_HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()

FILE_NAME = "firewall.local.nix"


def host_dir() -> str:
    return os.path.join(NH_FLAKE, "hosts", ROUDIX_HOST)


def firewall_file() -> str:
    return os.path.join(host_dir(), FILE_NAME)


def local_nix_file() -> str:
    return os.path.join(host_dir(), "local.nix")


def rebuild_command() -> list[str]:
    # `switch` (not `boot`): a firewall change should be live right away.
    # `path:` (not git+file:) so gitignored files are part of the flake.
    return ["nh", "os", "switch", "--elevation-strategy", "pkexec",
            "--accept-flake-config", f"path:{NH_FLAKE}"]


# ── Model ─────────────────────────────────────────────────────────────────────

PROTOS = ("tcp", "udp", "both")
PROTO_LABEL = {"tcp": "TCP", "udp": "UDP", "both": "TCP+UDP"}

# A port spec is a list of inclusive (from, to) pairs; a single port is (p, p).
PortSpec = list[tuple[int, int]]

MAX_NAME_LEN = 64
_IFACE_RE = re.compile(r"^[A-Za-z0-9_.:@+-]{1,15}$")  # IFNAMSIZ - 1


class FirewallError(ValueError):
    """Validation / IO problem (message in English, for logs; the GUI words its own)."""


class EmptyPortsError(FirewallError):
    """The ports field has nothing in it."""


class BadPortError(FirewallError):
    """One token of the ports field is not a port or a range; .token says which."""

    def __init__(self, token: str):
        super().__init__(token)
        self.token = token


def parse_port_spec(text: str) -> PortSpec:
    """'80, 443, 8000-8010' -> [(80, 80), (443, 443), (8000, 8010)] (sorted, deduped)."""
    tokens = [t for t in re.split(r"[,;\s]+", text.strip()) if t]
    if not tokens:
        raise EmptyPortsError("empty")
    out: set[tuple[int, int]] = set()
    for tok in tokens:
        m = re.fullmatch(r"(\d+)(?:\s*[-:–]\s*(\d+))?", tok)
        if not m:
            raise BadPortError(tok)
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) is not None else lo
        if not (1 <= lo <= 65535 and 1 <= hi <= 65535) or lo > hi:
            raise BadPortError(tok)
        out.add((lo, hi))
    return sorted(out)


def format_port_spec(spec: PortSpec) -> str:
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in spec)


def valid_interface(name: str) -> bool:
    return bool(_IFACE_RE.match(name))


@dataclass
class Rule:
    name: str
    proto: str          # "tcp" | "udp" | "both"
    spec: PortSpec
    enabled: bool = True

    def ports_text(self) -> str:
        return format_port_spec(self.spec)

    def key(self) -> tuple:
        return (self.proto, tuple(self.spec))


@dataclass
class Config:
    enabled: bool = True
    rules: list[Rule] = field(default_factory=list)
    trusted_interfaces: list[str] = field(default_factory=list)
    # How this config was read back: "metadata" (our own JSON line, hash OK),
    # "nix" (hand-edited / foreign file, parsed from the Nix) or "new" (no file).
    origin: str = "new"

    def snapshot(self) -> str:
        """Stable string used to detect unsaved changes."""
        return json.dumps(_to_meta(self), sort_keys=True)


def clean_name(name: str) -> str:
    name = " ".join(name.split())[:MAX_NAME_LEN]
    if not name:
        raise FirewallError("name")
    return name


# ── Presets ───────────────────────────────────────────────────────────────────
# (category, name, proto, ports). tr_noop only marks the strings for xgettext
# (scripts/i18n.sh); the GUI runs them through tr() when it displays them.

def tr_noop(s: str) -> str:
    return s


PRESETS: list[tuple[str, str, str, str]] = [
    (tr_noop("Common services"), tr_noop("SSH"),              "tcp",  "22"),
    (tr_noop("Common services"), tr_noop("HTTP / HTTPS"),     "tcp",  "80, 443"),
    (tr_noop("Common services"), tr_noop("DNS"),              "udp",  "53"),
    (tr_noop("Gaming"), tr_noop("Steam (game server)"),       "both", "27015-27030"),
    (tr_noop("Gaming"), tr_noop("Sunshine (TCP)"),            "tcp",  "47984, 47989, 47990, 48010"),
    (tr_noop("Gaming"), tr_noop("Sunshine (UDP)"),            "udp",  "47998, 47999, 48000, 48002, 48010"),
    (tr_noop("Gaming"), tr_noop("Minecraft Java server"),     "tcp",  "25565"),
    (tr_noop("Gaming"), tr_noop("Minecraft Bedrock server"),  "udp",  "19132"),
    (tr_noop("Connectivity"), tr_noop("KDE Connect / GSConnect"), "both", "1714-1764"),
    (tr_noop("Connectivity"), tr_noop("Syncthing (TCP)"),     "tcp",  "22000"),
    (tr_noop("Connectivity"), tr_noop("Syncthing (UDP)"),     "udp",  "22000, 21027"),
    (tr_noop("Connectivity"), tr_noop("Samba (TCP)"),         "tcp",  "139, 445"),
    (tr_noop("Connectivity"), tr_noop("Samba (UDP)"),         "udp",  "137, 138"),
    (tr_noop("Connectivity"), tr_noop("LocalSend"),           "both", "53317"),
]

INTERFACE_PRESETS: list[tuple[str, str]] = [
    ("docker0", tr_noop("Docker")),
    ("podman0", tr_noop("Podman")),
    ("virbr0", tr_noop("Libvirt / QEMU")),
    ("br0", tr_noop("Network bridge")),
    ("tailscale0", tr_noop("Tailscale")),
    ("wg0", tr_noop("WireGuard")),
]


# ── Generation ────────────────────────────────────────────────────────────────

_META_PREFIX = "# roudix-firewall:v1 "
_META_RE = re.compile(r"^# roudix-firewall:v1 (\{.*\})[ \t]*$", re.MULTILINE)

_HEADER = (
    "# Generated by roudix-firewall — rewritten on every save from the app.\n"
    "# Gitignored: never overwritten or blocked by `git pull` / roudix-autoupdate.\n"
    "# Hand edits to the Nix below are picked up by the app, then regenerated.\n"
)


def _to_meta(cfg: Config) -> dict:
    return {
        "enabled": cfg.enabled,
        "rules": [{"name": r.name, "proto": r.proto,
                   "ports": [list(p) for p in r.spec], "enabled": r.enabled}
                  for r in cfg.rules],
        "trusted_interfaces": list(cfg.trusted_interfaces),
    }


def _by_proto(cfg: Config, wanted: str) -> tuple[list[int], list[tuple[int, int]]]:
    singles: set[int] = set()
    ranges: set[tuple[int, int]] = set()
    for r in cfg.rules:
        if not r.enabled or r.proto not in (wanted, "both"):
            continue
        for a, b in r.spec:
            if a == b:
                singles.add(a)
            else:
                ranges.add((a, b))
    return sorted(singles), sorted(ranges)


def _nix_body(cfg: Config) -> str:
    lines = [
        "{ lib, ... }:",
        "{",
        "  networking.firewall = {",
        # common.nix sets enable = true at normal priority: mkForce lets the app
        # win in both directions without a \"defined multiple times\" conflict.
        f"    enable = lib.mkForce {'true' if cfg.enabled else 'false'};",
    ]
    for proto, up in (("tcp", "TCP"), ("udp", "UDP")):
        singles, ranges = _by_proto(cfg, proto)
        if singles:
            lines.append(f"    allowed{up}Ports = [ {' '.join(map(str, singles))} ];")
        if ranges:
            lines.append(f"    allowed{up}PortRanges = [")
            lines += [f"      {{ from = {a}; to = {b}; }}" for a, b in ranges]
            lines.append("    ];")
    if cfg.trusted_interfaces:
        quoted = " ".join(f'"{i}"' for i in cfg.trusted_interfaces)
        lines.append(f"    trustedInterfaces = [ {quoted} ];")
    lines += ["  };", "}", ""]
    return "\n".join(lines)


def generate(cfg: Config) -> str:
    validate(cfg)
    body = _nix_body(cfg)
    meta = _to_meta(cfg)
    meta["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    # ensure_ascii: one ASCII line, whatever the user typed as a rule name.
    return _HEADER + _META_PREFIX + json.dumps(meta, ensure_ascii=True) + "\n" + body


def validate(cfg: Config) -> None:
    """Everything that ends up in the Nix file is checked here, once."""
    for r in cfg.rules:
        if r.proto not in PROTOS:
            raise FirewallError(f"proto {r.proto!r}")
        if not r.spec:
            raise FirewallError(f"no ports in {r.name!r}")
        for a, b in r.spec:
            if not (1 <= a <= b <= 65535):
                raise FirewallError(f"port {a}-{b}")
    for i in cfg.trusted_interfaces:
        if not valid_interface(i):
            raise FirewallError(f"interface {i!r}")


# ── Parsing ───────────────────────────────────────────────────────────────────

def _from_meta(meta: dict) -> Config:
    rules = [Rule(clean_name(str(r["name"])), str(r["proto"]),
                  [(int(a), int(b)) for a, b in r["ports"]], bool(r.get("enabled", True)))
             for r in meta.get("rules", [])]
    cfg = Config(bool(meta.get("enabled", True)), rules,
                 [str(i) for i in meta.get("trusted_interfaces", [])], origin="metadata")
    validate(cfg)
    return cfg


def _nix_list(content: str, attr: str) -> str:
    m = re.search(rf"\b{attr}\s*=\s*\[(.*?)\]\s*;", content, re.DOTALL)
    return m.group(1) if m else ""


def _parse_nix(content: str, names: dict[tuple, str]) -> Config:
    """Best-effort read of the Nix itself (hand-edited or foreign file)."""
    cfg = Config(origin="nix")
    m = re.search(r"\benable\s*=\s*(?:lib\.mkForce\s+)?(true|false)\s*;", content)
    if m:
        cfg.enabled = m.group(1) == "true"
    for proto, up in (("tcp", "TCP"), ("udp", "UDP")):
        for p in re.findall(r"\d+", _nix_list(content, f"allowed{up}Ports")):
            spec = [(int(p), int(p))]
            cfg.rules.append(Rule(names.get((proto, tuple(spec)), f"{up} {p}"), proto, spec))
        for a, b in re.findall(r"from\s*=\s*(\d+)\s*;\s*to\s*=\s*(\d+)\s*;",
                               _nix_list(content, f"allowed{up}PortRanges")):
            spec = [(int(a), int(b))]
            cfg.rules.append(Rule(names.get((proto, tuple(spec)), f"{up} {a}-{b}"), proto, spec))
    cfg.trusted_interfaces = [i for i in re.findall(r'"([^"]+)"', _nix_list(content, "trustedInterfaces"))
                              if valid_interface(i)]
    # drop anything out of range rather than failing on a hand-edited file
    cfg.rules = [r for r in cfg.rules if all(1 <= a <= b <= 65535 for a, b in r.spec)]
    return cfg


def parse(content: str) -> Config:
    m = _META_RE.search(content)
    meta = None
    if m:
        try:
            meta = json.loads(m.group(1))
        except ValueError:
            meta = None
    if meta is not None:
        body = content[m.end():].lstrip("\n")
        if hashlib.sha256(body.encode()).hexdigest() == meta.get("sha256"):
            try:
                return _from_meta(meta)
            except (KeyError, TypeError, ValueError):
                pass  # corrupt metadata: fall through to the Nix
    names: dict[tuple, str] = {}
    if meta is not None:
        try:  # keep the names the user gave, for rules that still exist as is
            for r in meta.get("rules", []):
                spec = tuple((int(a), int(b)) for a, b in r["ports"])
                for proto in (("tcp", "udp") if r["proto"] == "both" else (r["proto"],)):
                    names[(proto, spec)] = clean_name(str(r["name"]))
        except (KeyError, TypeError, ValueError):
            names = {}
    return _parse_nix(content, names)


# ── Disk ──────────────────────────────────────────────────────────────────────

def load() -> Config:
    path = firewall_file()
    try:
        with open(path, encoding="utf-8") as f:
            return parse(f.read())
    except FileNotFoundError:
        return Config()


def read_previous() -> str | None:
    """Current file content, to restore it if the rebuild fails (None = no file)."""
    try:
        with open(firewall_file(), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _atomic_write(path: str, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".firewall-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def save(cfg: Config) -> None:
    """Validate, back up the previous file as *.bak (gitignored), write atomically."""
    content = generate(cfg)  # validates first: nothing is touched if it raises
    if not os.path.isdir(host_dir()):
        raise FirewallError(f"host directory not found: {host_dir()}")
    path = firewall_file()
    previous = read_previous()
    if previous is not None and previous != content:
        _atomic_write(path + ".bak", previous)
    _atomic_write(path, content)
    cfg.origin = "metadata"


def restore(previous: str | None) -> None:
    """Put the file back as it was before save() (rebuild failed)."""
    path = firewall_file()
    if previous is None:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    else:
        _atomic_write(path, previous)


# ── Environment checks (banners) ──────────────────────────────────────────────

def host_imports_firewall_file() -> bool:
    """False if hosts/<host>/configuration.nix does not import firewall.local.nix
    (checkout older than this feature): the file would be silently ignored."""
    try:
        with open(os.path.join(host_dir(), "configuration.nix"), encoding="utf-8") as f:
            return FILE_NAME in f.read()
    except OSError:
        return True  # unknown layout: do not cry wolf


def local_nix_firewall_lines() -> list[str]:
    """Uncommented networking.firewall.* lines hand-written in local.nix. They keep
    working (lists are merged) but are not editable here."""
    try:
        with open(local_nix_file(), encoding="utf-8") as f:
            return [ln.strip() for ln in f
                    if "networking.firewall" in ln and not ln.lstrip().startswith("#")]
    except OSError:
        return []

"""Translations for Roudix Store (gettext) plus the display words of the install queue.

Messages are written in English: tr("…"). The catalogs (po/<lang>.po) are compiled by the
Nix package to share/locale/<lang>/LC_MESSAGES/roudix-store.mo.
"""
from __future__ import annotations

import os

# ── translations (gettext) ───────────────────────────────────────────────────
# Messages are written in English: tr("…"). Catalogs live in po/<lang>.po and the Nix
# package compiles them to share/locale/<lang>/LC_MESSAGES/roudix-store.mo. The language comes
# from LANGUAGE / LC_ALL / LC_MESSAGES / LANG; a missing catalog falls back to English.
import gettext as _gettext
import glob as _glob

_DOMAIN = "roudix-store"


def _find_localedir(domain):
    cands = [os.environ.get("ROUDIX_LOCALEDIR", "")]
    d = os.path.dirname(os.path.realpath(__file__))
    while True:
        cands += [os.path.join(d, "share", "locale"), os.path.join(d, "locale")]
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    for c in cands:
        if c and _glob.glob(os.path.join(c, "*", "LC_MESSAGES", domain + ".mo")):
            return c
    return None


_translation = _gettext.translation(_DOMAIN, _find_localedir(_DOMAIN), fallback=True)
tr = _translation.gettext        # tr("text")
trc = _translation.pgettext      # trc("context", "text")


def tr_noop(text):
    """Mark a string for extraction now, translate it later with tr()."""
    return text


def desktop_locales() -> list[str]:
    """Locale suffixes for Name[xx] / Comment[xx] keys of .desktop files, most specific
    first (e.g. ["fr_BE", "fr"]), following the same variables gettext uses."""
    out: list[str] = []
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        for value in os.environ.get(var, "").split(":"):
            value = value.split(".")[0].split("@")[0]
            if value and value not in ("C", "POSIX"):
                out.append(value)
                if "_" in value:
                    out.append(value.split("_")[0])
        if out:
            break
    return out


def _sentence(text: str) -> str:
    """Upper-case the first letter (a translated action word may start a sentence)."""
    return text[:1].upper() + text[1:]


# Display words for queue actions / statuses (the raw values stay English: the code compares them).
# Translate them as words that fit the sentences they are used in ("Running {action} for …").
def _action_words() -> dict[str, tuple[str, str]]:
    return {
        "install": (trc("queue action", "install"), trc("queue action, capitalised", "Install")),
        "remove": (trc("queue action", "remove"), trc("queue action, capitalised", "Remove")),
        "update": (trc("queue action", "update"), trc("queue action, capitalised", "Update")),
        "system-update": (trc("queue action", "system-update"), trc("queue action, capitalised", "System-update")),
        "install-rpms": (trc("queue action", "install-rpms"), trc("queue action, capitalised", "Install-rpms")),
    }


def action_word(action: str, cap: bool = False) -> str:
    pair = _action_words().get(action)
    if pair:
        return pair[1 if cap else 0]
    return action[:1].upper() + action[1:] if cap else action


def status_word(status: str) -> str:
    words = {
        "queued": trc("queue status", "queued"),
        "running": trc("queue status", "running"),
        "done": trc("queue status", "done"),
        "failed": trc("queue status", "failed"),
    }
    return words.get(status, status)

"""Language helper — same idiom as the other Roudix apps: L(fr, en).

French when the first non-empty of LC_ALL / LC_MESSAGES / LANG / LANGUAGE starts
with "fr", English otherwise.
"""
from __future__ import annotations

import os


def _detect_lang() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(var, "")
        if value:
            return "fr" if value.lower().startswith("fr") else "en"
    return "en"


LANG = _detect_lang()


def L(fr: str, en: str) -> str:
    return fr if LANG == "fr" else en


# Display words for queue actions / statuses (the raw values stay English: the code compares them).
_ACTIONS_FR = {
    "install": "installation", "remove": "suppression", "update": "mise à jour",
    "system-update": "mise à jour système", "install-rpms": "installation RPM",
}
_STATUS_FR = {"queued": "en attente", "running": "en cours", "done": "terminé", "failed": "échec"}


def action_word(action: str, cap: bool = False) -> str:
    word = _ACTIONS_FR.get(action, action) if LANG == "fr" else action
    return word[:1].upper() + word[1:] if cap else word


def status_word(status: str) -> str:
    return _STATUS_FR.get(status, status) if LANG == "fr" else status

from __future__ import annotations

import gettext
import locale
import os
from pathlib import Path

DOMAIN = "org.dnf.AppCenter"


def _candidate_languages() -> list[str] | None:
    langs: list[str] = []
    env = os.environ.get("LANGUAGE")
    if env:
        for item in env.split(":"):
            item = item.strip()
            if item:
                langs.append(item)
    for getter in (lambda: locale.getlocale()[0], lambda: locale.getdefaultlocale()[0], lambda: os.environ.get("LANG")):
        try:
            value = getter()
        except Exception:
            value = None
        if value:
            langs.append(str(value))
    cleaned: list[str] = []
    seen: set[str] = set()
    for lang in langs:
        lang = lang.split(".", 1)[0].replace("-", "_")
        for item in (lang, lang.split("_", 1)[0]):
            if item and item not in seen:
                cleaned.append(item)
                seen.add(item)
    return cleaned or None


def _localedirs() -> list[str]:
    here = Path(__file__).resolve()
    return [
        str(here.parent.parent / "locale"),
        str(Path("/usr/share/locale")),
    ]


def _get_translation() -> gettext.NullTranslations:
    languages = _candidate_languages()
    for localedir in _localedirs():
        try:
            return gettext.translation(DOMAIN, localedir=localedir, languages=languages, fallback=True)
        except Exception:
            continue
    return gettext.NullTranslations()


_translation = _get_translation()
_ = _translation.gettext
ngettext = _translation.ngettext

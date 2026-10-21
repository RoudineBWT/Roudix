"""
i18n through GNU gettext.

Source strings are English: write ``tr("Some text")`` wherever text appears.
Translations live in ``po/<lang>.po`` (repo root of the installer) and are
compiled to ``locale/<lang>/LC_MESSAGES/roudix-installer.mo`` next to this
file at build time (see ``scripts/i18n.sh`` and the package's flake.nix).

  tr(msgid)            translate msgid
  trc(context, msgid)  same, when one English word needs two translations
                       (e.g. "none" -> "aucun" / "aucune")
  tr_noop(msgid)       mark a string for extraction without translating it yet
                       (use it in tables, then call tr() where it is displayed)

Unlike the usual process-wide ``_()``, the language can be switched while the
wizard is running (welcome page): call ``set_lang("fr" | "en" | ...)``.
Languages without a catalog (English is the source) fall back to the msgid.
"""

import gettext
import sys
from pathlib import Path

DOMAIN = "roudix-installer"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"
DEFAULT_LANG = "fr"

LANG = DEFAULT_LANG
_translation: gettext.NullTranslations = gettext.NullTranslations()


def set_lang(lang: str) -> None:
    global LANG, _translation
    LANG = lang
    _translation = gettext.translation(
        DOMAIN, localedir=str(LOCALE_DIR), languages=[lang], fallback=True
    )
    # English is the source language, so no catalog is expected for it. For any
    # other language a missing catalog means the .mo files were not built or
    # not packaged: say so instead of silently showing English.
    if lang != "en" and gettext.find(DOMAIN, str(LOCALE_DIR), [lang]) is None:
        print(f"roudix-installer: no '{lang}' translation catalog found in "
              f"{LOCALE_DIR}; falling back to English", file=sys.stderr)


def tr(message: str) -> str:
    return _translation.gettext(message)


def trc(context: str, message: str) -> str:
    return _translation.pgettext(context, message)


def tr_noop(message: str) -> str:
    return message


set_lang(DEFAULT_LANG)

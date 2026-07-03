"""
Minimal i18n: a module-level current language + L(fr, en) helper used
inline wherever text appears, instead of a big indirection-heavy key
dictionary. Good enough for a wizard this size; not meant to scale to
a real translation workflow (no .po files, no pluralization).
"""

LANG = "fr"


def set_lang(lang: str):
    global LANG
    LANG = lang


def L(fr: str, en: str) -> str:
    return fr if LANG == "fr" else en

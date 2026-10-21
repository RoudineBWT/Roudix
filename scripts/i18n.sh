#!/usr/bin/env bash
# i18n.sh — gettext workflow for the installer (iso/roudix-installer).
#
#   scripts/i18n.sh update     re-extract strings -> po/roudix-installer.pot, merge into every po/*.po
#   scripts/i18n.sh compile    po/*.po -> src/roudix_installer/locale/<lang>/LC_MESSAGES/*.mo
#                              (needed to run the installer from the source tree; Nix does it at build)
#   scripts/i18n.sh check      fail if a .po is out of date, has untranslated/fuzzy entries, or is invalid
#   scripts/i18n.sh new <lang> start a new translation, e.g. `new de`
#
# Needs GNU gettext (xgettext, msgmerge, msgfmt, msgcmp): `nix develop` provides it.
set -euo pipefail

command -v xgettext >/dev/null || { echo "i18n.sh: GNU gettext not found (use \`nix develop\`)" >&2; exit 127; }

cd "$(git rev-parse --show-toplevel)/iso/roudix-installer"
DOMAIN=roudix-installer
PKG=src/roudix_installer
POT=po/$DOMAIN.pot

# Strings come from tr("…"), trc("context", "…") and tr_noop("…") — all in English.
extract() {  # $1 = output .pot
    find "$PKG" -name '*.py' | LC_ALL=C sort | xargs xgettext \
        --language=Python --from-code=UTF-8 \
        --keyword=tr --keyword=trc:1c,2 --keyword=tr_noop \
        --add-comments=TRANSLATORS \
        --add-location=file --sort-by-file \
        --package-name="$DOMAIN" --output="$1"
    # The creation date changes on every run and would make every diff noisy.
    sed -i '/^"POT-Creation-Date:/d' "$1"
}

# Languages that must be 100% translated for `check` to pass. Any other language is
# only checked for validity and for being in sync with the sources, so a contributor
# can translate bit by bit without breaking CI.
REQUIRED_LANGS=" fr "

stats() {  # prints "<lang>: N translated, M fuzzy, K untranslated"; sets BAD=1 on a problem
    local po=$1 out lang
    lang=$(basename "$po" .po)
    out=$(msgfmt --check --statistics -o /dev/null "$po" 2>&1) || { echo "$po: INVALID"; echo "$out"; BAD=1; return; }
    echo "$lang: $out"
    if grep -qE '[0-9]+ (fuzzy|untranslated)' <<<"$out"; then
        case "$REQUIRED_LANGS" in
            *" $lang "*) BAD=1 ;;
            *) echo "  ($lang is incomplete: not enforced, only $REQUIRED_LANGS must be complete)" ;;
        esac
    fi
}

case "${1:-}" in
    update)
        mkdir -p po
        extract "$POT"
        for po in po/*.po; do
            [ -e "$po" ] || continue
            msgmerge --update --backup=off --quiet "$po" "$POT"
            BAD=0; stats "$po"
        done
        ;;
    compile)
        for po in po/*.po; do
            [ -e "$po" ] || continue
            lang=$(basename "$po" .po)
            mkdir -p "$PKG/locale/$lang/LC_MESSAGES"
            msgfmt --check -o "$PKG/locale/$lang/LC_MESSAGES/$DOMAIN.mo" "$po"
            echo "compiled: $lang"
        done
        ;;
    new)
        lang=${2:?usage: i18n.sh new <lang>   (e.g. de, es, pt_BR)}
        [ ! -e "po/$lang.po" ] || { echo "po/$lang.po already exists" >&2; exit 1; }
        extract "$POT"
        msginit --no-translator --locale="$lang" --input="$POT" --output-file="po/$lang.po"
        echo "created po/$lang.po — translate it, then: scripts/i18n.sh compile"
        ;;
    check)
        tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
        extract "$tmp/new.pot"
        BAD=0
        # 1. the committed .pot must match the current sources
        if ! diff -q <(msgcat --no-location "$POT") <(msgcat --no-location "$tmp/new.pot") >/dev/null; then
            echo "po/$DOMAIN.pot is out of date: run scripts/i18n.sh update"; BAD=1
        fi
        for po in po/*.po; do
            [ -e "$po" ] || continue
            # 2. same set of messages as the sources (nothing missing, nothing obsolete)
            if ! msgcmp --use-untranslated "$po" "$tmp/new.pot" 2>"$tmp/cmp.txt"; then
                echo "$po does not match the sources:"; sed 's/^/  /' "$tmp/cmp.txt"; BAD=1
            fi
            # 3. complete and well-formed
            stats "$po"
        done
        [ "$BAD" -eq 0 ] && echo "i18n OK" || { echo "i18n check FAILED (scripts/i18n.sh update, then translate)" >&2; exit 1; }
        ;;
    *)
        sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac

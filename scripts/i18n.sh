#!/usr/bin/env bash
# i18n.sh — gettext workflow for the installer (iso/roudix-installer) and the Roudix apps
# (pkgs/roudix-welcome, roudix-switcher, roudix-store, roudix-config, roudix-kernel-switcher, roudix-hw-sync, roudix-scheduler, roudix-firewall).
#
#   scripts/i18n.sh update  [component…]   re-extract strings -> po/<domain>.pot, merge into every po/*.po
#   scripts/i18n.sh compile [component…]   po/*.po -> <locale dir>/<lang>/LC_MESSAGES/<domain>.mo
#                                          (to run from the source tree; Nix does it at build)
#   scripts/i18n.sh check   [component…]   fail if a .po is out of date, has untranslated/fuzzy entries, or is invalid
#   scripts/i18n.sh new <lang> [component…] start a new translation, e.g. `new de`
#
# Components: installer welcome switcher store config kernel-switcher hw-sync scheduler firewall (default: all of them).
# Needs GNU gettext (xgettext, msgmerge, msgfmt, msgcmp): `nix develop` provides it.
set -euo pipefail

command -v xgettext >/dev/null || { echo "i18n.sh: GNU gettext not found (use \`nix develop\`)" >&2; exit 127; }

ROOT="$(git rev-parse --show-toplevel)"
ALL_COMPONENTS="installer welcome switcher store config kernel-switcher hw-sync scheduler firewall disk"

# Languages that must be 100% translated for `check` to pass. Any other language is
# only checked for validity and for being in sync with the sources, so a contributor
# can translate bit by bit without breaking CI.
REQUIRED_LANGS=" fr "

# select <component>: sets DIR, DOMAIN and LOCALE_DIR (where `compile` puts the .mo files)
select_component() {
    COMP=$1
    case "$COMP" in
        installer) DIR=iso/roudix-installer; DOMAIN=roudix-installer; LOCALE_DIR=src/roudix_installer/locale ;;
        welcome)   DIR=pkgs/roudix-welcome;  DOMAIN=roudix-welcome;   LOCALE_DIR=locale ;;
        switcher)  DIR=pkgs/roudix-switcher; DOMAIN=roudix-switcher;  LOCALE_DIR=locale ;;
        store)     DIR=pkgs/roudix-store;    DOMAIN=roudix-store;     LOCALE_DIR=locale ;;
        config)    DIR=pkgs/roudix-config;   DOMAIN=roudix-config;    LOCALE_DIR=locale ;;
        kernel-switcher) DIR=pkgs/roudix-kernel-switcher; DOMAIN=roudix-kernel-switcher; LOCALE_DIR=locale ;;
        hw-sync)   DIR=pkgs/roudix-hw-sync;  DOMAIN=roudix-hw-sync;   LOCALE_DIR=locale ;;
        scheduler) DIR=pkgs/roudix-scheduler-switcher; DOMAIN=roudix-scheduler; LOCALE_DIR=locale ;;
        firewall)  DIR=pkgs/roudix-firewall; DOMAIN=roudix-firewall; LOCALE_DIR=locale ;;
        disk)  DIR=pkgs/roudix-disk; DOMAIN=roudix-disk; LOCALE_DIR=locale ;;
        *) echo "i18n.sh: unknown component '$COMP' (one of: $ALL_COMPONENTS)" >&2; exit 2 ;;
    esac
    cd "$ROOT/$DIR"
    POT=po/$DOMAIN.pot
}

# Source files of the current component, relative to its directory.
sources() {
    case "$COMP" in
        installer) find src/roudix_installer -name '*.py' ;;
        store)     { ls -1 ./*.py | sed 's|^\./||'; find roudix_store -name '*.py'; } ;;
        *)         ls -1 ./*.py | sed 's|^\./||' ;;
    esac | LC_ALL=C sort
}

# Shell scripts of the current component whose messages are marked _t 'text' (extracted
# on top of the Python sources). Only roudix-hw-sync, the CLI next to its GUI, has one.
shell_sources() {
    case "$COMP" in
        hw-sync) echo roudix-hw-sync ;;
    esac
}

# Strings come from tr("…"), trc("context", "…") and tr_noop("…") — all in English —
# plus ngettext("one", "many", n), which xgettext knows by default, and _t '…' in shell scripts.
extract() {  # $1 = output .pot
    sources | xargs xgettext \
        --language=Python --from-code=UTF-8 \
        --keyword=tr --keyword=trc:1c,2 --keyword=tr_noop \
        --add-comments=TRANSLATORS \
        --add-location=file --sort-by-file \
        --package-name="$DOMAIN" --output="$1"
    local sh; sh=$(shell_sources)
    if [ -n "$sh" ]; then
        # No --sort-by-file here: the shell messages go after the Python ones.
        # shellcheck disable=SC2086  # $sh is a short list of file names without spaces
        xgettext --language=Shell --from-code=UTF-8 --keyword=_t \
            --add-comments=TRANSLATORS --add-location=file \
            --join-existing --output="$1" $sh
    fi
    # The creation date changes on every run and would make every diff noisy.
    sed -i '/^"POT-Creation-Date:/d' "$1"
}

stats() {  # prints "<lang>: N translated, M fuzzy, K untranslated"; sets BAD=1 on a problem
    local po=$1 out lang
    lang=$(basename "$po" .po)
    out=$(msgfmt --check --statistics -o /dev/null "$po" 2>&1) || { echo "$po: INVALID"; echo "$out"; BAD=1; return; }
    echo "$lang: $out"
    if grep -qE '[0-9]+ (fuzzy|untranslated)' <<<"$out"; then
        case "$REQUIRED_LANGS" in
            *" $lang "*) BAD=1 ;;
            *) echo "  ($lang is incomplete: not enforced, only$REQUIRED_LANGS must be complete)" ;;
        esac
    fi
}

cmd_update() {
    mkdir -p po
    extract "$POT"
    for po in po/*.po; do
        [ -e "$po" ] || continue
        msgmerge --update --backup=off --quiet "$po" "$POT"
        BAD=0; stats "$po"
    done
}

cmd_compile() {
    for po in po/*.po; do
        [ -e "$po" ] || continue
        lang=$(basename "$po" .po)
        mkdir -p "$LOCALE_DIR/$lang/LC_MESSAGES"
        msgfmt --check -o "$LOCALE_DIR/$lang/LC_MESSAGES/$DOMAIN.mo" "$po"
        echo "compiled: $lang"
    done
}

cmd_new() {  # $1 = language
    local lang=$1
    [ ! -e "po/$lang.po" ] || { echo "$DIR/po/$lang.po already exists" >&2; exit 1; }
    mkdir -p po
    extract "$POT"
    msginit --no-translator --locale="$lang" --input="$POT" --output-file="po/$lang.po"
    echo "created $DIR/po/$lang.po — translate it, then: scripts/i18n.sh compile $COMP"
}

cmd_check() {
    local tmp
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' RETURN
    extract "$tmp/new.pot"
    # 1. the committed .pot must match the current sources
    if ! diff -q <(msgcat --no-location "$POT") <(msgcat --no-location "$tmp/new.pot") >/dev/null; then
        echo "$DIR/$POT is out of date: run scripts/i18n.sh update $COMP"; BAD=1
    fi
    for po in po/*.po; do
        [ -e "$po" ] || continue
        # 2. same set of messages as the sources (nothing missing, nothing obsolete)
        if ! msgcmp --use-untranslated "$po" "$tmp/new.pot" 2>"$tmp/cmp.txt"; then
            echo "$DIR/$po does not match the sources:"; sed 's/^/  /' "$tmp/cmp.txt"; BAD=1
        fi
        # 3. complete and well-formed
        stats "$po"
    done
}

CMD=${1:-}
case "$CMD" in
    update|compile|check)
        shift
        COMPONENTS=${*:-$ALL_COMPONENTS}
        BAD=0
        for c in $COMPONENTS; do
            select_component "$c"
            echo "── $c"
            "cmd_$CMD"
        done
        if [ "$CMD" = check ]; then
            [ "$BAD" -eq 0 ] && echo "i18n OK" || { echo "i18n check FAILED (scripts/i18n.sh update, then translate)" >&2; exit 1; }
        fi
        ;;
    new)
        lang=${2:?usage: i18n.sh new <lang> [component…]   (e.g. de, es, pt_BR)}
        shift 2
        COMPONENTS=${*:-$ALL_COMPONENTS}
        for c in $COMPONENTS; do
            select_component "$c"
            cmd_new "$lang"
        done
        ;;
    *)
        sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac

#!/usr/bin/env bash
# release.sh — cut a release from CHANGELOG.md's [Unreleased] section.
#
# Run by .github/workflows/sync-main.yml right after testing is merged into main
# (the 1st and 15th), and usable by hand with --dry-run. It
#   1. picks the tag: v<YYYY.MM.DD> (calendar version, UTC) — a rolling distro has
#      no meaningful "major.minor", and the date tells users how fresh they are;
#   2. takes the notes from the curated [Unreleased] section of CHANGELOG.md. If it
#      is empty (a change landed without a changelog entry) it falls back to the
#      feat/fix commit subjects since the previous tag, so a release never ships
#      with blank notes;
#   3. renames [Unreleased] to [<tag>] - <date> and leaves a fresh empty
#      [Unreleased] above it;
#   4. writes the notes to $RELEASE_NOTES (default: release-notes.md) and, when
#      running in GitHub Actions, sets the `tag` / `notes` step outputs.
# It does NOT commit, tag or push — the workflow does, so a failure here cannot
# leave main half-released. Exit 0 with no `tag` output = nothing to release.
#
#   scripts/release.sh [--dry-run]     (--dry-run: print the notes, change nothing)
set -euo pipefail

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

cd "$(git rev-parse --show-toplevel)"
CHANGELOG=CHANGELOG.md
NOTES=${RELEASE_NOTES:-release-notes.md}
DATE=$(date -u +%Y.%m.%d)
TAG="v$DATE"

if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  echo "release: tag $TAG already exists — one release per day, nothing to do."
  exit 0
fi
grep -q '^## \[Unreleased\]' "$CHANGELOG" || { echo "release: no [Unreleased] section in $CHANGELOG" >&2; exit 1; }

# Body of [Unreleased]: everything up to the next "## [" heading, blank edges trimmed.
body=$(awk '
  /^## \[Unreleased\]/ { on = 1; next }
  on && /^## \[/       { exit }
  on                   { print }
' "$CHANGELOG" | sed -e '/./,$!d' | sed -e ':a' -e '/^\n*$/{$d;N;ba' -e '}')

FALLBACK=0
if [ -z "${body//[[:space:]]/}" ]; then
  prev=$(git describe --tags --abbrev=0 --match 'v[0-9]*' 2>/dev/null || true)
  if [ -z "$prev" ]; then
    echo "release: [Unreleased] is empty and there is no previous tag — nothing to release."
    exit 0
  fi
  body=$(git log --no-merges --format='%s' "$prev..HEAD" | grep -E '^(feat|fix)(\(|:|!)' | sed 's/^/- /' || true)
  if [ -z "$body" ]; then
    echo "release: no [Unreleased] entry and no feat/fix commit since $prev — nothing to release."
    exit 0
  fi
  FALLBACK=1
  echo "release: [Unreleased] was empty — notes taken from the feat/fix commits since $prev."
fi

if [ "$DRY" -eq 1 ]; then
  echo "── would release $TAG ──"
  printf '%s\n' "$body"
  exit 0
fi

printf '%s\n' "$body" > "$NOTES"

# Promote [Unreleased] -> [tag], keep an empty [Unreleased] on top.
tmp=$(mktemp)
awk -v tag="${TAG#v}" -v date="$(date -u +%Y-%m-%d)" -v fb="$FALLBACK" -v notes="$NOTES" '
  !done && /^## \[Unreleased\]/ {
    print; print ""; print "## [" tag "] - " date; done = 1
    if (fb) { print ""; print "### Changed"; while ((getline l < notes) > 0) print l }  # commit-derived entries
    next
  }
  { print }
' "$CHANGELOG" > "$tmp"
mv "$tmp" "$CHANGELOG"

echo "release: $TAG prepared ($(wc -l < "$NOTES") lines of notes in $NOTES)."
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  { echo "tag=$TAG"; echo "notes=$NOTES"; } >> "$GITHUB_OUTPUT"
fi

# Roudix — dev tasks. Run `just` to list them.
#
# Flake references use `path:.` (like `rebuild` does with path:$NH_FLAKE): plain
# `.#` only sees files tracked by git, and hardware-configuration.nix /
# username.nix / local.nix are gitignored on purpose.

_default:
    @just --list

# Evaluate ONE host without building — yours by default ($ROUDIX_HOST, else the hostname). e.g. `just check nixie`
check host="":
    #!/usr/bin/env bash
    set -euo pipefail
    host="{{host}}"
    [ -n "$host" ] || host="${ROUDIX_HOST:-$(hostname)}"
    if [ ! -f "hosts/$host/configuration.nix" ]; then
        echo "no host '$host'. Available: $(ls -d hosts/*/ | xargs -n1 basename | tr '\n' ' ')" >&2
        exit 1
    fi
    scripts/ci-stubs.sh create
    trap 'scripts/ci-stubs.sh remove' EXIT
    echo "==> eval $host"
    nix eval --raw --accept-flake-config \
        "path:.#nixosConfigurations.$host.config.system.build.toplevel.drvPath" >/dev/null
    echo "OK: $host evaluates"

# Evaluate EVERY host, like CI does (missing local files are stubbed, then cleaned up)
check-all:
    #!/usr/bin/env bash
    set -euo pipefail
    scripts/ci-stubs.sh create
    trap 'scripts/ci-stubs.sh remove' EXIT
    for dir in hosts/*/; do
        host="$(basename "$dir")"
        [ -f "hosts/$host/configuration.nix" ] || continue
        echo "==> eval $host"
        nix eval --raw --accept-flake-config \
            "path:.#nixosConfigurations.$host.config.system.build.toplevel.drvPath" >/dev/null
    done
    echo "OK: all hosts evaluate"

# Build a host's system closure (uses your real local files) — e.g. `just build roudix`
build host="roudix":
    nix build --accept-flake-config -L --no-link "path:.#nixosConfigurations.{{host}}.config.system.build.toplevel"

# statix (report only) + deadnix (fails on dead code) — same as CI
lint:
    nix run nixpkgs#statix -- check . || true
    nix run nixpkgs#deadnix -- --fail --no-lambda-pattern-names .

# Python: real errors only (syntax, undefined names) — same as CI
py:
    nix run nixpkgs#ruff -- check --select E9,F63,F7,F82 --no-cache pkgs iso scripts

# Stale repo-relative paths in pkgs/ and the installer — same as CI
paths:
    python3 scripts/check-path-refs.py

# Everything CI checks, in one go
ci: paths py lint check-all

# Regroupe les commits "auto:" de gitwatch en UN commit au vrai message (IA locale), à relire. Ajoute -n pour juste voir le message.
ship *args:
    python3 scripts/ai-commit.py squash {{args}}

# Commit de ce qui est stagé, avec un message généré (ouvre l'éditeur pour relire)
commit *args:
    python3 scripts/ai-commit.py commit {{args}}

# Update flake.lock
update:
    nix flake update

# Remove the ./result symlink
clean:
    rm -f result

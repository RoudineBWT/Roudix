# Changelog

All notable changes to Roudix are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); entries are grouped by
**Added / Changed / Fixed / Removed**. Changes land on `dev`, move to `testing`
once they build, then to `main` — so an entry shows up here when it reaches `main`.

## [Unreleased]

### Added
- `Justfile` (`just check`, `just ci`, …) and `scripts/ci-stubs.sh` to evaluate
  every host locally the same way CI does.
- `check-eval.yml`: every push / PR now evaluates all hosts and runs `ruff`
  (errors only), before the full build gate of the sync workflows.
- Issue templates (bug report, feature request).

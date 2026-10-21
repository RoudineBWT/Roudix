#!/usr/bin/env python3
"""ai-commit — proper commit messages for Roudix, written by a local LLM.

gitwatch keeps snapshotting the repo with cheap, deterministic "auto: ..."
commits (no network, nothing to wait for). This tool turns those snapshots
into real history when YOU decide the work is done:

  ai-commit.py squash      squash the trailing run of "auto:" commits into ONE
                           commit with a Conventional-Commits message
  ai-commit.py commit      message for what is staged, then open the editor
  ai-commit.py message     just print the message for what is staged

Nothing is sent anywhere unless you point it somewhere: by default the model
is an Ollama server on this machine. The prompt contains only the diff of
tracked files (secret-looking values are redacted, lock files / binaries are
summarised, size is capped). `--show-prompt` prints exactly what is sent.

If the model is unreachable or answers garbage, a plain deterministic message
is used instead — the tool never blocks you and never invents anything.

Environment:
  ROUDIX_AI_URL      Ollama base URL            (default http://127.0.0.1:11434)
  ROUDIX_AI_MODEL    model name                 (default qwen2.5-coder:14b)
  ROUDIX_AI_CMD      instead of Ollama: a command that reads the prompt on
                     stdin and prints the message, e.g. "claude -p"
  ROUDIX_AI_TIMEOUT  seconds to wait for the model (default 90)
  ROUDIX_AI_LANG     language of the message   (default English)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

URL = os.environ.get("ROUDIX_AI_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("ROUDIX_AI_MODEL", "qwen2.5-coder:14b")
CMD = os.environ.get("ROUDIX_AI_CMD", "")
TIMEOUT = int(os.environ.get("ROUDIX_AI_TIMEOUT", "90"))
LANG = os.environ.get("ROUDIX_AI_LANG", "English")

SERVICE = "roudix-gitwatch"
BACKUP_REF = "refs/roudix/pre-squash"

# What gitwatch (Roudix's commit script, or its default message) produces.
AUTO_RE = re.compile(r"^(auto:|Scripted auto-commit)")

MAX_TOTAL = 14000   # chars of diff sent to the model, all files together
MAX_FILE = 3500     # chars of diff per file
MAX_LISTED = 60     # files listed in the prompt
# Changes in these are summarised, not sent: noise for the model, no signal.
SKIP_NAMES = ("flake.lock",)
SKIP_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".irs",
            ".pack", ".ttf", ".otf", ".woff", ".woff2", ".lock")

HEADER_RE = re.compile(
    r"^(feat|fix|refactor|perf|docs|style|test|build|ci|chore|revert)"
    r"(\([a-z0-9][a-z0-9._/-]*\))?!?: \S")
MAX_HEADER = 72

SYSTEM = f"""You write git commit messages for Roudix, a NixOS-based Linux \
distribution (Nix modules, Python GTK tools, shell scripts, CI workflows).
Reply with ONLY the commit message: no preface, no code fences, no quotes.

Format (Conventional Commits):
  <type>(<scope>): <subject>

  <optional body>

Rules:
- type is one of: feat, fix, refactor, perf, docs, style, test, build, ci, chore.
- scope is short and lowercase (niri, store, kernel, installer, docs, ci...).
  Use the suggested scope if it fits; omit the scope if the change is broad.
- subject: imperative mood ("add", "fix"), lowercase, no trailing period, and
  the whole first line is at most {MAX_HEADER} characters.
- body: only if the change has several distinct parts. At most 6 short lines,
  each starting with "- ". Say what changed, and why only if the diff shows it.
- Describe ONLY what the diff shows. Never invent a reason, an issue number or
  a feature that is not visible in it.
- If the diff is only formatting or comments, use type style or chore.
- Write in {LANG}."""

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
     "<redacted private key>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "<redacted>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "<redacted>"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "<redacted>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<redacted>"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)(\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|\S+)"),
     r"\1\2<redacted>"),
]


class LLMError(Exception):
    pass


def log(msg: str) -> None:
    print(f"ai-commit: {msg}", file=sys.stderr)


def die(msg: str, code: int = 1):
    log(msg)
    raise SystemExit(code)


# ── git ──────────────────────────────────────────────────────────────────────
def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def in_repo() -> None:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0:
        die("not inside a git repository")
    os.chdir(r.stdout.strip())


# ── collecting the change ────────────────────────────────────────────────────
def collect(spec: list[str]) -> list[dict]:
    """[{path, status, add, dele, binary}] for `git diff <spec>` (no rename detection)."""
    status = {}
    for line in git("diff", *spec, "--name-status", "--no-renames").splitlines():
        s, _, p = line.partition("\t")
        status[p] = s[:1]
    files = []
    for line in git("diff", *spec, "--numstat", "--no-renames").splitlines():
        a, d, p = line.split("\t", 2)
        binary = a == "-"
        files.append({"path": p, "status": status.get(p, "M"),
                      "add": 0 if binary else int(a), "dele": 0 if binary else int(d),
                      "binary": binary})
    return files


def redact(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def skipped(f: dict) -> bool:
    p = f["path"]
    return f["binary"] or os.path.basename(p) in SKIP_NAMES or p.lower().endswith(SKIP_EXT)


def diff_bodies(spec: list[str], files: list[dict]) -> str:
    """Diff text for the model: small files first so that many small changes fit."""
    out, used, omitted = [], 0, 0
    for f in sorted(files, key=lambda f: f["add"] + f["dele"]):
        if skipped(f):
            continue
        body = git("diff", *spec, "-U2", "--no-color", "--no-renames", "--", f["path"])
        body = redact(body)
        if len(body) > MAX_FILE:
            body = body[:MAX_FILE] + "\n... (diff of this file truncated)\n"
        if used + len(body) > MAX_TOTAL:
            omitted += 1
            continue
        out.append(body)
        used += len(body)
    if omitted:
        out.append(f"\n... ({omitted} more file(s) not shown, size limit)\n")
    return "\n".join(out)


# ── heuristics (no model needed) ─────────────────────────────────────────────
def scope_of(path: str) -> str | None:
    parts = path.split("/")
    top = parts[0]
    if path == "flake.lock":
        return "deps"
    if path == "flake.nix":
        return "flake"
    if top == "pkgs" and len(parts) > 1:
        return re.sub(r"^roudix-", "", parts[1]) or None
    if top == "modules" and len(parts) > 2:
        if parts[1] == "home" and parts[2] == "desktop" and len(parts) > 3:
            return re.sub(r"\.nix$", "", parts[3]).lstrip("_") or "desktop"
        if parts[1] == "system" and parts[2] == "desktop" and len(parts) > 3:
            return re.sub(r"\.nix$", "", parts[3])
        return re.sub(r"\.nix$", "", parts[2])
    return {"hosts": "hosts", "docs": "docs", ".github": "ci", "scripts": "scripts",
            "iso": "installer", "assets": "assets", "dotfiles": "dotfiles"}.get(top) or (
        "installer" if path == "roudix-installer.sh" else "docs" if path.endswith(".md") else None)


def common_scope(files: list[dict]) -> str | None:
    """The one scope all files share. flake.lock rides along with almost any change,
    so it only decides when it is the only thing that changed."""
    real = [f for f in files if os.path.basename(f["path"]) not in SKIP_NAMES] or files
    scopes = {scope_of(f["path"]) for f in real}
    return scopes.pop() if len(scopes) == 1 else None


def fallback_message(files: list[dict], scope: str | None) -> str:
    """Honest, deterministic message: what files changed, nothing more."""
    paths = [f["path"] for f in files]
    if all(p.endswith(".md") or p.startswith("docs/") for p in paths):
        typ = "docs"
    elif all(p.startswith(".github/") for p in paths):
        typ = "ci"
    else:
        typ = "chore"
    head = f"{typ}({scope}): " if scope else f"{typ}: "
    head += f"update {os.path.basename(paths[0])}" if len(paths) == 1 else f"update {len(paths)} files"
    body = [f"- {f['status']} {f['path']} (+{f['add']}/-{f['dele']})" for f in files[:8]]
    if len(files) > 8:
        body.append(f"- ... and {len(files) - 8} more")
    return head + ("\n\n" + "\n".join(body) if len(files) > 1 else "")


def lock_only(files: list[dict]) -> bool:
    return bool(files) and all(f["path"] == "flake.lock" for f in files)


# ── the model ────────────────────────────────────────────────────────────────
def build_prompt(files: list[dict], scope: str | None, bodies: str) -> str:
    listing = [f"  {f['status']} {f['path']} (+{f['add']}/-{f['dele']})"
               + ("  [summarised, content not shown]" if skipped(f) else "")
               for f in files[:MAX_LISTED]]
    if len(files) > MAX_LISTED:
        listing.append(f"  ... and {len(files) - MAX_LISTED} more files")
    return (f"Suggested scope: {scope or '(none, broad change)'}\n"
            f"Files changed ({len(files)}):\n" + "\n".join(listing) +
            f"\n\nDiff:\n{bodies}\n")


def ask_llm(system: str, user: str, timeout: int) -> str:
    if CMD:
        try:
            r = subprocess.run(shlex.split(CMD), input=f"{system}\n\n{user}", text=True,
                               capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise LLMError(f"ROUDIX_AI_CMD failed: {e}")
        if r.returncode != 0:
            raise LLMError(f"ROUDIX_AI_CMD exited {r.returncode}: {r.stderr.strip()[:200]}")
        return r.stdout
    body = json.dumps({
        "model": MODEL, "stream": False,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(f"{URL}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)["message"]["content"]
    except urllib.error.HTTPError as e:
        hint = f" (try: ollama pull {MODEL})" if e.code == 404 else ""
        raise LLMError(f"model server answered HTTP {e.code}{hint}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LLMError(f"model server unreachable at {URL}: {getattr(e, 'reason', e)}")
    except (KeyError, ValueError) as e:
        raise LLMError(f"unexpected answer from the model server: {e}")


def clean(raw: str) -> tuple[str | None, str]:
    """Model output -> valid commit message, or (None, why it was rejected)."""
    t = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)
    t = "\n".join(l for l in t.splitlines() if not l.strip().startswith("```")).strip()
    t = re.sub(r"(?i)^(commit message|message)\s*:\s*", "", t)
    lines = t.splitlines()
    if not lines:
        return None, "empty answer"
    header = lines[0].strip().strip("`\"'").rstrip(".")
    if not HEADER_RE.match(header):
        return None, "first line is not '<type>(<scope>): <subject>'"
    if len(header) > MAX_HEADER:
        return None, f"first line is {len(header)} characters, the limit is {MAX_HEADER}"
    body = [l.rstrip() for l in lines[1:]]
    while body and not body[0]:
        body.pop(0)
    body = [l for i, l in enumerate(body) if l or (i and body[i - 1])][:10]
    return header + ("\n\n" + "\n".join(body) if body else ""), ""


def generate(files: list[dict], spec: list[str], offline: bool, show_prompt: bool,
             timeout: int) -> tuple[str, str]:
    scope = common_scope(files)
    if lock_only(files):
        return "chore(deps): update flake.lock", "rule"
    if offline:
        return fallback_message(files, scope), "fallback"
    user = build_prompt(files, scope, diff_bodies(spec, files))
    if show_prompt:
        print(f"--- system ---\n{SYSTEM}\n--- user ---\n{user}--- end ---", file=sys.stderr)
    feedback = ""
    for attempt in (1, 2):
        try:
            raw = ask_llm(SYSTEM, user + feedback, timeout)
        except LLMError as e:
            log(f"{e}; using the plain message")
            break
        msg, why = clean(raw)
        if msg:
            return msg, "ai"
        log(f"answer rejected ({why})" + ("; retrying" if attempt == 1 else "; using the plain message"))
        feedback = (f"\n\nYour previous answer was rejected: {why}. "
                    "Reply with ONLY the commit message in the required format.")
    return fallback_message(files, scope), "fallback"


# ── gitwatch service ─────────────────────────────────────────────────────────
def service_active() -> bool:
    if not shutil.which("systemctl"):
        return False
    r = subprocess.run(["systemctl", "--user", "is-active", "--quiet", SERVICE])
    return r.returncode == 0


def service(action: str) -> None:
    subprocess.run(["systemctl", "--user", action, SERVICE], capture_output=True)


# ── commands ─────────────────────────────────────────────────────────────────
def staged_message(args) -> tuple[str, str, list[dict]]:
    files = collect(["--cached"])
    if not files:
        die("nothing is staged (git add what you want in this commit first)")
    msg, how = generate(files, ["--cached"], args.offline, args.show_prompt, args.timeout)
    return msg, how, files


def cmd_message(args) -> int:
    msg, how, _ = staged_message(args)
    log(f"message written by: {how}")
    print(msg)
    return 0


def commit_with(msg: str, edit: bool) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
        t.write(msg + "\n")
        path = t.name
    try:
        return subprocess.run(["git", "commit", *(["-e"] if edit else []), "-F", path]).returncode
    finally:
        os.unlink(path)


def cmd_commit(args) -> int:
    msg, how, _ = staged_message(args)
    log(f"message written by: {how}")
    return commit_with(msg, edit=not args.yes)


def auto_run(include_pushed: bool) -> list[str]:
    """Hashes (newest first) of the trailing run of single-parent auto commits.

    By default only commits that are NOT on any remote: what is already pushed
    is never rewritten, the run simply stops there."""
    cmd = ["log", "--first-parent", "-n", "500", "--format=%H%x09%P%x09%s", "HEAD"]
    if not include_pushed:
        cmd += ["--not", "--remotes"]
    run = []
    for line in git(*cmd).splitlines():
        h, parents, subject = line.split("\t", 2)
        if len(parents.split()) != 1 or not AUTO_RE.match(subject):
            break
        run.append(h)
    return run


def cmd_squash(args) -> int:
    run = auto_run(args.allow_pushed)
    if not run:
        die("no unpushed 'auto:' commits at the tip of the branch, nothing to squash "
            "(already-pushed commits are left alone; --allow-pushed overrides)", 0)
    oldest = run[-1]
    base = git("rev-parse", f"{oldest}^").strip()

    if args.allow_pushed:
        remotes = git("for-each-ref", "--contains", oldest, "--format=%(refname:short)",
                      "refs/remotes").split()
        if remotes:
            log(f"warning: some of these commits are on {', '.join(remotes)}; "
                "you will have to `git push --force-with-lease` afterwards")

    spec = [base, "HEAD"]
    files = collect(spec)
    if not files:
        die("these commits cancel each other out (empty diff); nothing to describe", 1)
    msg, how = generate(files, spec, args.offline, args.show_prompt, args.timeout)

    print(f"{len(run)} commit(s) -> 1, {len(files)} file(s), message by: {how}\n", file=sys.stderr)
    print(msg + "\n")
    if args.dry_run:
        return 0

    was_active = service_active()
    if was_active:
        service("stop")                     # gitwatch must not commit mid-squash
    try:
        if git("status", "--porcelain").strip():
            die("uncommitted changes in the working tree (gitwatch had not committed them yet); "
                "wait for it, or commit/stash them, then re-run")
        git("update-ref", BACKUP_REF, "HEAD")
        git("reset", "--soft", base)
        if commit_with(msg, edit=not args.yes) != 0:
            git("reset", "--soft", BACKUP_REF)
            die("commit aborted, history restored")
        log(f"done. Undo with: git reset --soft {BACKUP_REF}")
        return 0
    finally:
        if was_active:
            service("start")


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--offline", action="store_true", help="don't call the model; plain message")
    common.add_argument("--show-prompt", action="store_true", help="print what is sent to the model")
    common.add_argument("--timeout", type=int, default=TIMEOUT, help="seconds to wait for the model")
    ap = argparse.ArgumentParser(description="AI-written commit messages for Roudix")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("message", parents=[common], help="print the message for the staged changes")
    c = sub.add_parser("commit", parents=[common],
                       help="commit the staged changes with a generated message")
    c.add_argument("-y", "--yes", action="store_true", help="don't open the editor")
    s = sub.add_parser("squash", parents=[common], help="squash the trailing gitwatch 'auto:' commits")
    s.add_argument("-y", "--yes", action="store_true", help="don't open the editor")
    s.add_argument("-n", "--dry-run", action="store_true", help="show the message, change nothing")
    s.add_argument("--allow-pushed", action="store_true",
                   help="squash even if those commits are already on a remote")
    args = ap.parse_args()
    in_repo()
    return {"message": cmd_message, "commit": cmd_commit, "squash": cmd_squash}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

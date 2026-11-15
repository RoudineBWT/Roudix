#!/usr/bin/env python3
"""
Roudix Installer — entry point. One installer, two front-ends:

    roudix-installer            asks graphical or terminal when run by hand in a terminal
                                on a desktop; graphical if launched without a terminal
                                (menu, autostart), terminal when there is no display
    roudix-installer --tui      terminal wizard (replaces the old roudix-installer.sh)
    roudix-installer --gui      graphical wizard (GTK4 / libadwaita)

    --dry-run                   only generate and check the configuration, never
                                partition, mount or install anything
    --lang CODE                 skip the language question (en, fr, es, pt_BR, …)

The GTK modules are imported only when the graphical wizard actually starts, so
the terminal one works where PyGObject is not installed.
"""
import argparse
import os
import sys


def _parse(argv):
    parser = argparse.ArgumentParser(prog="roudix-installer", add_help=True,
                                     description="Roudix installer (graphical or terminal wizard).")
    ui = parser.add_mutually_exclusive_group()
    ui.add_argument("--tui", dest="ui", action="store_const", const="tui", help="terminal wizard")
    ui.add_argument("--gui", dest="ui", action="store_const", const="gui", help="graphical wizard")
    parser.add_argument("--dry-run", action="store_true", help="generate and check the configuration only")
    parser.add_argument("--lang", help="language code, skips the question")
    # What is left is for GTK (Gio.Application options such as --gapplication-service).
    return parser.parse_known_args(argv)


def _has_display() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"))


def _ask_ui() -> str:
    """Ask graphical or terminal. Only called from an interactive terminal with a display,
    when nothing (--gui/--tui/ROUDIX_INSTALLER_UI) already decided."""
    print("Roudix installer - choose the interface:")
    print("  1) Graphical (GTK)   [default]")
    print("  2) Terminal (TUI)")
    try:
        answer = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(130)
    return "tui" if answer in {"2", "t", "tui", "terminal"} else "gui"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args, rest = _parse(argv)
    if args.dry_run:
        os.environ["ROUDIX_INSTALLER_DRY_RUN"] = "1"
    ui = args.ui or os.environ.get("ROUDIX_INSTALLER_UI", "").lower()
    if not ui:
        if _has_display() and sys.stdin.isatty() and sys.stdout.isatty():
            ui = _ask_ui()   # launched by hand from a terminal on a desktop: let the user pick
        else:
            ui = "gui" if _has_display() else "tui"   # desktop launcher, SSH, bare TTY: no question

    if ui == "gui":
        try:
            from roudix_installer import gui
        except (ImportError, ValueError) as exc:   # no PyGObject / GTK 4 / libadwaita
            if args.ui == "gui":
                print(f"roudix-installer: the graphical wizard is not available ({exc}).", file=sys.stderr)
                return 1
            print("roudix-installer: GTK is not available, starting the terminal wizard.", file=sys.stderr)
        else:
            if args.lang:
                from roudix_installer import i18n
                i18n.set_lang(args.lang)
            return gui.main([sys.argv[0], *rest])

    from roudix_installer import tui
    return tui.run(lang=args.lang)


if __name__ == "__main__":
    sys.exit(main())

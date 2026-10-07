from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw

from .ui import MainWindow


class RoudixStore(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.roudix.store")
        Adw.init()

    def do_activate(self) -> None:  # type: ignore[override]
        window = self.props.active_window or MainWindow(self)
        window.present()


def main() -> int:
    return RoudixStore().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())

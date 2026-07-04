from gi.repository import Adw, Gtk


def page_with_header(title: str, content: Gtk.Widget) -> Adw.ToolbarView:
    """
    Wraps page content in its own Adw.ToolbarView + Adw.HeaderBar.
    Adw.NavigationView only draws its automatic back button when the
    *current* page owns a header bar — a single shared window-level
    header (what the first version of this app used) never gets one.
    """
    toolbar = Adw.ToolbarView()
    header = Adw.HeaderBar()
    header.set_title_widget(Adw.WindowTitle(title=title))
    toolbar.add_top_bar(header)
    toolbar.set_content(content)
    return toolbar

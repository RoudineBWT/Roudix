#!/usr/bin/env python3
"""roudix-store — search nixpkgs, queue installs/removals, record them in local.nix.

Installs are written into a managed block of:
  user   -> ~/.config/roudix/modules/home/local.nix   (roudix.store.packages)
  system -> ~/.config/roudix/hosts/<host>/local.nix   (roudix.store.systemPackages)
then `nh os switch` is run. If the rebuild fails, the files are restored.
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time, urllib.request

NH_FLAKE = os.path.expanduser("~/.config/roudix")
HOST = os.environ.get("ROUDIX_HOST") or socket.gethostname()
FILES = {
    "home": (os.path.join(NH_FLAKE, "modules/home/local.nix"), "roudix.store.packages"),
    "system": (os.path.join(NH_FLAKE, "hosts", HOST, "local.nix"), "roudix.store.systemPackages"),
}
CACHE_DIR = os.path.expanduser("~/.cache/roudix-store")
INDEX_CACHE = os.path.join(CACHE_DIR, "index.json")
INDEX_URL = "https://channels.nixos.org/nixos-unstable/packages.json.br"
INDEX_MAX_AGE = 7 * 86400
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")
BEGIN = "# >>> roudix-store (managed by Roudix Store, edit with care) >>>"
END = "# <<< roudix-store <<<"
BLOCK_RE = re.compile(r"\n?[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*\n?", re.S)


def L(fr, en):
    return fr if os.environ.get("LANG", "").startswith("fr") else en


# ── local.nix managed block ───────────────────────────────────────────────

def read_block(path, key):
    """Package names currently in the managed block (empty if none)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    m = BLOCK_RE.search(text)
    if not m:
        return []
    return [n for n in re.findall(r'"([^"\n]+)"', m.group(0)) if NAME_RE.match(n)]


def render_block(key, names):
    items = "".join(f'    "{n}"\n' for n in sorted(set(names)))
    return f"  {BEGIN}\n  {key} = [\n{items}  ];\n  {END}\n"


def write_block(path, key, names):
    """Replace/insert the managed block. Returns True or an error string."""
    bad = [n for n in names if not NAME_RE.match(n)]
    if bad:
        return f"invalid package name: {bad[0]!r}"
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        text = "{ ... }:\n{\n}\n"
    except OSError as e:
        return str(e)
    body = render_block(key, names) if names else ""
    if BLOCK_RE.search(text):
        new = BLOCK_RE.sub(lambda _m: ("\n" + body) if body else "", text, count=1)
    elif not names:
        return True
    else:
        i = text.rstrip().rfind("}")
        if i < 0:
            return "no closing '}' found in " + path
        new = text[:i].rstrip("\n") + "\n\n" + body + text[i:]
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".store-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new)
        os.replace(tmp, path)
    except OSError as e:
        return str(e)
    return True


def backup_files():
    os.makedirs(CACHE_DIR, exist_ok=True)
    saved = {}
    for scope, (path, _k) in FILES.items():
        dst = os.path.join(CACHE_DIR, f"{scope}.local.nix.bak")
        if os.path.exists(path):
            shutil.copy2(path, dst)
            saved[scope] = dst
        else:
            saved[scope] = None
    return saved


def restore_files(saved):
    for scope, bak in saved.items():
        path = FILES[scope][0]
        if bak:
            shutil.copy2(bak, path)
        elif os.path.exists(path):
            os.remove(path)


# ── nixpkgs index ─────────────────────────────────────────────────────────

def _reduce(raw):
    pk = raw.get("packages", raw)
    out = {}
    for attr, p in pk.items():
        meta = p.get("meta") or {}
        desc = meta.get("description") or ""
        if not desc or not NAME_RE.match(attr):
            continue
        lic = meta.get("license")
        if isinstance(lic, list):
            lic = ", ".join(l.get("fullName", "") if isinstance(l, dict) else str(l) for l in lic)
        elif isinstance(lic, dict):
            lic = lic.get("fullName", "")
        home = meta.get("homepage")
        if isinstance(home, list):
            home = home[0] if home else ""
        out[attr] = {
            "pname": p.get("pname", attr), "version": p.get("version", ""),
            "desc": desc, "long": (meta.get("longDescription") or "")[:1500],
            "home": home or "", "license": lic or "", "prog": meta.get("mainProgram", ""),
            "unfree": bool(meta.get("unfree")),
        }
    return out


def load_index(force=False):
    if not force and os.path.exists(INDEX_CACHE) and time.time() - os.path.getmtime(INDEX_CACHE) < INDEX_MAX_AGE:
        with open(INDEX_CACHE, encoding="utf-8") as f:
            return json.load(f)
    import brotli
    req = urllib.request.Request(INDEX_URL, headers={"User-Agent": "roudix-store"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = json.loads(brotli.decompress(r.read()))
    idx = _reduce(raw)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(INDEX_CACHE, "w", encoding="utf-8") as f:
        json.dump(idx, f)
    return idx


def search(idx, query, limit=60):
    q = query.strip().lower()
    if len(q) < 2:
        return []
    scored = []
    for attr, p in idx.items():
        a = attr.lower()
        if a == q or p["prog"].lower() == q:
            s = 0
        elif a.startswith(q):
            s = 1
        elif q in a:
            s = 2
        elif q in p["desc"].lower():
            s = 3
        else:
            continue
        scored.append((s, len(attr), attr))
    scored.sort()
    return [a for _s, _l, a in scored[:limit]]


# ── GTK UI ────────────────────────────────────────────────────────────────

def main():
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk, GLib, Pango

    class Win(Adw.ApplicationWindow):
        def __init__(self, app):
            super().__init__(application=app, title="Roudix Store", default_width=1000, default_height=700)
            self.idx = {}
            self.installed = {s: set(read_block(p, k)) for s, (p, k) in FILES.items()}
            self.pending = {}          # attr -> (scope, "add"|"remove")
            self.current = None
            self.results = []

            # sidebar: search + results
            self.entry = Gtk.SearchEntry(placeholder_text=L("Rechercher une app…", "Search apps…"), hexpand=True)
            self.entry.connect("search-changed", self.on_search)
            self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
            self.listbox.add_css_class("navigation-sidebar")
            self.listbox.connect("row-selected", self.on_row)
            self.status = Gtk.Label(label=L("Chargement de l'index nixpkgs…", "Loading nixpkgs index…"), wrap=True, margin_top=12, margin_bottom=12)
            side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            side.append(self.entry)
            side.append(self.status)
            side.append(Gtk.ScrolledWindow(child=self.listbox, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
            side_tb = Adw.ToolbarView(content=side)
            hb = Adw.HeaderBar()
            refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text=L("Mettre à jour l'index", "Refresh index"))
            refresh.connect("clicked", lambda *_: self.fetch_index(True))
            hb.pack_end(refresh)
            side_tb.add_top_bar(hb)

            # detail
            self.title_l = Gtk.Label(xalign=0, wrap=True); self.title_l.add_css_class("title-1")
            self.sub_l = Gtk.Label(xalign=0, wrap=True); self.sub_l.add_css_class("dim-label")
            self.long_l = Gtk.Label(xalign=0, wrap=True, selectable=True)
            self.meta_l = Gtk.Label(xalign=0, wrap=True, use_markup=True)
            self.scope = Adw.ComboRow(title=L("Installer pour", "Install for"),
                                      model=Gtk.StringList.new([L("Utilisateur (home)", "User (home)"), L("Système", "System")]))
            self.action_btn = Gtk.Button(halign=Gtk.Align.START); self.action_btn.add_css_class("suggested-action")
            self.action_btn.connect("clicked", self.on_action)
            lst = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE); lst.add_css_class("boxed-list"); lst.append(self.scope)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
            for w in (self.title_l, self.sub_l, self.long_l, self.meta_l, lst, self.action_btn):
                box.append(w)
            self.detail_stack = Adw.ViewStack()
            self.detail_stack.add_named(Adw.StatusPage(icon_name="system-software-install-symbolic",
                                                       title=L("Choisis une application", "Pick an application")), "empty")
            self.detail_stack.add_named(Gtk.ScrolledWindow(child=Adw.Clamp(child=box, maximum_size=700)), "detail")

            # bottom bar: queue + apply + log
            self.queue_l = Gtk.Label(xalign=0, hexpand=True)
            self.apply_btn = Gtk.Button(label=L("Appliquer", "Apply"), sensitive=False); self.apply_btn.add_css_class("suggested-action")
            self.apply_btn.connect("clicked", self.on_apply)
            self.clear_btn = Gtk.Button(label=L("Vider", "Clear"), sensitive=False)
            self.clear_btn.connect("clicked", self.on_clear)
            bar = Gtk.Box(spacing=8, margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)
            for w in (self.queue_l, self.clear_btn, self.apply_btn):
                bar.append(w)
            self.log = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
            self.log_sw = Gtk.ScrolledWindow(child=self.log, min_content_height=180, visible=False)
            right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.detail_stack.set_vexpand(True)
            for w in (self.detail_stack, self.log_sw, Gtk.Separator(), bar):
                right.append(w)
            right_tb = Adw.ToolbarView(content=right)
            right_tb.add_top_bar(Adw.HeaderBar())

            split = Adw.OverlaySplitView(sidebar=side_tb, content=right_tb, min_sidebar_width=300, max_sidebar_width=420)
            self.set_content(split)
            self.fetch_index(False)

        # index / search
        def fetch_index(self, force):
            self.status.set_label(L("Chargement de l'index nixpkgs…", "Loading nixpkgs index…"))
            def work():
                try:
                    idx = load_index(force)
                    GLib.idle_add(self.index_ready, idx, None)
                except Exception as e:  # network, brotli missing, bad cache…
                    GLib.idle_add(self.index_ready, None, str(e))
            threading.Thread(target=work, daemon=True).start()

        def index_ready(self, idx, err):
            if err:
                self.status.set_label(L("Index indisponible : ", "Index unavailable: ") + err)
                return
            self.idx = idx
            self.status.set_label(L(f"{len(idx)} paquets — tape au moins 2 lettres.", f"{len(idx)} packages — type at least 2 letters."))
            self.on_search(self.entry)

        def on_search(self, entry):
            self.results = search(self.idx, entry.get_text()) if self.idx else []
            while (r := self.listbox.get_first_child()):
                self.listbox.remove(r)
            for attr in self.results:
                p = self.idx[attr]
                row = Adw.ActionRow(title=GLib.markup_escape_text(attr), subtitle=GLib.markup_escape_text(p["desc"]), activatable=True)
                row.set_subtitle_lines(2)
                row.attr = attr
                row.add_prefix(Gtk.Image.new_from_icon_name(self.icon_for(p)))
                row.set_name(attr)
                self.listbox.append(row)

        def icon_for(self, p):
            theme = Gtk.IconTheme.get_for_display(self.get_display())
            for n in (p["prog"], p["pname"]):
                if n and theme.has_icon(n):
                    return n
            return "application-x-executable"

        # detail
        def on_row(self, _lb, row):
            if row is None:
                return
            self.current = row.attr
            p = self.idx[self.current]
            self.title_l.set_label(self.current)
            self.sub_l.set_label(p["desc"])
            self.long_l.set_label(p["long"])
            self.long_l.set_visible(bool(p["long"]))
            bits = []
            if p["version"]: bits.append(f"<b>{L('Version','Version')}</b> {GLib.markup_escape_text(p['version'])}")
            if p["license"]: bits.append(f"<b>{L('Licence','License')}</b> {GLib.markup_escape_text(p['license'])}" + (" (unfree)" if p["unfree"] else ""))
            if p["home"]: bits.append(f"<a href=\"{GLib.markup_escape_text(p['home'])}\">{GLib.markup_escape_text(p['home'])}</a>")
            self.meta_l.set_markup("\n".join(bits))
            self.detail_stack.set_visible_child_name("detail")
            self.refresh_action()

        def state_of(self, attr):
            for scope in ("home", "system"):
                if attr in self.installed[scope]:
                    return scope
            return None

        def refresh_action(self):
            if not self.current:
                return
            sc = self.state_of(self.current)
            pend = self.pending.get(self.current)
            self.scope.set_sensitive(sc is None and pend is None)
            if pend:
                self.action_btn.set_label(L("Annuler la file", "Remove from queue"))
            elif sc:
                self.action_btn.set_label(L("Désinstaller", "Uninstall"))
            else:
                self.action_btn.set_label(L("Ajouter à la file", "Add to queue"))

        def on_action(self, _b):
            a = self.current
            if a in self.pending:
                del self.pending[a]
            elif (sc := self.state_of(a)):
                self.pending[a] = (sc, "remove")
            else:
                self.pending[a] = ("home" if self.scope.get_selected() == 0 else "system", "add")
            self.refresh_action(); self.refresh_queue()

        def on_clear(self, _b):
            self.pending.clear(); self.refresh_action(); self.refresh_queue()

        def refresh_queue(self):
            n = len(self.pending)
            self.apply_btn.set_sensitive(n > 0); self.clear_btn.set_sensitive(n > 0)
            adds = [a for a, (_s, k) in self.pending.items() if k == "add"]
            rms = [a for a, (_s, k) in self.pending.items() if k == "remove"]
            parts = []
            if adds: parts.append("+ " + ", ".join(adds))
            if rms: parts.append("− " + ", ".join(rms))
            self.queue_l.set_label("   ".join(parts) if parts else L("File vide", "Queue empty"))

        # apply
        def log_append(self, line):
            buf = self.log.get_buffer(); buf.insert(buf.get_end_iter(), line + "\n")
            adj = self.log_sw.get_vadjustment(); adj.set_value(adj.get_upper())

        def on_apply(self, _b):
            new = {s: set(v) for s, v in self.installed.items()}
            for a, (sc, kind) in self.pending.items():
                (new[sc].add if kind == "add" else new[sc].discard)(a)
            saved = backup_files()
            for sc, (path, key) in FILES.items():
                if new[sc] != self.installed[sc]:
                    res = write_block(path, key, sorted(new[sc]))
                    if res is not True:
                        restore_files(saved)
                        self.status.set_label(L("Écriture impossible : ", "Write failed: ") + res)
                        return
            self.apply_btn.set_sensitive(False); self.clear_btn.set_sensitive(False)
            self.log_sw.set_visible(True)
            self.log.get_buffer().set_text("")
            threading.Thread(target=self.rebuild, args=(saved, new), daemon=True).start()

        def rebuild(self, saved, new):
            cmd = ["nh", "os", "switch", "--elevation-strategy", "pkexec", "--accept-flake-config", f"path:{NH_FLAKE}"]
            GLib.idle_add(self.log_append, "$ " + " ".join(cmd))
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    GLib.idle_add(self.log_append, line.rstrip())
                ok = proc.wait() == 0
            except OSError as e:
                GLib.idle_add(self.log_append, str(e)); ok = False
            GLib.idle_add(self.rebuild_done, ok, saved, new)

        def rebuild_done(self, ok, saved, new):
            if ok:
                self.installed = new; self.pending.clear()
                self.status.set_label(L("✓ Appliqué.", "✓ Applied."))
            else:
                restore_files(saved)
                self.status.set_label(L("✗ Échec — local.nix restauré.", "✗ Failed — local.nix restored."))
            self.refresh_action(); self.refresh_queue()

    class App(Adw.Application):
        def __init__(self):
            super().__init__(application_id="io.roudix.store")
        def do_activate(self):
            (self.props.active_window or Win(self)).present()

    sys.exit(App().run(sys.argv))


if __name__ == "__main__":
    main()

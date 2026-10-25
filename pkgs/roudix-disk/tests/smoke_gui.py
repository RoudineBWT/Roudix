"""GUI smoke test under Xvfb with fake lsblk data and fake rebuilds.
   xvfb-run -a python3 tests/smoke_gui.py <hardware-configuration.nix> <out.png>"""
import os, sys, json, tempfile, subprocess, importlib.util, importlib.machinery
from pathlib import Path

hw_src, shot = Path(sys.argv[1]), sys.argv[2]
td = Path(tempfile.mkdtemp())
(td / "flake/hosts/roudix").mkdir(parents=True)
(td / "flake/hosts/roudix/hardware-configuration.nix").write_text(hw_src.read_text())
os.environ.update(NH_FLAKE=str(td / "flake"), ROUDIX_HOST="roudix", XDG_STATE_HOME=str(td / "state"),
                  GSK_RENDERER="cairo", GDK_BACKEND="x11", LANGUAGE="en")

HERE = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("rd", str(HERE / "roudix-disk.py"))
spec = importlib.util.spec_from_loader("rd", loader); rd = importlib.util.module_from_spec(spec); loader.exec_module(rd)

LSBLK = {"blockdevices": [
  {"name": "nvme0n1", "path": "/dev/nvme0n1", "size": 1000204886016, "model": "Samsung SSD 980 1TB", "type": "disk", "rm": False, "rota": False,
   "children": [
     {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "size": 4294967296, "type": "part", "fstype": "vfat", "uuid": "E00D-27FB", "mountpoints": ["/boot"]},
     {"name": "nvme0n1p2", "path": "/dev/nvme0n1p2", "size": 995909918720, "type": "part", "fstype": "btrfs", "uuid": "efd3a1ff-c992-4d9e-a45a-3142a90f4229", "mountpoints": ["/nix/store", "/var/log", "/nix", "/home", "/"]}]},
  {"name": "sda", "path": "/dev/sda", "size": 2000398934016, "model": "WD Elements 25A2", "type": "disk", "rm": True, "rota": True,
   "children": [{"name": "sda1", "path": "/dev/sda1", "size": 2000397795328, "type": "part", "fstype": "ntfs", "label": "Backup & Co", "uuid": "5A3C1F2B3C1F0000", "mountpoints": []}]},
  {"name": "sdb", "path": "/dev/sdb", "size": 500107862016, "model": "Crucial MX500", "type": "disk", "rm": False, "rota": False,
   "children": [{"name": "sdb1", "path": "/dev/sdb1", "size": 500106788864, "type": "part", "fstype": "ext4", "label": "Games", "uuid": "aaaa-bbbb-cccc", "mountpoints": []}]},
  {"name": "sdc", "path": "/dev/sdc", "size": 64023257088, "model": "USB Flash", "type": "disk", "rm": True, "rota": False, "children": []},
]}
rd._lsblk_json = lambda *a: LSBLK

import gi
from gi.repository import GLib
hwf = Path(os.environ["NH_FLAKE"]) / "hosts/roudix/hardware-configuration.nix"
orig = hwf.read_text()
results = []
def check(name, cond): results.append((name, bool(cond))); print(("ok   " if cond else "FAIL ") + name)

app = rd.App()
state = {}

def rows(win):
    out = []
    for g in win._groups:
        out.append(g.get_title())
    return out

def step1():
    win = app.props.active_window; state["win"] = win
    check("window built, 4 disk groups", len(win._groups) == 4)
    check("no pending changes at start", not win.dirty and not win.apply_btn.get_sensitive())
    check("model with & is escaped in titles", all("&" not in (t or "").replace("&amp;", "") for t in rows(win)))
    # add a mount for sdb1 (Games), through the same code path as the dialog
    sdb = next(d for d in win.disks if d.name == "sdb")
    part = sdb.partitions[0]
    win.entries.append(rd.MountEntry("/media/Games", part.uuid_path, "ext4", rd.default_options("ext4", False, 1000, 100)))
    sda = next(d for d in win.disks if d.name == "sda")
    win.entries.append(rd.MountEntry("/media/Backup", sda.partitions[0].uuid_path, rd.nix_fstype("ntfs"),
                                     rd.default_options("ntfs3", True, 1000, 100)))
    win.render()
    check("dirty after adding", win.dirty and win.apply_btn.get_sensitive() and win.pending_banner.get_revealed())
    check("missing banner shown (fake uuids don't exist in /dev)", win.missing_banner.get_revealed())
    # screenshot of the 'pending' state
    GLib.timeout_add(700, shot_and_continue)
    return False

def shot_and_continue():
    subprocess.run(["import", "-window", "root", shot], check=False)
    GLib.timeout_add(100, step2); return False

def step2():
    win = state["win"]
    # successful apply
    rd.rebuild_cmd = lambda mode: ["sh", "-c", f"echo fake nh os {mode}; exit 0"]
    win._do_apply("switch")
    GLib.timeout_add(1500, step3); return False

def step3():
    win = state["win"]
    txt = hwf.read_text()
    check("file written with managed block", "# >>> roudix-disk" in txt and 'fileSystems."/media/Games"' in txt)
    check("protected blocks intact", all(s in txt for s in ['fileSystems."/home"', 'subvol=nix', 'fmask=0077']))
    check("ntfs written as ntfs3", 'fsType = "ntfs3"' in txt)
    check("after success: reloaded, not dirty", not win.dirty and len(win.saved_entries) == 2)
    check("backup exists", any((Path(os.environ["XDG_STATE_HOME"]) / "roudix-disk/backups").glob("roudix-*.nix")))
    # now a failing rebuild: remove one entry, apply, expect restore + still dirty
    win.entries = [e for e in win.entries if e.mountpoint != "/media/Backup"]; win.render()
    before = hwf.read_text()
    rd.rebuild_cmd = lambda mode: ["sh", "-c", "echo boom; exit 1"]
    win._do_apply("boot")
    GLib.timeout_add(1500, step4, before); return False

def step4(before):
    win = state["win"]
    check("failed rebuild: file restored", hwf.read_text() == before)
    check("failed rebuild: edits kept (still dirty)", win.dirty and len(win.entries) == 1)
    check("failed rebuild: error banner shown", win.error_banner.get_revealed())
    # pkexec cancelled (126) message
    rd.rebuild_cmd = lambda mode: ["sh", "-c", "exit 126"]
    win._do_apply("switch")
    GLib.timeout_add(1200, step5); return False

def step5():
    win = state["win"]
    check("pkexec cancelled: message says nothing changed", "nothing was changed" in win.error_banner.get_title())
    for w in list(app.get_windows()): w.destroy()
    app.quit(); return False

def on_activate(a):
    GLib.timeout_add(800, step1)
app.connect("activate", lambda a: None)
app.connect("activate", on_activate)
rc = app.run([sys.argv[0]])
bad = [n for n, ok in results if not ok]
print("\nGUI SMOKE:", "ALL PASSED" if not bad and results else f"FAILED {bad}")
sys.exit(1 if bad or not results else 0)

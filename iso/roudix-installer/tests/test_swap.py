"""Temporary install swap: when to add it, how big, on which filesystem."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from roudix_installer import swap  # noqa: E402

GIB = 1024 ** 3
KIB_GIB = 1024 * 1024


class Plan(unittest.TestCase):
    def test_8_gib_machine_gets_a_swap_file(self):
        mib, why = swap.plan(int(7.6 * KIB_GIB), 0, 100 * GIB)
        self.assertEqual(why, "")
        self.assertEqual(mib, 8 * 1024)           # capped at MAX_SWAP_GIB

    def test_12_gib_machine_gets_less(self):
        mib, _ = swap.plan(12 * KIB_GIB, 0, 100 * GIB)
        self.assertEqual(mib, 4 * 1024)

    def test_enough_memory_or_swap_needs_nothing(self):
        self.assertEqual(swap.plan(16 * KIB_GIB, 0, 100 * GIB), (0, "no-need"))
        self.assertEqual(swap.plan(8 * KIB_GIB, 8 * KIB_GIB, 100 * GIB), (0, "no-need"))
        self.assertEqual(swap.plan(0, 0, 100 * GIB), (0, "no-need"))   # unreadable /proc/meminfo

    def test_small_target_disk_is_respected(self):
        self.assertEqual(swap.plan(8 * KIB_GIB, 0, 13 * GIB)[1], "no-space")   # 12 GiB kept free, 1 left
        mib, why = swap.plan(8 * KIB_GIB, 0, 16 * GIB)                         # 4 GiB to spare
        self.assertEqual((mib, why), (4 * 1024, ""))


class Zram(unittest.TestCase):
    def test_low_memory(self):
        self.assertTrue(swap.low_memory(8 * KIB_GIB, 0))
        self.assertFalse(swap.low_memory(16 * KIB_GIB, 0))
        self.assertFalse(swap.low_memory(8 * KIB_GIB, 8 * KIB_GIB))
        self.assertFalse(swap.low_memory(0, 0))

    def test_zram_size_follows_ram_with_a_cap(self):
        self.assertEqual(swap.zram_size_mib(4 * KIB_GIB), 4096)
        self.assertEqual(swap.zram_size_mib(int(7.6 * KIB_GIB)), 7680)
        self.assertEqual(swap.zram_size_mib(32 * KIB_GIB), 8192)


class Parsing(unittest.TestCase):
    def test_meminfo(self):
        self.assertEqual(swap.read_meminfo("MemTotal:  7840000 kB\nSwapTotal:  1024 kB\nX: 1 kB\n"), (7840000, 1024))

    def test_fstype_of_picks_the_deepest_mount(self):
        mounts = ("tmpfs / tmpfs rw 0 0\n/dev/vda2 /mnt btrfs rw 0 0\n/dev/vda2 /mnt/nix btrfs rw 0 0\n"
                  "/dev/vda1 /mnt/boot vfat rw 0 0\n")
        self.assertEqual(swap.fstype_of("/mnt", mounts), "btrfs")
        self.assertEqual(swap.fstype_of("/mnt/boot", mounts), "vfat")
        self.assertEqual(swap.fstype_of("/mntx", mounts), "tmpfs")


if __name__ == "__main__":
    unittest.main()

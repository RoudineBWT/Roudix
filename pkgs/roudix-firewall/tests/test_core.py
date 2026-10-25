#!/usr/bin/env python3
# Run: python3 pkgs/roudix-firewall/tests/test_core.py   (no GTK needed)
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import roudix_firewall_core as fw  # noqa: E402


def sample() -> fw.Config:
    return fw.Config(
        enabled=True,
        rules=[
            fw.Rule("SSH", "tcp", [(22, 22)]),
            fw.Rule("Steam", "both", [(27015, 27030)]),
            fw.Rule("Web \"quoted\" é\nname", "tcp", [(80, 80), (443, 443), (8000, 8010)]),
            fw.Rule("Off", "udp", [(1234, 1234)], enabled=False),
        ],
        trusted_interfaces=["docker0", "virbr0"],
    )


class PortSpec(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(fw.parse_port_spec("443, 80 8000-8010;80"),
                         [(80, 80), (443, 443), (8000, 8010)])
        self.assertEqual(fw.format_port_spec([(80, 80), (1, 5)]), "80, 1-5")

    def test_bad(self):
        for bad in ("", "abc", "0", "65536", "90-80", "1-2-3", "80,,x"):
            with self.assertRaises(fw.FirewallError, msg=bad):
                fw.parse_port_spec(bad)


class Generate(unittest.TestCase):
    def test_nix_content(self):
        out = fw.generate(sample())
        self.assertIn("enable = lib.mkForce true;", out)
        self.assertIn("allowedTCPPorts = [ 22 80 443 ];", out)
        self.assertNotIn("1234", out.split("\n{ lib")[1])           # disabled rule not emitted
        self.assertIn("{ from = 27015; to = 27030; }", out)
        self.assertIn('trustedInterfaces = [ "docker0" "virbr0" ];', out)
        # exactly one metadata line, pure ASCII, no raw newline from the rule name
        meta = [l for l in out.splitlines() if l.startswith("# roudix-firewall:v1 ")]
        self.assertEqual(len(meta), 1)
        self.assertTrue(meta[0].isascii())

    def test_both_goes_to_tcp_and_udp(self):
        body = fw.generate(sample())
        self.assertEqual(body.count("{ from = 27015; to = 27030; }"), 2)

    def test_disabled_firewall(self):
        c = sample()
        c.enabled = False
        self.assertIn("enable = lib.mkForce false;", fw.generate(c))

    def test_rejects_bad_data(self):
        for c in (fw.Config(rules=[fw.Rule("x", "icmp", [(1, 1)])]),
                  fw.Config(rules=[fw.Rule("x", "tcp", [])]),
                  fw.Config(rules=[fw.Rule("x", "tcp", [(0, 5)])]),
                  fw.Config(trusted_interfaces=['a"; evil = "']),
                  fw.Config(trusted_interfaces=["x" * 16])):
            with self.assertRaises(fw.FirewallError):
                fw.generate(c)


class RoundTrip(unittest.TestCase):
    def test_roundtrip_keeps_names_and_disabled_rules(self):
        c = sample()
        back = fw.parse(fw.generate(c))
        self.assertEqual(back.origin, "metadata")
        self.assertEqual(back.snapshot(), fw.Config(
            c.enabled, [fw.Rule(fw.clean_name(r.name), r.proto, r.spec, r.enabled) for r in c.rules],
            c.trusted_interfaces).snapshot())
        self.assertFalse(back.rules[3].enabled)

    def test_hand_edit_wins_and_names_survive(self):
        text = fw.generate(sample()).replace("allowedTCPPorts = [ 22 80 443 ];",
                                             "allowedTCPPorts = [ 22 9999 ];")
        back = fw.parse(text)
        self.assertEqual(back.origin, "nix")
        tcp = {r.spec[0][0]: r.name for r in back.rules if r.proto == "tcp" and r.spec[0][0] == r.spec[0][1]}
        self.assertEqual(tcp[22], "SSH")          # name recovered
        self.assertEqual(tcp[9999], "TCP 9999")   # new port from the hand edit
        self.assertNotIn(80, tcp)
        self.assertEqual(back.trusted_interfaces, ["docker0", "virbr0"])

    def test_foreign_file(self):
        back = fw.parse("{ ... }: { networking.firewall = { enable = false;\n"
                        "allowedUDPPorts = [ 53 ];\n"
                        "allowedUDPPortRanges = [ { from = 1000; to = 2000; } ]; }; }")
        self.assertEqual(back.origin, "nix")
        self.assertFalse(back.enabled)
        self.assertEqual([(r.proto, r.spec) for r in back.rules],
                         [("udp", [(53, 53)]), ("udp", [(1000, 2000)])])

    def test_corrupt_metadata_falls_back(self):
        back = fw.parse("# roudix-firewall:v1 {not json}\n{ ... }: { networking.firewall.enable = true; }")
        self.assertEqual(back.origin, "nix")


class Disk(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        fw.NH_FLAKE = self.tmp.name
        fw.ROUDIX_HOST = "testhost"
        os.makedirs(fw.host_dir())

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_load_backup_restore(self):
        self.assertEqual(fw.load().origin, "new")
        self.assertIsNone(fw.read_previous())
        fw.save(sample())
        self.assertEqual(fw.load().origin, "metadata")
        first = fw.read_previous()
        c2 = sample()
        c2.rules.pop(0)
        fw.save(c2)
        self.assertTrue(os.path.exists(fw.firewall_file() + ".bak"))
        with open(fw.firewall_file() + ".bak") as f:
            self.assertEqual(f.read(), first)
        fw.restore(first)
        self.assertEqual(fw.read_previous(), first)
        fw.restore(None)
        self.assertFalse(os.path.exists(fw.firewall_file()))
        self.assertEqual([f for f in os.listdir(fw.host_dir()) if f.endswith(".tmp")], [])

    def test_save_validates_before_touching_disk(self):
        with self.assertRaises(fw.FirewallError):
            fw.save(fw.Config(trusted_interfaces=["bad iface"]))
        self.assertFalse(os.path.exists(fw.firewall_file()))

    def test_missing_host_dir(self):
        os.rmdir(fw.host_dir())
        with self.assertRaises(fw.FirewallError):
            fw.save(sample())

    def test_banners(self):
        self.assertTrue(fw.host_imports_firewall_file())           # no configuration.nix: stay quiet
        with open(os.path.join(fw.host_dir(), "configuration.nix"), "w") as f:
            f.write("{ imports = [ ./local.nix ]; }")
        self.assertFalse(fw.host_imports_firewall_file())
        with open(os.path.join(fw.host_dir(), "configuration.nix"), "w") as f:
            f.write("lib.optional (builtins.pathExists ./firewall.local.nix) ./firewall.local.nix")
        self.assertTrue(fw.host_imports_firewall_file())
        with open(fw.local_nix_file(), "w") as f:
            f.write("# networking.firewall.x = 1;\n  networking.firewall.allowedTCPPorts = [ 25565 ];\n")
        self.assertEqual(fw.local_nix_firewall_lines(),
                         ["networking.firewall.allowedTCPPorts = [ 25565 ];"])


class Presets(unittest.TestCase):
    def test_all_presets_are_valid(self):
        for _cat, name, proto, ports in fw.PRESETS:
            self.assertIn(proto, fw.PROTOS, name)
            fw.parse_port_spec(ports)
        for iface, _ in fw.INTERFACE_PRESETS:
            self.assertTrue(fw.valid_interface(iface), iface)


if __name__ == "__main__":
    unittest.main(verbosity=1)

#!/usr/bin/env python3
"""Liste les noms d'icônes de cosmic-icons que Roudix ne fournit pas encore (aucun = couverture COSMIC complète).

Usage : check_cosmic.py <cosmic-icons (dépôt)> [<Roudix racine>]
"""
import os, sys
COS = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
total = 0
for variant in ("Roudix", "Roudix-Light"):
    have = {f[:-4] for r, _, fs in os.walk(os.path.join(ROOT, variant)) for f in fs if f.endswith(".svg")}
    want = {}
    for src in ("freedesktop", "extra"):
        base = os.path.join(COS, src, "scalable")
        for ctx in os.listdir(base):
            for f in os.listdir(os.path.join(base, ctx)):
                if f.endswith(".svg"): want[f[:-4]] = ctx
    miss = sorted(n for n in want if n not in have)
    total += len(miss)
    print(f"{variant}: {len(want)} noms COSMIC, {len(miss)} manquants")
    for n in miss: print(f"  {want[n]}/{n}")
sys.exit(1 if total else 0)

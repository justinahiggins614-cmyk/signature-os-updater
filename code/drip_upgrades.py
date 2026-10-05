#!/usr/bin/env python3
"""2h drip: append N upgrade packs (default 200). Usage: python3 code/drip_upgrades.py --n 200"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import gen_upgrades as G

n = 200
for i, a in enumerate(sys.argv[1:]):
    if a == "--n" and i + 1 < len(sys.argv[1:]):
        n = int(sys.argv[1:][i + 1])
    elif a.startswith("--n="):
        n = int(a.split("=")[1])

packs = G.load()
start = len(packs) + 1
for i in range(start, start + n):
    packs.append(G.make_pack(i))
G.save(packs)
print("packs=%d (+%d)" % (len(packs), n))

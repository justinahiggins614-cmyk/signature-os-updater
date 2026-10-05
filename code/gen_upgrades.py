#!/usr/bin/env python3
"""Seed + drip generator for JAH-UPG upgrade packs (The Signature OS Updater).
Deterministic: same index -> same pack, forever. Only appends; never rewrites history.
Usage: python3 code/gen_upgrades.py --seed 600   (initial seed)
       python3 code/drip_upgrades.py --n 200      (2h drip append)
"""
import json, os, random, sys, datetime

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA, exist_ok=True)

ERAS = ["1990s", "2000s", "2010s", "modern"]
OSS = ["Windows", "macOS", "Linux"]
FOCUS = ["office", "creative", "coding", "school", "web", "gaming", "general"]

FOCUS_LABEL = {"office": "Office work", "creative": "Creative work", "coding": "Coding & building",
               "school": "School & study", "web": "Web & email", "gaming": "Games & play", "general": "Everyday use"}

BASE_COMPONENTS = ["apps", "tools", "lenses", "pc_models", "software", "ai_sweeper", "sweep"]

def components_for(era, focus):
    comps = list(BASE_COMPONENTS)
    if era in ("2010s", "modern"):
        comps.append("ai_offline")
    comps.append("ai_online")
    if focus == "coding":
        comps = ["tools", "lenses"] + [c for c in comps if c not in ("tools", "lenses")]
    elif focus == "creative":
        comps = ["apps", "lenses"] + [c for c in comps if c not in ("apps", "lenses")]
    elif focus == "office":
        comps = ["apps", "software"] + [c for c in comps if c not in ("apps", "software")]
    return comps

def make_pack(i):
    """i is 1-based pack number."""
    rng = random.Random(1000000 + i)
    era = ERAS[(i - 1) % 4]
    os_ = OSS[((i - 1) // 4) % 3]
    focus = FOCUS[((i - 1) // 12) % 7]
    variant = (i - 1) // 84 + 1
    title_bits = {
        "office": "Office Renewal", "creative": "Creator Refresh", "coding": "Builder Tune-Up",
        "school": "Study Revival", "web": "Web Ready", "gaming": "Play Boost", "general": "Full Refresh"}[focus]
    title = "%s %s \u2014 %s %s" % (era.capitalize(), os_, title_bits,
                                    ("Mk %d" % variant) if variant > 1 else "")
    blurbs = {
        "office": "Documents, email and video calls running smooth on your %s %s machine." % (era, os_),
        "creative": "Art, music and video tools refreshed for %s-era %s." % (era, os_),
        "coding": "Editors, terminals and dev tools tuned for %s %s." % (era, os_),
        "school": "Study apps, notes and research tools on %s %s, good as new." % (era, os_),
        "web": "A fast, safe modern web on your %s %s machine." % (era, os_),
        "gaming": "Honest tune-up for play on %s %s \u2014 we say plainly what old hardware can and can't run." % (era, os_),
        "general": "The complete refresh: every compatible upgrade for %s %s." % (era, os_)}
    return {"id": "JAH-UPG-%06d" % i, "title": title.strip(), "era": era, "os": os_,
            "focus": focus, "focus_label": FOCUS_LABEL[focus],
            "components": components_for(era, focus), "blurb": blurbs[focus],
            "best": (i == 1)}

def load():
    p = os.path.join(DATA, "upgrades.json")
    if os.path.exists(p):
        return json.load(open(p))
    return []

def save(packs):
    json.dump(packs, open(os.path.join(DATA, "upgrades.json"), "w"))
    json.dump({"packs": len(packs), "updated": datetime.date.today().isoformat(),
               "goal": 1000000, "prefix": "JAH-UPG-"},
              open(os.path.join(DATA, "manifest.json"), "w"), indent=1)

def main():
    n = 600
    for a in sys.argv[1:]:
        if a == "--seed" :
            pass
        elif a.startswith("--n"):
            n = int(a.split("=")[1] if "=" in a else sys.argv[sys.argv.index(a) + 1])
    packs = load()
    start = len(packs) + 1
    for i in range(start, start + n):
        packs.append(make_pack(i))
    save(packs)
    print("packs=%d (+%d)" % (len(packs), n))

if __name__ == "__main__":
    main()

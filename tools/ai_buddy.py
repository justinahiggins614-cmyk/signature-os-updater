#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch - your on-machine AI buddy for the Signature OS overlay.

A conversational assistant that ships with the overlay toolkit. It knows your
machine's upgrade state (system check results, applied patches, sweeper
findings, health-check status), talks in natural sentences, answers questions
about your PC, recommends next steps, and runs safe actions only with your
confirmation.

Pure stdlib, Python 3.6+. No network. Never touches anything outside the
SignatureOS folder except the sweeper's own safe temp/cache cleaning, and only
ever with your say-so.

Usage:
  python3 ai_buddy.py                  chat with Patch
  python3 ai_buddy.py --ask "question" one question, one answer
  python3 ai_buddy.py --test-qa       scripted Q&A self-test (needs a temp install)
"""

from __future__ import print_function

import importlib.util
import json
import os
import re
import sys

VERSION = "1.0.0"
FOLDER_NAME = "SignatureOS"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_overlay():
    """Import signature_os_overlay from next to this file. Returns module or None."""
    path = os.path.join(SCRIPT_DIR, "signature_os_overlay.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("signature_overlay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OVERLAY = None


def overlay():
    global OVERLAY
    if OVERLAY is None:
        OVERLAY = load_overlay()
    return OVERLAY


def find_install():
    """Locate the SignatureOS folder: home dir default, else cwd."""
    ov = overlay()
    for target in (os.path.expanduser("~"), os.getcwd()):
        if ov:
            root = ov.find_root(target)
        else:
            root = os.path.join(os.path.abspath(target), FOLDER_NAME)
        if os.path.isfile(os.path.join(root, "manifest.json")):
            return root
    return None


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def read_head(path, lines=14):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            out = []
            for _ in range(lines):
                line = fh.readline()
                if not line:
                    break
                out.append(line.rstrip())
            return "\n".join(out)
    except Exception:
        return ""


def load_state():
    """Everything Patch knows about this machine's upgrade state."""
    state = {"installed": False, "root": None, "machine": {}, "components": [],
             "installed_at": None, "sweep_report": None, "full_sweep": None}
    root = find_install()
    if not root:
        return state
    state["installed"] = True
    state["root"] = root
    man = read_json(os.path.join(root, "manifest.json")) or {}
    state["machine"] = man.get("machine") or {}
    state["components"] = man.get("components") or []
    state["installed_at"] = man.get("installed_at")
    for name in ("ai_sweep_report.txt", "tools/ai_sweep_report.txt"):
        head = read_head(os.path.join(root, name))
        if head:
            state["sweep_report"] = head
            break
    fs = read_head(os.path.join(root, "FULL_SWEEP.txt"))
    if fs:
        state["full_sweep"] = fs
    return state


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

def pick(variants, seed):
    h = 0
    for ch in seed:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return variants[h % len(variants)]


def machine_line(state):
    m = state["machine"]
    if not m:
        return "I couldn't find a saved machine profile."
    bits = []
    if m.get("os"):
        bits.append(str(m["os"]) + (" " + str(m.get("os_version", ""))).rstrip())
    if m.get("arch"):
        bits.append(str(m["arch"]))
    if m.get("ram_gb") not in (None, "unknown"):
        bits.append("{0} GB of memory".format(m["ram_gb"]))
    if m.get("era_class"):
        bits.append("roughly a {0} machine".format(str(m["era_class"]).replace("-class", "")))
    return "a " + ", ".join(bits) if bits else "your machine"


def opener(seed):
    return pick(["Sure thing.", "Good question.", "Happy to.", "Of course."], seed)


def answer(state, question):
    """Route a question to an intent. Returns (text, action) where action is an
    optional callable the caller may offer to run with confirmation."""
    q = question.strip().lower()
    if not q:
        return ("Go on - I'm listening.", None)

    has = lambda *words: any(w in q for w in words)

    if has("who are you", "your name", "what are you"):
        return ("I'm Patch - the AI buddy that came with your Signature upgrade. "
                "I live right here on your machine, I know what the upgrade did, "
                "and I answer questions about your PC in plain words. No account, "
                "no cloud - just me and this computer.", None)

    if has("hello", "hi ", "hi!", "hey", "good morning", "good evening") and len(q) < 30:
        if state["installed"]:
            return ("Hey! Good to see you. Your Signature upgrade is in place - "
                    "ask me how your PC is doing, what got installed, or what to do next.", None)
        return ("Hey! I'm Patch. Once the Signature overlay is installed I'll know "
                "this machine inside out. For now, ask me what the upgrade does.", None)

    if has("how is my", "how's my", "pc doing", "health", "good form", "everything ok", "everything okay"):
        if not state["installed"]:
            return ("The overlay isn't installed yet, so there's nothing for me to check. "
                    "Run the installer first - then I'll keep an eye on things.", None)
        return ("Here's the honest picture: the overlay is installed ({0} components, {1}). ".format(
                    len(state["components"]),
                    ("since " + state["installed_at"]) if state["installed_at"] else "date unknown") +
                "The last full sweep {0}. ".format(
                    "ran and wrote FULL_SWEEP.txt" if state["full_sweep"] else "hasn't run yet - want me to run a health check?") +
                "Say 'check health' and I'll verify everything's in good form right now.", "health")

    if has("what did you install", "what was installed", "what did the upgrade do", "what's installed"):
        if not state["installed"]:
            return ("Nothing yet - the overlay isn't installed on this machine. "
                    "That's the toolkit's --install step.", None)
        names = {"apps": "app collection", "tools": "technician tools", "lenses": "lens views",
                 "pc_models": "PC model data", "software": "software set", "ai_offline": "offline AI",
                 "ai_online": "online AI", "sweep": "full sweep", "ai_sweeper": "AI Sweeper"}
        comps = [names.get(c, c) for c in state["components"]]
        return ("{0} I put in: {1}. All of it lives in one SignatureOS folder - "
                "your old system wasn't touched at all.".format(
                    opener(q), ", ".join(comps) if comps else "nothing recorded"), None)

    if has("sweep", "clean", "junk", "what did you find", "what did you fix"):
        if state["sweep_report"]:
            lines = [l for l in state["sweep_report"].splitlines() if l.strip()][:8]
            return ("The Sweeper's last report says:\n" + "\n".join(lines) +
                    "\n\nWant me to run it again? Say 'run the sweeper'.", "sweep")
        return ("The Sweeper hasn't run yet on this machine. Say 'run the sweeper' and "
                "I'll scan for junk and startup bloat - I'll only ever clean what's safe, "
                "and I'll ask before anything risky.", "sweep")

    if has("my system", "my pc", "specs", "specification", "memory", "ram ", "processor", "cpu"):
        return ("You're on " + machine_line(state) + ". " +
                ("That's from the check the installer ran - real numbers, not guesses." if state["machine"] else ""), None)

    if has("undo", "remove", "uninstall", "go back", "revert"):
        return ("Easy - the whole upgrade lives in one SignatureOS folder, and the installer "
                "wrote a restore manifest. Deleting that folder undoes everything; your old "
                "system was never modified. If you want me to do it, say 'yes, remove it' "
                "and I'll run the official --remove.", "remove")

    if has("yes, remove it"):
        return ("Last chance - this deletes the SignatureOS folder and all its upgrades. "
                "Type 'remove now' to confirm, or anything else to keep it.", "remove_now")

    if has("what now", "what should i do", "next step", "recommend"):
        recs = []
        if not state["installed"]:
            recs.append("install the overlay first - that's the whole point of me being here")
        else:
            if not state["sweep_report"]:
                recs.append("run the AI Sweeper once, so the junk gets cleared")
            recs.append("try the offline AI - it's yours, no internet needed")
            recs.append("ask me anything about this machine whenever something feels off")
        return ("{0} Here's what I'd do: {1}.".format(opener(q), "; ".join(recs) + "."), None)

    if has("run the sweeper", "sweep again", "clean my pc"):
        return ("I'll scan for junk, old caches, startup bloat and dead links - report first, "
                "and I'll only clean what's safe unless you say otherwise. Ready?", "sweep")

    if has("check health", "health check", "verify"):
        return ("I'll verify the install: manifests parse, every component's files are present, "
                "the helper scripts compile, and disk space is healthy. Run it?", "health")

    if has("offline ai", "ai buddy", "llama"):
        return ("The offline AI config is part of the overlay - model card and chat settings. "
                "Straight talk: the config ships, the model weights download separately from "
                "the Signature Llama site. And me? I'm the small talkative one - I run right "
                "here with no weights at all.", None)

    if has("thank"):
        return ("Anytime. That's what I'm here for - keeping this machine in good form.", None)

    if has("bye", "goodbye", "see you", "quit", "exit"):
        return ("See you - I'll be right here in the SignatureOS folder whenever you need me.", "bye")

    if has("what can you do", "help", "commands"):
        return ("I can: tell you how your PC is doing, explain what the upgrade installed, "
                "report what the Sweeper found, run the sweeper or a health check (I'll ask first), "
                "and explain how to undo the upgrade. Just ask in plain words.", None)

    return ("Hmm - I don't know that one, and I won't bluff. I'm a small on-machine helper: "
            "I know this PC's upgrade state, the sweeper, and the health check. "
            "Try 'how is my pc doing' or 'what can you do'.", None)


# ---------------------------------------------------------------------------
# Safe actions (always confirmed first by the caller)
# ---------------------------------------------------------------------------

def do_sweep(state, out):
    ov = overlay()
    root = state.get("root")
    if not ov or not root:
        out("I can't run the sweeper - the overlay toolkit isn't next to me.")
        return
    mod = ov.load_sweeper_module(root)
    if not mod:
        out("The sweeper module isn't available.")
        return
    out("Scanning for junk, old caches, startup bloat and dead links...")
    findings, startups, notes = mod.scan_all()
    out("Found {0} item(s). Startup programs listed: {1}.".format(len(findings), len(startups)))
    safe = [f for f in findings if f.get("auto_fix_safe")]
    out("{0} of them are safe to clean.".format(len(safe)))
    for f in findings[:10]:
        out("  - {0} ({1})".format(f.get("title"), "safe" if f.get("auto_fix_safe") else "ask-first"))
    if not findings:
        out("Nothing to clean - tidy machine.")


def do_health(state, out):
    ov = overlay()
    root = state.get("root")
    if not ov or not root:
        out("I can't run the health check - no install found.")
        return
    fails, warns, passes = ov.cmd_health_check(os.path.dirname(root), out=out)
    if fails:
        out("Not all green - {0} check(s) failed. See above for what to do.".format(fails))
    else:
        out("Your PC is in good form - {0} checks passed{1}.".format(
            passes, ", {0} warning(s)".format(warns) if warns else ""))


def do_remove(state, out):
    ov = overlay()
    root = state.get("root")
    if not ov or not root:
        out("Nothing to remove - no install found.")
        return
    ov.cmd_remove(os.path.dirname(root), out=out)
    out("Done - the SignatureOS folder is gone and your old system is exactly as it was.")


def confirm(prompt):
    try:
        ans = input(prompt + " [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans in ("y", "yes")


ACTIONS = {"sweep": do_sweep, "health": do_health, "remove": do_remove}


def chat_loop(ask_one=None):
    state = load_state()
    out = print
    if state["installed"]:
        out("Patch here - I can see your Signature upgrade ({0} components). What's on your mind?".format(
            len(state["components"])))
    else:
        out("Patch here - no overlay installed yet, but I can still answer questions. What's up?")
    out("(Type 'bye' to leave. I only ever act when you say so.)")
    while True:
        try:
            q = ask_one if ask_one is not None else input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            out("\nPatch: See you - I'll be right here whenever you need me.")
            break
        if not q:
            if ask_one is not None:
                break
            continue
        text, action = answer(state, q)
        out("\nPatch: " + text)
        if action == "bye":
            break
        if action == "remove_now":
            if confirm("Type-confirm: delete the SignatureOS folder?"):
                do_remove(state, out)
                state = load_state()
            else:
                out("Patch: Keeping everything. Wise - it's a good setup.")
        elif action in ACTIONS:
            what = {"sweep": "run the sweeper scan", "health": "run the health check",
                    "remove": "remove the whole upgrade"}[action]
            if action == "remove":
                out("Patch: Say 'yes, remove it' and I'll ask one final confirmation.")
            elif confirm("Patch: {0}?".format(what.capitalize())):
                ACTIONS[action](state, out)
                state = load_state()
            else:
                out("Patch: No problem - nothing changed.")
        if ask_one is not None:
            break


# ---------------------------------------------------------------------------
# Scripted Q&A self-test
# ---------------------------------------------------------------------------

SCRIPT = [
    ("who are you", ["Patch", "on your machine"]),
    ("how is my pc doing", ["overlay is installed", "components"]),
    ("what did you install", ["app collection", "SignatureOS folder"]),
    ("what did the sweeper find", ["Sweeper", "report"]),
    ("what's my system", ["Linux"]),
    ("what should i do next", ["offline AI"]),
    ("how do i undo this", ["SignatureOS folder", "never modified"]),
    ("what can you do", ["health check", "sweeper"]),
    ("tell me about quantum banana regulations", ["won't bluff", "don't know"]),
]


def run_test_qa():
    """Build a temp install, then run the scripted Q&A against it."""
    import tempfile
    import shutil
    ov = overlay()
    if not ov:
        print("TEST-FAIL: overlay toolkit not found next to ai_buddy.py")
        return 1
    tmp = tempfile.mkdtemp(prefix="buddyqa-")
    try:
        # install overlay into tmp
        rc = ov.main(["--install", "--target", tmp, "--components",
                      "apps,tools,lenses,pc_models,software,ai_sweeper,sweep"])
        if rc != 0:
            print("TEST-FAIL: install returned {0}".format(rc))
            return 1
        # fake a sweeper report so the buddy has findings to talk about
        root = ov.find_root(tmp)
        with open(os.path.join(root, "ai_sweep_report.txt"), "w", encoding="utf-8") as fh:
            fh.write("SIGNATURE AI SWEEPER - sweep report\n[fixed] Old temp file: junk.tmp\n[kept]  Broken link: dead.lnk\n")
        # point HOME at tmp so find_install() sees it
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = tmp
        try:
            state = load_state()
            if not state["installed"]:
                print("TEST-FAIL: buddy did not see the temp install")
                return 1
            fails = 0
            for q, must in SCRIPT:
                text, _action = answer(state, q)
                missing = [m for m in must if m.lower() not in text.lower()]
                status = "PASS" if not missing else "FAIL"
                if missing:
                    fails += 1
                print("[{0}] Q: {1}".format(status, q))
                if missing:
                    print("       missing: {0}".format(", ".join(missing)))
                    print("       got: {0}".format(text[:220]))
            # determinism: same question twice -> same answer
            a1, _ = answer(state, "who are you")
            a2, _ = answer(state, "who are you")
            if a1 != a2:
                print("[FAIL] answers not deterministic")
                fails += 1
            else:
                print("[PASS] deterministic answers")
            # no sweeper report yet -> the buddy should recommend running it
            state2 = dict(state)
            state2["sweep_report"] = None
            t3, _ = answer(state2, "what should i do next")
            if "sweeper" in t3.lower():
                print("[PASS] recommends the sweeper when none has run")
            else:
                print("[FAIL] should recommend the sweeper when none has run")
                fails += 1
            print("TEST-QA: {0}".format("ALL PASS" if not fails else "{0} FAILURES".format(fails)))
            return 0 if not fails else 1
        finally:
            if old_home is None:
                del os.environ["HOME"]
            else:
                os.environ["HOME"] = old_home
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--test-qa" in args:
        return run_test_qa()
    if "--ask" in args:
        i = args.index("--ask")
        q = args[i + 1] if i + 1 < len(args) else ""
        text, _action = answer(load_state(), q)
        print("Patch: " + text)
        return 0
    if "--version" in args:
        print("Patch (Signature AI buddy) {0}".format(VERSION))
        return 0
    ask_one = None
    if args and not args[0].startswith("-"):
        ask_one = " ".join(args)
    chat_loop(ask_one=ask_one)
    return 0


if __name__ == "__main__":
    sys.exit(main())

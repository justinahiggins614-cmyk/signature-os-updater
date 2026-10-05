#!/usr/bin/env python3
"""Clean-remove cycle test: install -> verify restore manifest -> remove ->
assert zero residue. Manon's standing principle: if there's an issue, it must
cleanly remove. Exit 0 only if everything passes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "tools", "signature_os_overlay.py")


def tree(root):
    out = set()
    for dp, dns, fns in os.walk(root):
        for n in dns + fns:
            out.add(os.path.relpath(os.path.join(dp, n), root))
    return out


def run(*args):
    p = subprocess.run([sys.executable, TOOL] + list(args),
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def main():
    tmp = tempfile.mkdtemp(prefix="removecycle-")
    fails = []

    def check(name, cond, detail=""):
        print("[{0}] {1}{2}".format("PASS" if cond else "FAIL", name,
                                    " - " + detail if detail and not cond else ""))
        if not cond:
            fails.append(name)

    try:
        # seed the target with a pre-existing user file (must survive)
        with open(os.path.join(tmp, "my_document.txt"), "w") as fh:
            fh.write("precious user data")
        before = tree(tmp)

        rc, out, err = run("--install", "--target", tmp, "--components", "all")
        check("install exits 0", rc == 0, err[-300:] if rc else "")

        root = os.path.join(tmp, "SignatureOS")
        check("SignatureOS folder created", os.path.isdir(root))

        # restore manifest verified: every payload file on disk is listed
        restore = json.load(open(os.path.join(root, "RESTORE.json")))
        listed = set(restore.get("created", []))
        on_disk = set()
        for dp, _dns, fns in os.walk(root):
            for n in fns:
                on_disk.add(os.path.relpath(os.path.join(dp, n), root))
        # manifests record themselves apart from the payload list
        payload = on_disk - {"RESTORE.json"}
        missing = payload - listed
        check("restore manifest covers every created file", not missing,
              "unlisted: {0}".format(sorted(missing)))

        # nothing was created outside SignatureOS/
        after_install = tree(tmp)
        outside = set(p for p in (after_install - before)
                      if not p.startswith("SignatureOS"))
        check("nothing written outside SignatureOS/", not outside,
              "outside: {0}".format(sorted(outside)))

        # the user's own file is untouched
        check("user file untouched",
              open(os.path.join(tmp, "my_document.txt")).read() == "precious user data")

        rc, out, err = run("--remove", "--target", tmp)
        check("remove exits 0", rc == 0, err[-300:] if rc else "")
        check("SignatureOS folder gone", not os.path.exists(root))

        after = tree(tmp)
        check("zero residue: target identical to before install", after == before,
              "diff: {0}".format(sorted(after ^ before)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("REMOVE-CYCLE: {0}".format("ALL PASS" if not fails else "FAILURES: " + ", ".join(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

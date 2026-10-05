#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signature AI Sweeper - uses AI-guided plain-language rules to find and fix
common, safely-fixable PC issues.

Part of the Signature OS Overlay toolkit. Pure stdlib, Python 3.6+.
No network access. No admin needed. Never touches anything outside
well-known temp/cache folders without asking first.

What it scans for (Windows, macOS, Linux - OS-aware paths):
  * junk / temp files older than 48 hours        -> safe to auto-fix
  * bloated caches (old cached files)            -> safe to auto-fix
  * startup bloat (what launches at startup)     -> listed only, never touched
  * broken shortcuts / dead links                -> asks before touching
  * disk-space hogs (largest top-level folders)  -> listed only, never touched

Usage:
  python3 ai_sweeper.py                 scan and print a report (fix nothing)
  python3 ai_sweeper.py --fix           fix the safe items, ask about risky ones
  python3 ai_sweeper.py --fix --yes     fix safe items, skip prompts
                                        (risky items are left alone and reported)
  python3 ai_sweeper.py --fix --quarantine DIR
                                        move safe items to DIR instead of deleting
  python3 ai_sweeper.py --report PATH   write the sweep report here
  python3 ai_sweeper.py --root DIR      advanced/test hook: scan DIR as "home"

Exit code: 0 on success, 1 on error.
"""

from __future__ import print_function

import argparse
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import time

VERSION = "1.0.0"
SAFE_AGE_HOURS = 48          # only files older than this are auto-fixed
MAX_WALK_FILES = 20000       # safety cap per scanned tree
HOG_MIN_BYTES = 100 * 1024 * 1024  # only report folders over 100 MB
HOG_TOP_N = 8


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def system_name():
    return platform.system()


def home_dir():
    return os.path.expanduser("~")


def is_interactive():
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def fmt_size(n):
    """Human-readable size, 3.6-safe."""
    try:
        n = float(n)
    except Exception:
        return "unknown size"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return "{0:.1f} {1}".format(n, unit)
        n /= 1024.0
    return "{0:.1f} PB".format(n)


def age_hours(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 3600.0
    except Exception:
        return 0.0


def ask_yes_no(prompt):
    """Ask a yes/no question on an interactive terminal. Default is NO."""
    try:
        answer = input(prompt + " [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


# ---------------------------------------------------------------------------
# OS-aware scan locations
# ---------------------------------------------------------------------------

def scan_roots(home=None):
    """Return (temp_dirs, cache_dirs) for this OS."""
    home = home or home_dir()
    sysname = system_name()
    temp_dirs = [tempfile.gettempdir()]
    cache_dirs = []
    if sysname == "Windows":
        local = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        temp_dirs.append(os.path.join(local, "Temp"))
        temp_dirs.append(os.environ.get("TEMP", ""))
        cache_dirs.append(os.path.join(local, "Microsoft", "Windows", "INetCache"))
    elif sysname == "Darwin":
        cache_dirs.append(os.path.join(home, "Library", "Caches"))
    else:  # Linux and others
        xdg = os.environ.get("XDG_CACHE_HOME") or os.path.join(home, ".cache")
        cache_dirs.append(xdg)
    # dedupe + keep only existing dirs
    out_temp, out_cache = [], []
    for d in temp_dirs:
        if d and os.path.isdir(d) and d not in out_temp:
            out_temp.append(d)
    for d in cache_dirs:
        if d and os.path.isdir(d) and d not in out_cache:
            out_cache.append(d)
    return out_temp, out_cache


def startup_entries(home=None):
    """Read-only list of what launches at startup. Never modifies anything.

    Returns a list of dicts: {"source": ..., "name": ..., "detail": ...}.
    On any error returns the entries found so far plus an error note entry.
    """
    home = home or home_dir()
    sysname = system_name()
    entries = []

    def note(source, name, detail=""):
        entries.append({"source": source, "name": name, "detail": detail})

    if sysname == "Windows":
        try:
            import winreg
            for hive, hivename in ((winreg.HKEY_CURRENT_USER, "HKCU"),
                                   (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
                for sub in (r"Software\Microsoft\Windows\CurrentVersion\Run",
                            r"Software\Microsoft\Windows\CurrentVersion\RunOnce"):
                    try:
                        key = winreg.OpenKey(hive, sub)
                    except OSError:
                        continue
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                        except OSError:
                            break
                        note(hivename + "\\" + sub, name, str(value)[:200])
                        i += 1
                    winreg.CloseKey(key)
        except Exception as exc:
            note("windows-registry", "(could not read registry)", str(exc))
        for folder in (
                os.path.join(home, "AppData", "Roaming", "Microsoft", "Windows",
                             "Start Menu", "Programs", "Startup"),
                os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                             r"Microsoft\Windows\Start Menu\Programs\Startup")):
            if os.path.isdir(folder):
                try:
                    for item in sorted(os.listdir(folder)):
                        note("startup-folder", item, folder)
                except OSError as exc:
                    note("startup-folder", "(unreadable: {0})".format(folder), str(exc))
    elif sysname == "Darwin":
        for folder in (os.path.join(home, "Library", "LaunchAgents"),
                       "/Library/LaunchDaemons"):
            if os.path.isdir(folder):
                try:
                    for item in sorted(os.listdir(folder)):
                        if item.endswith(".plist"):
                            note("launchd", item, folder)
                except OSError as exc:
                    note("launchd", "(unreadable: {0})".format(folder), str(exc))
    else:  # Linux / other Unix
        folder = os.path.join(home, ".config", "autostart")
        if os.path.isdir(folder):
            try:
                for item in sorted(os.listdir(folder)):
                    if not item.endswith(".desktop"):
                        continue
                    name, exec_line = item, ""
                    try:
                        with open(os.path.join(folder, item), "r",
                                 encoding="utf-8", errors="replace") as fh:
                            for line in fh:
                                if line.startswith("Name="):
                                    name = line[5:].strip()
                                elif line.startswith("Exec="):
                                    exec_line = line[5:].strip()
                    except OSError:
                        pass
                    note("autostart", name, exec_line[:200])
            except OSError as exc:
                note("autostart", "(unreadable: {0})".format(folder), str(exc))
    return entries


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def make_finding(kind, path, size, safe, title, explanation):
    return {
        "kind": kind,
        "path": path,
        "size_bytes": int(size or 0),
        "auto_fix_safe": bool(safe),
        "title": title,
        "explanation": explanation,
    }


def iter_files_capped(root):
    """Yield file paths under root, capped for safety. Skips unreadable dirs."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None,
                                                followlinks=False):
        for name in filenames:
            if count >= MAX_WALK_FILES:
                return
            count += 1
            yield os.path.join(dirpath, name)


def scan_junk(temp_dirs, cache_dirs):
    """Old files in temp/cache dirs. Safe to auto-fix only if old enough."""
    findings = []
    for root in temp_dirs + cache_dirs:
        if not os.path.isdir(root):
            continue
        in_cache = root in cache_dirs
        for path in iter_files_capped(root):
            try:
                if os.path.islink(path) and not os.path.exists(path):
                    findings.append(make_finding(
                        "broken_link", path, 0, False,
                        "Broken link: {0}".format(os.path.basename(path)),
                        "This is a shortcut that points to something that no "
                        "longer exists. It does nothing, but removing it is "
                        "your call - the sweeper will ask first."))
                    continue
                if not os.path.isfile(path):
                    continue
                age = age_hours(path)
                if age < SAFE_AGE_HOURS:
                    continue
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                kind = "cache" if in_cache else "temp_file"
                title = ("Old cached file: {0}".format(os.path.basename(path))
                         if in_cache else
                         "Old temp file: {0}".format(os.path.basename(path)))
                expl = ("This file sits in a {0} folder and has not been "
                        "touched in {1:.0f} hours. Programs recreate these "
                        "folders on their own, so deleting old files here is "
                        "safe - nothing you installed or saved depends on "
                        "them.".format("cache" if in_cache else "temporary",
                                       age))
                findings.append(make_finding(kind, path, size, True, title, expl))
            except OSError:
                continue
    return findings


def scan_shortcuts(home=None):
    """Broken .lnk shortcuts on Windows: listed, never auto-touched."""
    findings = []
    if system_name() != "Windows":
        return findings
    home = home or home_dir()
    for folder in (os.path.join(home, "Desktop"),
                   os.path.join(home, "AppData", "Roaming", "Microsoft",
                                "Windows", "Start Menu", "Programs", "Startup")):
        if not os.path.isdir(folder):
            continue
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            if name.lower().endswith(".lnk"):
                findings.append(make_finding(
                    "shortcut", os.path.join(folder, name), 0, False,
                    "Windows shortcut: {0}".format(name),
                    "This is a shortcut file (.lnk). The sweeper only lists "
                    "shortcuts - it never deletes or changes them, because "
                    "only you know which ones you still want."))
    return findings


def dir_size_top_level(folder):
    """Return list of (path, bytes) for top-level children of folder."""
    results = []
    try:
        children = os.listdir(folder)
    except OSError:
        return results
    for name in children:
        path = os.path.join(folder, name)
        total = 0
        try:
            if os.path.islink(path):
                continue
            if os.path.isfile(path):
                total = os.path.getsize(path)
            elif os.path.isdir(path):
                for dirpath, _dirnames, filenames in os.walk(
                        path, onerror=lambda e: None, followlinks=False):
                    for fn in filenames:
                        try:
                            total += os.path.getsize(os.path.join(dirpath, fn))
                        except OSError:
                            pass
        except OSError:
            continue
        results.append((path, total))
    results.sort(key=lambda t: t[1], reverse=True)
    return results


def scan_hogs(home=None):
    """Largest top-level folders in the user's home dir. Listed only."""
    findings = []
    home = home or home_dir()
    for path, size in dir_size_top_level(home)[:HOG_TOP_N]:
        if size < HOG_MIN_BYTES:
            break
        findings.append(make_finding(
            "folder_hog", path, size, False,
            "Large folder: {0} ({1})".format(os.path.basename(path),
                                             fmt_size(size)),
            "This folder is using {0} of disk space. The sweeper never "
            "deletes folders - it just shows you the biggest ones so you can "
            "decide what to clean up yourself.".format(fmt_size(size))))
    return findings


def scan_all(home=None):
    """Run every scan. Returns (findings, startup_list, notes)."""
    home = home or home_dir()
    notes = []
    temp_dirs, cache_dirs = scan_roots(home)
    findings = []
    findings.extend(scan_junk(temp_dirs, cache_dirs))
    findings.extend(scan_shortcuts(home))
    findings.extend(scan_hogs(home))
    startups = startup_entries(home)
    notes.append("Scanned temp dirs: {0}".format(", ".join(temp_dirs) or "(none)"))
    notes.append("Scanned cache dirs: {0}".format(", ".join(cache_dirs) or "(none)"))
    return findings, startups, notes


# ---------------------------------------------------------------------------
# Fixing
# ---------------------------------------------------------------------------

def apply_fixes(findings, fix_safe=True, interactive=False, quarantine=None):
    """Apply fixes. Returns (fixed, left_alone) lists of finding dicts.

    fixed: findings that were removed/moved, each gains "action".
    left_alone: findings not touched, each gains "reason".
    Only auto_fix_safe findings are ever removed, and only when fix_safe.
    """
    fixed, left_alone = [], []

    if quarantine:
        try:
            if not os.path.isdir(quarantine):
                os.makedirs(quarantine)
        except OSError as exc:
            raise RuntimeError("Cannot create quarantine dir {0}: {1}".format(
                quarantine, exc))

    def record_fixed(f, action):
        f = dict(f)
        f["action"] = action
        fixed.append(f)

    def record_left(f, reason):
        f = dict(f)
        f["reason"] = reason
        left_alone.append(f)

    for f in findings:
        kind = f.get("kind")
        path = f.get("path", "")
        if f.get("auto_fix_safe") and fix_safe:
            if not os.path.exists(path) and not os.path.islink(path):
                record_left(f, "already gone")
                continue
            try:
                if quarantine:
                    dest = os.path.join(quarantine, os.path.basename(path))
                    base, ext = os.path.splitext(dest)
                    n = 1
                    while os.path.exists(dest):
                        dest = "{0}_{1}{2}".format(base, n, ext)
                        n += 1
                    shutil.move(path, dest)
                    record_fixed(f, "moved to quarantine: {0}".format(dest))
                else:
                    os.remove(path)
                    record_fixed(f, "deleted")
            except OSError as exc:
                record_left(f, "could not remove ({0}) - left alone".format(exc))
        elif kind == "broken_link" and fix_safe and interactive:
            if ask_yes_no("Remove the broken link?\n  {0}".format(path)):
                try:
                    os.remove(path)
                    record_fixed(f, "deleted (you approved)")
                except OSError as exc:
                    record_left(f, "could not remove ({0})".format(exc))
            else:
                record_left(f, "left alone - needs your approval")
        elif kind in ("broken_link", "shortcut", "folder_hog"):
            record_left(f, "left alone - needs your approval")
        else:
            record_left(f, "report only - the sweeper never touches this kind")
    return fixed, left_alone


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def build_report(findings, startups, fixed, left_alone, notes):
    lines = []
    lines.append("=" * 64)
    lines.append("SIGNATURE AI SWEEPER - sweep report")
    lines.append("Version {0} | {1} | {2}".format(
        VERSION, time.strftime("%Y-%m-%d %H:%M:%S"), system_name()))
    lines.append("=" * 64)
    lines.append("")
    lines.append("WHAT WAS FIXED ({0} items):".format(len(fixed)))
    if fixed:
        for f in fixed:
            lines.append("  [fixed] {0}".format(f["title"]))
            lines.append("          {0} | {1}".format(f["path"], f.get("action", "")))
    else:
        lines.append("  (nothing - run with --fix to clean the safe items)")
    lines.append("")
    lines.append("LEFT ALONE ({0} items):".format(len(left_alone)))
    if left_alone:
        for f in left_alone:
            lines.append("  [kept]  {0}".format(f["title"]))
            lines.append("          {0}".format(f["path"]))
            lines.append("          Why: {0}".format(f.get("reason", "")))
            lines.append("          What it is: {0}".format(f["explanation"]))
    else:
        lines.append("  (nothing left alone)")
    lines.append("")
    lines.append("STARTUP PROGRAMS ({0} found - listed only, never changed):".format(
        len(startups)))
    for s in startups:
        detail = " - {0}".format(s["detail"]) if s.get("detail") else ""
        lines.append("  * {0} [{1}]{2}".format(s["name"], s["source"], detail))
    lines.append("")
    lines.append("NOTES:")
    for n in notes:
        lines.append("  - {0}".format(n))
    try:
        total, used, free = shutil.disk_usage(home_dir())
        lines.append("  - Disk: {0} free of {1}".format(fmt_size(free), fmt_size(total)))
    except OSError:
        pass
    lines.append("")
    lines.append("Honest note: the sweeper only deletes old files inside temp")
    lines.append("and cache folders. It never touches your documents, photos,")
    lines.append("programs, or system files - and it always asks before")
    lines.append("anything it is not sure about.")
    lines.append("=" * 64)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Signature AI Sweeper - find and fix safe PC junk. "
                    "Report-only unless you pass --fix.")
    parser.add_argument("--fix", action="store_true",
                        help="Fix the safe items (old temp/cache files). "
                             "Asks before anything risky.")
    parser.add_argument("--yes", action="store_true",
                        help="Do not prompt. Risky items are left alone and "
                             "reported.")
    parser.add_argument("--quarantine", metavar="DIR", default=None,
                        help="Move safe items to DIR instead of deleting them.")
    parser.add_argument("--report", metavar="PATH", default="ai_sweep_report.txt",
                        help="Where to write the sweep report.")
    parser.add_argument("--root", metavar="DIR", default=None,
                        help="Advanced/test hook: scan DIR instead of your "
                             "home folder.")
    parser.add_argument("--startup-only", action="store_true",
                        help="Only list startup programs, skip file scans.")
    parser.add_argument("--json", action="store_true",
                        help="Print findings as JSON instead of the report.")
    parser.add_argument("--version", action="store_true",
                        help="Print the sweeper version and exit.")
    args = parser.parse_args(argv)

    if args.version:
        print("Signature AI Sweeper {0}".format(VERSION))
        return 0

    home = args.root or home_dir()
    interactive = is_interactive() and not args.yes

    if args.startup_only:
        startups = startup_entries(home)
        if args.json:
            print(json.dumps(startups, indent=2, sort_keys=True))
        else:
            print("Startup programs ({0} found - listed only, never changed):"
                  .format(len(startups)))
            for s in startups:
                detail = " - {0}".format(s["detail"]) if s.get("detail") else ""
                print("  * {0} [{1}]{2}".format(s["name"], s["source"], detail))
        return 0

    findings, startups, notes = scan_all(home)

    if args.json:
        print(json.dumps({"findings": findings, "startup": startups,
                          "notes": notes}, indent=2, sort_keys=True))
        return 0

    if args.fix:
        fixed, left_alone = apply_fixes(
            findings, fix_safe=True,
            interactive=interactive,
            quarantine=args.quarantine)
    else:
        fixed = []
        left_alone = []
        for f in findings:
            g = dict(f)
            g["reason"] = ("would be fixed with --fix" if f.get("auto_fix_safe")
                           else "left alone - needs your approval")
            left_alone.append(g)
        if findings and not args.fix:
            notes.append("Run with --fix to clean the {0} safe item(s)."
                         .format(sum(1 for f in findings if f.get("auto_fix_safe"))))

    report = build_report(findings, startups, fixed, left_alone, notes)
    print(report)
    try:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("Report written to: {0}".format(args.report))
    except OSError as exc:
        print("WARNING: could not write report to {0}: {1}".format(
            args.report, exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

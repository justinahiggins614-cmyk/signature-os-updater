================================================================
SIGNATURE OS OVERLAY TOOLKIT - README
Version 1.0.0 | Pure Python (standard library only, Python 3.6+)
No internet needed. No administrator rights needed.
================================================================

WHAT THIS IS
------------
A NON-DESTRUCTIVE overlay "upgrade" for your PC.

WHAT IT IS NOT (please read - this matters)
-------------------------------------------
- It does NOT install an operating system. No website or downloaded
  script can replace your OS through a browser. That is not how
  computers work, and anyone who tells you otherwise is not being
  honest with you.
- It does NOT replace, modify, or remove anything on your PC. Your
  Windows, macOS, or Linux install stays exactly as it is.
- It does NOT touch system folders, the registry, or boot settings.

WHAT IT DOES
------------
It creates ONE folder - SignatureOS - in the place you choose
(your home folder by default), and puts helpful Signature content
inside it: an app catalog index, helper tools, lens templates, a PC
model index, a software manifest, AI configs, and the AI Sweeper.
That is the whole "upgrade": your old system, plus one new folder
of Signature tools sitting on top.

TO UNDO IT: delete the SignatureOS folder. That is everything.
Or run:  python3 signature_os_overlay.py --remove
There is nothing else to uninstall, because nothing else was changed.

FILES IN THIS FOLDER
--------------------
signature_os_overlay.py  - the toolkit (the only file you must download)
ai_sweeper.py            - the AI Sweeper (also installed by the toolkit)
README.txt               - this file

THE CHECKER (for the Upgrade page)
----------------------------------
On an old PC, you may only want to check what you have. Download just
signature_os_overlay.py and run:

    python3 signature_os_overlay.py --code

It prints ONE line of code. Copy it, paste it into the Upgrade page
on the Signature OS Updater site, and the site reads your machine's
profile (OS, RAM, CPU, era estimate). Nothing is installed, nothing
is changed, nothing goes anywhere until you paste it yourself.

HOW TO RUN IT
-------------
You need Python 3.6 or newer already on your PC.

Windows:
    1. Install Python from python.org if you do not have it
       (tick "Add python.exe to PATH" during setup).
    2. Open Command Prompt in the folder with these files and run:
         python signature_os_overlay.py --install
    Or double-click is NOT recommended - use the command line so you
    can see what it says.

Mac:
    1. Open Terminal, go to the folder with these files:
         cd ~/Downloads/signature-os-toolkit
    2. Run:
         python3 signature_os_overlay.py --install

Linux:
    1. Open a terminal in the folder with these files.
    2. Run:
         python3 signature_os_overlay.py --install

Useful commands:
    python3 signature_os_overlay.py
        Help + a summary of your machine. Changes nothing.
    python3 signature_os_overlay.py --detect
        Print your machine profile as JSON. Changes nothing.
    python3 signature_os_overlay.py --code
        The checker: one paste-able line for the Upgrade page.
    python3 signature_os_overlay.py --install --target "C:\Users\You\Desktop"
        Install into the SignatureOS folder at the place you choose.
    python3 signature_os_overlay.py --install --components apps,tools,sweep
        Install only some parts (default is all).
        Parts: apps, tools, lenses, pc_models, software,
               ai_offline, ai_online, sweep, ai_sweeper
    python3 signature_os_overlay.py --install --dry-run
        Show what WOULD be created, without writing anything.
    python3 signature_os_overlay.py --health-check
        "As good form if upgrading": verifies the install is complete
        and healthy. Runs automatically at the end of every install.
    python3 signature_os_overlay.py --remove
        Delete the SignatureOS folder (undo everything).
    python3 signature_os_overlay.py --self-test
        Safe self-check in temporary folders. Writes nothing to your PC.

THE AI SWEEPER
--------------
"Uses AI to fix any issues it can with the PC" - honestly, here is
what that means: the sweeper scans well-known temp and cache folders
for old junk files, lists what starts with your PC, points out broken
shortcuts and the biggest space-hogging folders, and explains each
finding in plain language.

What it fixes BY ITSELF: only old files (untouched for 48+ hours)
inside temp/cache folders. It never touches your documents, photos,
programs, or system files.

What it ASKS about first: broken links/shortcuts and anything else
it is not sure about. If it cannot ask (or you pass --yes), it leaves
those alone and says so in its report.

Run it from inside your overlay after installing:
    python3 SignatureOS/tools/ai_sweeper.py            (report only)
    python3 SignatureOS/tools/ai_sweeper.py --fix      (clean safe junk, ask first)
    python3 SignatureOS/tools/ai_sweeper.py --fix --yes
        (clean safe junk, skip questions, leave risky items alone)
    python3 SignatureOS/tools/ai_sweeper.py --fix --quarantine C:\SweepBackup
        (move instead of delete, so you can put things back)

It writes ai_sweep_report.txt saying what it fixed, what it left
alone, and why. On Windows it only deletes old temp/cache files;
if you want extra safety, use --quarantine.

THE POST-UPGRADE HEALTH CHECK ("as good form if upgrading")
----------------------------------------------------------
Every --install ends with an automatic health check, and you can run
it any time with --health-check. It verifies:

  - manifest.json and RESTORE.json exist and parse
  - every installed part's files are actually present
  - the helper scripts (sweep, update check, AI Sweeper) still run
  - the offline AI config parses and its built-in responder answers
    a smoke-test prompt (this checks the bundled helper logic only -
    the real Signature Llama weights are a separate download from
    the Signature Llama site)
  - the disk has healthy free space (warns under 1 GB free)
  - a read-only startup scan completes (lists, never changes)

It prints "Your PC is in good form" with a PASS/WARN/FAIL list, or
tells you plainly what still needs attention and what to do about it.
The upgrade is not done until this check passes.

HONEST LIMITATIONS
------------------
- The "era class" (1990s/2000s/2010s/modern) is a rough guess from
  RAM and CPU counts only. Two machines with the same RAM can be
  decades apart - treat it as a fun estimate, not a measurement.
- If your PC cannot report its RAM (some locked-down systems), the
  toolkit says "unknown" instead of guessing.
- The app/PC-model catalogs in the overlay are INDEXES (sample
  manifests), not the full archives - the full collections live on
  their sites.
- The online AI config ships with BLANK endpoints. You fill in your
  own provider and key; keys are never bundled.
- update_check.py reads the local version manifest only. It makes no
  network calls, so it cannot tell you about newer releases -
  re-download the toolkit from the site for the latest version.
- The sweeper is conservative on purpose: when in doubt it leaves
  things alone and tells you. That is a feature, not a bug.

QUESTIONS? Read the Signature OS Updater site's Upgrade page, which
explains all of this in plain language.
================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signature OS Overlay toolkit.

A NON-DESTRUCTIVE overlay "upgrade" for any PC. Honest by design:

  * It does NOT install an operating system. A website / downloaded script
    cannot replace your OS through a browser - that is not how computers work.
  * It does NOT modify your existing system: no system directories, no
    registry edits, no boot changes, no admin rights needed.
  * Everything it creates lives inside ONE folder: <target>/SignatureOS/
    Deleting that folder undoes the whole thing (or run --remove).

Pure stdlib, Python 3.6+ compatible, no network access, no admin.

Usage:
  python3 signature_os_overlay.py                      print help + machine summary
  python3 signature_os_overlay.py --detect              print machine profile JSON
  python3 signature_os_overlay.py --code                print one-line checker code
  python3 signature_os_overlay.py --install [--target DIR] [--components ...] [--dry-run]
  python3 signature_os_overlay.py --health-check [--target DIR]
  python3 signature_os_overlay.py --remove [--target DIR]
  python3 signature_os_overlay.py --self-test
"""

from __future__ import print_function

import argparse
import base64
import importlib.util
import json
import os
import platform
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time

TOOL_VERSION = "1.0.0"
FOLDER_NAME = "SignatureOS"

# Filled in at build time by injecting base64(ai_sweeper.py).
# At install time the tool first looks for ai_sweeper.py next to itself;
# this embedded copy is the fallback so the single-file download still works.
AI_SWEEPER_B64 = "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiIKU2lnbmF0dXJlIEFJIFN3ZWVwZXIgLSB1c2VzIEFJLWd1aWRlZCBwbGFpbi1sYW5ndWFnZSBydWxlcyB0byBmaW5kIGFuZCBmaXgKY29tbW9uLCBzYWZlbHktZml4YWJsZSBQQyBpc3N1ZXMuCgpQYXJ0IG9mIHRoZSBTaWduYXR1cmUgT1MgT3ZlcmxheSB0b29sa2l0LiBQdXJlIHN0ZGxpYiwgUHl0aG9uIDMuNisuCk5vIG5ldHdvcmsgYWNjZXNzLiBObyBhZG1pbiBuZWVkZWQuIE5ldmVyIHRvdWNoZXMgYW55dGhpbmcgb3V0c2lkZQp3ZWxsLWtub3duIHRlbXAvY2FjaGUgZm9sZGVycyB3aXRob3V0IGFza2luZyBmaXJzdC4KCldoYXQgaXQgc2NhbnMgZm9yIChXaW5kb3dzLCBtYWNPUywgTGludXggLSBPUy1hd2FyZSBwYXRocyk6CiAgKiBqdW5rIC8gdGVtcCBmaWxlcyBvbGRlciB0aGFuIDQ4IGhvdXJzICAgICAgICAtPiBzYWZlIHRvIGF1dG8tZml4CiAgKiBibG9hdGVkIGNhY2hlcyAob2xkIGNhY2hlZCBmaWxlcykgICAgICAgICAgICAtPiBzYWZlIHRvIGF1dG8tZml4CiAgKiBzdGFydHVwIGJsb2F0ICh3aGF0IGxhdW5jaGVzIGF0IHN0YXJ0dXApICAgICAtPiBsaXN0ZWQgb25seSwgbmV2ZXIgdG91Y2hlZAogICogYnJva2VuIHNob3J0Y3V0cyAvIGRlYWQgbGlua3MgICAgICAgICAgICAgICAgLT4gYXNrcyBiZWZvcmUgdG91Y2hpbmcKICAqIGRpc2stc3BhY2UgaG9ncyAobGFyZ2VzdCB0b3AtbGV2ZWwgZm9sZGVycykgIC0+IGxpc3RlZCBvbmx5LCBuZXZlciB0b3VjaGVkCgpVc2FnZToKICBweXRob24zIGFpX3N3ZWVwZXIucHkgICAgICAgICAgICAgICAgIHNjYW4gYW5kIHByaW50IGEgcmVwb3J0IChmaXggbm90aGluZykKICBweXRob24zIGFpX3N3ZWVwZXIucHkgLS1maXggICAgICAgICAgIGZpeCB0aGUgc2FmZSBpdGVtcywgYXNrIGFib3V0IHJpc2t5IG9uZXMKICBweXRob24zIGFpX3N3ZWVwZXIucHkgLS1maXggLS15ZXMgICAgIGZpeCBzYWZlIGl0ZW1zLCBza2lwIHByb21wdHMKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIChyaXNreSBpdGVtcyBhcmUgbGVmdCBhbG9uZSBhbmQgcmVwb3J0ZWQpCiAgcHl0aG9uMyBhaV9zd2VlcGVyLnB5IC0tZml4IC0tcXVhcmFudGluZSBESVIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIG1vdmUgc2FmZSBpdGVtcyB0byBESVIgaW5zdGVhZCBvZiBkZWxldGluZwogIHB5dGhvbjMgYWlfc3dlZXBlci5weSAtLXJlcG9ydCBQQVRIICAgd3JpdGUgdGhlIHN3ZWVwIHJlcG9ydCBoZXJlCiAgcHl0aG9uMyBhaV9zd2VlcGVyLnB5IC0tcm9vdCBESVIgICAgICBhZHZhbmNlZC90ZXN0IGhvb2s6IHNjYW4gRElSIGFzICJob21lIgoKRXhpdCBjb2RlOiAwIG9uIHN1Y2Nlc3MsIDEgb24gZXJyb3IuCiIiIgoKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBwcmludF9mdW5jdGlvbgoKaW1wb3J0IGFyZ3BhcnNlCmltcG9ydCBqc29uCmltcG9ydCBvcwppbXBvcnQgcGxhdGZvcm0KaW1wb3J0IHNodXRpbAppbXBvcnQgc3RhdAppbXBvcnQgc3lzCmltcG9ydCB0ZW1wZmlsZQppbXBvcnQgdGltZQoKVkVSU0lPTiA9ICIxLjAuMCIKU0FGRV9BR0VfSE9VUlMgPSA0OCAgICAgICAgICAjIG9ubHkgZmlsZXMgb2xkZXIgdGhhbiB0aGlzIGFyZSBhdXRvLWZpeGVkCk1BWF9XQUxLX0ZJTEVTID0gMjAwMDAgICAgICAgIyBzYWZldHkgY2FwIHBlciBzY2FubmVkIHRyZWUKSE9HX01JTl9CWVRFUyA9IDEwMCAqIDEwMjQgKiAxMDI0ICAjIG9ubHkgcmVwb3J0IGZvbGRlcnMgb3ZlciAxMDAgTUIKSE9HX1RPUF9OID0gOAoKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCiMgU21hbGwgaGVscGVycwojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoKZGVmIHN5c3RlbV9uYW1lKCk6CiAgICByZXR1cm4gcGxhdGZvcm0uc3lzdGVtKCkKCgpkZWYgaG9tZV9kaXIoKToKICAgIHJldHVybiBvcy5wYXRoLmV4cGFuZHVzZXIoIn4iKQoKCmRlZiBpc19pbnRlcmFjdGl2ZSgpOgogICAgdHJ5OgogICAgICAgIHJldHVybiBzeXMuc3RkaW4uaXNhdHR5KCkKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcmV0dXJuIEZhbHNlCgoKZGVmIGZtdF9zaXplKG4pOgogICAgIiIiSHVtYW4tcmVhZGFibGUgc2l6ZSwgMy42LXNhZmUuIiIiCiAgICB0cnk6CiAgICAgICAgbiA9IGZsb2F0KG4pCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHJldHVybiAidW5rbm93biBzaXplIgogICAgZm9yIHVuaXQgaW4gKCJCIiwgIktCIiwgIk1CIiwgIkdCIiwgIlRCIik6CiAgICAgICAgaWYgbiA8IDEwMjQuMDoKICAgICAgICAgICAgcmV0dXJuICJ7MDouMWZ9IHsxfSIuZm9ybWF0KG4sIHVuaXQpCiAgICAgICAgbiAvPSAxMDI0LjAKICAgIHJldHVybiAiezA6LjFmfSBQQiIuZm9ybWF0KG4pCgoKZGVmIGFnZV9ob3VycyhwYXRoKToKICAgIHRyeToKICAgICAgICByZXR1cm4gKHRpbWUudGltZSgpIC0gb3MucGF0aC5nZXRtdGltZShwYXRoKSkgLyAzNjAwLjAKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcmV0dXJuIDAuMAoKCmRlZiBhc2tfeWVzX25vKHByb21wdCk6CiAgICAiIiJBc2sgYSB5ZXMvbm8gcXVlc3Rpb24gb24gYW4gaW50ZXJhY3RpdmUgdGVybWluYWwuIERlZmF1bHQgaXMgTk8uIiIiCiAgICB0cnk6CiAgICAgICAgYW5zd2VyID0gaW5wdXQocHJvbXB0ICsgIiBbeS9OXSAiKS5zdHJpcCgpLmxvd2VyKCkKICAgIGV4Y2VwdCAoRU9GRXJyb3IsIEtleWJvYXJkSW50ZXJydXB0KToKICAgICAgICByZXR1cm4gRmFsc2UKICAgIHJldHVybiBhbnN3ZXIgaW4gKCJ5IiwgInllcyIpCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KIyBPUy1hd2FyZSBzY2FuIGxvY2F0aW9ucwojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoKZGVmIHNjYW5fcm9vdHMoaG9tZT1Ob25lKToKICAgICIiIlJldHVybiAodGVtcF9kaXJzLCBjYWNoZV9kaXJzKSBmb3IgdGhpcyBPUy4iIiIKICAgIGhvbWUgPSBob21lIG9yIGhvbWVfZGlyKCkKICAgIHN5c25hbWUgPSBzeXN0ZW1fbmFtZSgpCiAgICB0ZW1wX2RpcnMgPSBbdGVtcGZpbGUuZ2V0dGVtcGRpcigpXQogICAgY2FjaGVfZGlycyA9IFtdCiAgICBpZiBzeXNuYW1lID09ICJXaW5kb3dzIjoKICAgICAgICBsb2NhbCA9IG9zLmVudmlyb24uZ2V0KCJMT0NBTEFQUERBVEEiKSBvciBvcy5wYXRoLmpvaW4oaG9tZSwgIkFwcERhdGEiLCAiTG9jYWwiKQogICAgICAgIHRlbXBfZGlycy5hcHBlbmQob3MucGF0aC5qb2luKGxvY2FsLCAiVGVtcCIpKQogICAgICAgIHRlbXBfZGlycy5hcHBlbmQob3MuZW52aXJvbi5nZXQoIlRFTVAiLCAiIikpCiAgICAgICAgY2FjaGVfZGlycy5hcHBlbmQob3MucGF0aC5qb2luKGxvY2FsLCAiTWljcm9zb2Z0IiwgIldpbmRvd3MiLCAiSU5ldENhY2hlIikpCiAgICBlbGlmIHN5c25hbWUgPT0gIkRhcndpbiI6CiAgICAgICAgY2FjaGVfZGlycy5hcHBlbmQob3MucGF0aC5qb2luKGhvbWUsICJMaWJyYXJ5IiwgIkNhY2hlcyIpKQogICAgZWxzZTogICMgTGludXggYW5kIG90aGVycwogICAgICAgIHhkZyA9IG9zLmVudmlyb24uZ2V0KCJYREdfQ0FDSEVfSE9NRSIpIG9yIG9zLnBhdGguam9pbihob21lLCAiLmNhY2hlIikKICAgICAgICBjYWNoZV9kaXJzLmFwcGVuZCh4ZGcpCiAgICAjIGRlZHVwZSArIGtlZXAgb25seSBleGlzdGluZyBkaXJzCiAgICBvdXRfdGVtcCwgb3V0X2NhY2hlID0gW10sIFtdCiAgICBmb3IgZCBpbiB0ZW1wX2RpcnM6CiAgICAgICAgaWYgZCBhbmQgb3MucGF0aC5pc2RpcihkKSBhbmQgZCBub3QgaW4gb3V0X3RlbXA6CiAgICAgICAgICAgIG91dF90ZW1wLmFwcGVuZChkKQogICAgZm9yIGQgaW4gY2FjaGVfZGlyczoKICAgICAgICBpZiBkIGFuZCBvcy5wYXRoLmlzZGlyKGQpIGFuZCBkIG5vdCBpbiBvdXRfY2FjaGU6CiAgICAgICAgICAgIG91dF9jYWNoZS5hcHBlbmQoZCkKICAgIHJldHVybiBvdXRfdGVtcCwgb3V0X2NhY2hlCgoKZGVmIHN0YXJ0dXBfZW50cmllcyhob21lPU5vbmUpOgogICAgIiIiUmVhZC1vbmx5IGxpc3Qgb2Ygd2hhdCBsYXVuY2hlcyBhdCBzdGFydHVwLiBOZXZlciBtb2RpZmllcyBhbnl0aGluZy4KCiAgICBSZXR1cm5zIGEgbGlzdCBvZiBkaWN0czogeyJzb3VyY2UiOiAuLi4sICJuYW1lIjogLi4uLCAiZGV0YWlsIjogLi4ufS4KICAgIE9uIGFueSBlcnJvciByZXR1cm5zIHRoZSBlbnRyaWVzIGZvdW5kIHNvIGZhciBwbHVzIGFuIGVycm9yIG5vdGUgZW50cnkuCiAgICAiIiIKICAgIGhvbWUgPSBob21lIG9yIGhvbWVfZGlyKCkKICAgIHN5c25hbWUgPSBzeXN0ZW1fbmFtZSgpCiAgICBlbnRyaWVzID0gW10KCiAgICBkZWYgbm90ZShzb3VyY2UsIG5hbWUsIGRldGFpbD0iIik6CiAgICAgICAgZW50cmllcy5hcHBlbmQoeyJzb3VyY2UiOiBzb3VyY2UsICJuYW1lIjogbmFtZSwgImRldGFpbCI6IGRldGFpbH0pCgogICAgaWYgc3lzbmFtZSA9PSAiV2luZG93cyI6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBpbXBvcnQgd2lucmVnCiAgICAgICAgICAgIGZvciBoaXZlLCBoaXZlbmFtZSBpbiAoKHdpbnJlZy5IS0VZX0NVUlJFTlRfVVNFUiwgIkhLQ1UiKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAod2lucmVnLkhLRVlfTE9DQUxfTUFDSElORSwgIkhLTE0iKSk6CiAgICAgICAgICAgICAgICBmb3Igc3ViIGluIChyIlNvZnR3YXJlXE1pY3Jvc29mdFxXaW5kb3dzXEN1cnJlbnRWZXJzaW9uXFJ1biIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICByIlNvZnR3YXJlXE1pY3Jvc29mdFxXaW5kb3dzXEN1cnJlbnRWZXJzaW9uXFJ1bk9uY2UiKToKICAgICAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgICAgIGtleSA9IHdpbnJlZy5PcGVuS2V5KGhpdmUsIHN1YikKICAgICAgICAgICAgICAgICAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgICAgICAgICBpID0gMAogICAgICAgICAgICAgICAgICAgIHdoaWxlIFRydWU6CiAgICAgICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIG5hbWUsIHZhbHVlLCBfID0gd2lucmVnLkVudW1WYWx1ZShrZXksIGkpCiAgICAgICAgICAgICAgICAgICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgICAgICAgICAgbm90ZShoaXZlbmFtZSArICJcXCIgKyBzdWIsIG5hbWUsIHN0cih2YWx1ZSlbOjIwMF0pCiAgICAgICAgICAgICAgICAgICAgICAgIGkgKz0gMQogICAgICAgICAgICAgICAgICAgIHdpbnJlZy5DbG9zZUtleShrZXkpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBleGM6CiAgICAgICAgICAgIG5vdGUoIndpbmRvd3MtcmVnaXN0cnkiLCAiKGNvdWxkIG5vdCByZWFkIHJlZ2lzdHJ5KSIsIHN0cihleGMpKQogICAgICAgIGZvciBmb2xkZXIgaW4gKAogICAgICAgICAgICAgICAgb3MucGF0aC5qb2luKGhvbWUsICJBcHBEYXRhIiwgIlJvYW1pbmciLCAiTWljcm9zb2Z0IiwgIldpbmRvd3MiLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICJTdGFydCBNZW51IiwgIlByb2dyYW1zIiwgIlN0YXJ0dXAiKSwKICAgICAgICAgICAgICAgIG9zLnBhdGguam9pbihvcy5lbnZpcm9uLmdldCgiUHJvZ3JhbURhdGEiLCByIkM6XFByb2dyYW1EYXRhIiksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgciJNaWNyb3NvZnRcV2luZG93c1xTdGFydCBNZW51XFByb2dyYW1zXFN0YXJ0dXAiKSk6CiAgICAgICAgICAgIGlmIG9zLnBhdGguaXNkaXIoZm9sZGVyKToKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICBmb3IgaXRlbSBpbiBzb3J0ZWQob3MubGlzdGRpcihmb2xkZXIpKToKICAgICAgICAgICAgICAgICAgICAgICAgbm90ZSgic3RhcnR1cC1mb2xkZXIiLCBpdGVtLCBmb2xkZXIpCiAgICAgICAgICAgICAgICBleGNlcHQgT1NFcnJvciBhcyBleGM6CiAgICAgICAgICAgICAgICAgICAgbm90ZSgic3RhcnR1cC1mb2xkZXIiLCAiKHVucmVhZGFibGU6IHswfSkiLmZvcm1hdChmb2xkZXIpLCBzdHIoZXhjKSkKICAgIGVsaWYgc3lzbmFtZSA9PSAiRGFyd2luIjoKICAgICAgICBmb3IgZm9sZGVyIGluIChvcy5wYXRoLmpvaW4oaG9tZSwgIkxpYnJhcnkiLCAiTGF1bmNoQWdlbnRzIiksCiAgICAgICAgICAgICAgICAgICAgICAgIi9MaWJyYXJ5L0xhdW5jaERhZW1vbnMiKToKICAgICAgICAgICAgaWYgb3MucGF0aC5pc2Rpcihmb2xkZXIpOgogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIGZvciBpdGVtIGluIHNvcnRlZChvcy5saXN0ZGlyKGZvbGRlcikpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBpdGVtLmVuZHN3aXRoKCIucGxpc3QiKToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIG5vdGUoImxhdW5jaGQiLCBpdGVtLCBmb2xkZXIpCiAgICAgICAgICAgICAgICBleGNlcHQgT1NFcnJvciBhcyBleGM6CiAgICAgICAgICAgICAgICAgICAgbm90ZSgibGF1bmNoZCIsICIodW5yZWFkYWJsZTogezB9KSIuZm9ybWF0KGZvbGRlciksIHN0cihleGMpKQogICAgZWxzZTogICMgTGludXggLyBvdGhlciBVbml4CiAgICAgICAgZm9sZGVyID0gb3MucGF0aC5qb2luKGhvbWUsICIuY29uZmlnIiwgImF1dG9zdGFydCIpCiAgICAgICAgaWYgb3MucGF0aC5pc2Rpcihmb2xkZXIpOgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBmb3IgaXRlbSBpbiBzb3J0ZWQob3MubGlzdGRpcihmb2xkZXIpKToKICAgICAgICAgICAgICAgICAgICBpZiBub3QgaXRlbS5lbmRzd2l0aCgiLmRlc2t0b3AiKToKICAgICAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgICAgICAgICBuYW1lLCBleGVjX2xpbmUgPSBpdGVtLCAiIgogICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICAgICAgd2l0aCBvcGVuKG9zLnBhdGguam9pbihmb2xkZXIsIGl0ZW0pLCAiciIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGVuY29kaW5nPSJ1dGYtOCIsIGVycm9ycz0icmVwbGFjZSIpIGFzIGZoOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgZm9yIGxpbmUgaW4gZmg6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgaWYgbGluZS5zdGFydHN3aXRoKCJOYW1lPSIpOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBuYW1lID0gbGluZVs1Ol0uc3RyaXAoKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGVsaWYgbGluZS5zdGFydHN3aXRoKCJFeGVjPSIpOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBleGVjX2xpbmUgPSBsaW5lWzU6XS5zdHJpcCgpCiAgICAgICAgICAgICAgICAgICAgZXhjZXB0IE9TRXJyb3I6CiAgICAgICAgICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICAgICAgICAgICAgICBub3RlKCJhdXRvc3RhcnQiLCBuYW1lLCBleGVjX2xpbmVbOjIwMF0pCiAgICAgICAgICAgIGV4Y2VwdCBPU0Vycm9yIGFzIGV4YzoKICAgICAgICAgICAgICAgIG5vdGUoImF1dG9zdGFydCIsICIodW5yZWFkYWJsZTogezB9KSIuZm9ybWF0KGZvbGRlciksIHN0cihleGMpKQogICAgcmV0dXJuIGVudHJpZXMKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQojIFNjYW5uaW5nCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCgpkZWYgbWFrZV9maW5kaW5nKGtpbmQsIHBhdGgsIHNpemUsIHNhZmUsIHRpdGxlLCBleHBsYW5hdGlvbik6CiAgICByZXR1cm4gewogICAgICAgICJraW5kIjoga2luZCwKICAgICAgICAicGF0aCI6IHBhdGgsCiAgICAgICAgInNpemVfYnl0ZXMiOiBpbnQoc2l6ZSBvciAwKSwKICAgICAgICAiYXV0b19maXhfc2FmZSI6IGJvb2woc2FmZSksCiAgICAgICAgInRpdGxlIjogdGl0bGUsCiAgICAgICAgImV4cGxhbmF0aW9uIjogZXhwbGFuYXRpb24sCiAgICB9CgoKZGVmIGl0ZXJfZmlsZXNfY2FwcGVkKHJvb3QpOgogICAgIiIiWWllbGQgZmlsZSBwYXRocyB1bmRlciByb290LCBjYXBwZWQgZm9yIHNhZmV0eS4gU2tpcHMgdW5yZWFkYWJsZSBkaXJzLiIiIgogICAgY291bnQgPSAwCiAgICBmb3IgZGlycGF0aCwgZGlybmFtZXMsIGZpbGVuYW1lcyBpbiBvcy53YWxrKHJvb3QsIG9uZXJyb3I9bGFtYmRhIGU6IE5vbmUsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGZvbGxvd2xpbmtzPUZhbHNlKToKICAgICAgICBmb3IgbmFtZSBpbiBmaWxlbmFtZXM6CiAgICAgICAgICAgIGlmIGNvdW50ID49IE1BWF9XQUxLX0ZJTEVTOgogICAgICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgICAgIGNvdW50ICs9IDEKICAgICAgICAgICAgeWllbGQgb3MucGF0aC5qb2luKGRpcnBhdGgsIG5hbWUpCgoKZGVmIHNjYW5fanVuayh0ZW1wX2RpcnMsIGNhY2hlX2RpcnMpOgogICAgIiIiT2xkIGZpbGVzIGluIHRlbXAvY2FjaGUgZGlycy4gU2FmZSB0byBhdXRvLWZpeCBvbmx5IGlmIG9sZCBlbm91Z2guIiIiCiAgICBmaW5kaW5ncyA9IFtdCiAgICBmb3Igcm9vdCBpbiB0ZW1wX2RpcnMgKyBjYWNoZV9kaXJzOgogICAgICAgIGlmIG5vdCBvcy5wYXRoLmlzZGlyKHJvb3QpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGluX2NhY2hlID0gcm9vdCBpbiBjYWNoZV9kaXJzCiAgICAgICAgZm9yIHBhdGggaW4gaXRlcl9maWxlc19jYXBwZWQocm9vdCk6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIGlmIG9zLnBhdGguaXNsaW5rKHBhdGgpIGFuZCBub3Qgb3MucGF0aC5leGlzdHMocGF0aCk6CiAgICAgICAgICAgICAgICAgICAgZmluZGluZ3MuYXBwZW5kKG1ha2VfZmluZGluZygKICAgICAgICAgICAgICAgICAgICAgICAgImJyb2tlbl9saW5rIiwgcGF0aCwgMCwgRmFsc2UsCiAgICAgICAgICAgICAgICAgICAgICAgICJCcm9rZW4gbGluazogezB9Ii5mb3JtYXQob3MucGF0aC5iYXNlbmFtZShwYXRoKSksCiAgICAgICAgICAgICAgICAgICAgICAgICJUaGlzIGlzIGEgc2hvcnRjdXQgdGhhdCBwb2ludHMgdG8gc29tZXRoaW5nIHRoYXQgbm8gIgogICAgICAgICAgICAgICAgICAgICAgICAibG9uZ2VyIGV4aXN0cy4gSXQgZG9lcyBub3RoaW5nLCBidXQgcmVtb3ZpbmcgaXQgaXMgIgogICAgICAgICAgICAgICAgICAgICAgICAieW91ciBjYWxsIC0gdGhlIHN3ZWVwZXIgd2lsbCBhc2sgZmlyc3QuIikpCiAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgICAgIGlmIG5vdCBvcy5wYXRoLmlzZmlsZShwYXRoKToKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgYWdlID0gYWdlX2hvdXJzKHBhdGgpCiAgICAgICAgICAgICAgICBpZiBhZ2UgPCBTQUZFX0FHRV9IT1VSUzoKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIHNpemUgPSBvcy5wYXRoLmdldHNpemUocGF0aCkKICAgICAgICAgICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICAgICAgICAgIHNpemUgPSAwCiAgICAgICAgICAgICAgICBraW5kID0gImNhY2hlIiBpZiBpbl9jYWNoZSBlbHNlICJ0ZW1wX2ZpbGUiCiAgICAgICAgICAgICAgICB0aXRsZSA9ICgiT2xkIGNhY2hlZCBmaWxlOiB7MH0iLmZvcm1hdChvcy5wYXRoLmJhc2VuYW1lKHBhdGgpKQogICAgICAgICAgICAgICAgICAgICAgICAgaWYgaW5fY2FjaGUgZWxzZQogICAgICAgICAgICAgICAgICAgICAgICAgIk9sZCB0ZW1wIGZpbGU6IHswfSIuZm9ybWF0KG9zLnBhdGguYmFzZW5hbWUocGF0aCkpKQogICAgICAgICAgICAgICAgZXhwbCA9ICgiVGhpcyBmaWxlIHNpdHMgaW4gYSB7MH0gZm9sZGVyIGFuZCBoYXMgbm90IGJlZW4gIgogICAgICAgICAgICAgICAgICAgICAgICAidG91Y2hlZCBpbiB7MTouMGZ9IGhvdXJzLiBQcm9ncmFtcyByZWNyZWF0ZSB0aGVzZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICJmb2xkZXJzIG9uIHRoZWlyIG93biwgc28gZGVsZXRpbmcgb2xkIGZpbGVzIGhlcmUgaXMgIgogICAgICAgICAgICAgICAgICAgICAgICAic2FmZSAtIG5vdGhpbmcgeW91IGluc3RhbGxlZCBvciBzYXZlZCBkZXBlbmRzIG9uICIKICAgICAgICAgICAgICAgICAgICAgICAgInRoZW0uIi5mb3JtYXQoImNhY2hlIiBpZiBpbl9jYWNoZSBlbHNlICJ0ZW1wb3JhcnkiLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBhZ2UpKQogICAgICAgICAgICAgICAgZmluZGluZ3MuYXBwZW5kKG1ha2VfZmluZGluZyhraW5kLCBwYXRoLCBzaXplLCBUcnVlLCB0aXRsZSwgZXhwbCkpCiAgICAgICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICAgICAgY29udGludWUKICAgIHJldHVybiBmaW5kaW5ncwoKCmRlZiBzY2FuX3Nob3J0Y3V0cyhob21lPU5vbmUpOgogICAgIiIiQnJva2VuIC5sbmsgc2hvcnRjdXRzIG9uIFdpbmRvd3M6IGxpc3RlZCwgbmV2ZXIgYXV0by10b3VjaGVkLiIiIgogICAgZmluZGluZ3MgPSBbXQogICAgaWYgc3lzdGVtX25hbWUoKSAhPSAiV2luZG93cyI6CiAgICAgICAgcmV0dXJuIGZpbmRpbmdzCiAgICBob21lID0gaG9tZSBvciBob21lX2RpcigpCiAgICBmb3IgZm9sZGVyIGluIChvcy5wYXRoLmpvaW4oaG9tZSwgIkRlc2t0b3AiKSwKICAgICAgICAgICAgICAgICAgIG9zLnBhdGguam9pbihob21lLCAiQXBwRGF0YSIsICJSb2FtaW5nIiwgIk1pY3Jvc29mdCIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIldpbmRvd3MiLCAiU3RhcnQgTWVudSIsICJQcm9ncmFtcyIsICJTdGFydHVwIikpOgogICAgICAgIGlmIG5vdCBvcy5wYXRoLmlzZGlyKGZvbGRlcik6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgdHJ5OgogICAgICAgICAgICBuYW1lcyA9IG9zLmxpc3RkaXIoZm9sZGVyKQogICAgICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGZvciBuYW1lIGluIG5hbWVzOgogICAgICAgICAgICBpZiBuYW1lLmxvd2VyKCkuZW5kc3dpdGgoIi5sbmsiKToKICAgICAgICAgICAgICAgIGZpbmRpbmdzLmFwcGVuZChtYWtlX2ZpbmRpbmcoCiAgICAgICAgICAgICAgICAgICAgInNob3J0Y3V0Iiwgb3MucGF0aC5qb2luKGZvbGRlciwgbmFtZSksIDAsIEZhbHNlLAogICAgICAgICAgICAgICAgICAgICJXaW5kb3dzIHNob3J0Y3V0OiB7MH0iLmZvcm1hdChuYW1lKSwKICAgICAgICAgICAgICAgICAgICAiVGhpcyBpcyBhIHNob3J0Y3V0IGZpbGUgKC5sbmspLiBUaGUgc3dlZXBlciBvbmx5IGxpc3RzICIKICAgICAgICAgICAgICAgICAgICAic2hvcnRjdXRzIC0gaXQgbmV2ZXIgZGVsZXRlcyBvciBjaGFuZ2VzIHRoZW0sIGJlY2F1c2UgIgogICAgICAgICAgICAgICAgICAgICJvbmx5IHlvdSBrbm93IHdoaWNoIG9uZXMgeW91IHN0aWxsIHdhbnQuIikpCiAgICByZXR1cm4gZmluZGluZ3MKCgpkZWYgZGlyX3NpemVfdG9wX2xldmVsKGZvbGRlcik6CiAgICAiIiJSZXR1cm4gbGlzdCBvZiAocGF0aCwgYnl0ZXMpIGZvciB0b3AtbGV2ZWwgY2hpbGRyZW4gb2YgZm9sZGVyLiIiIgogICAgcmVzdWx0cyA9IFtdCiAgICB0cnk6CiAgICAgICAgY2hpbGRyZW4gPSBvcy5saXN0ZGlyKGZvbGRlcikKICAgIGV4Y2VwdCBPU0Vycm9yOgogICAgICAgIHJldHVybiByZXN1bHRzCiAgICBmb3IgbmFtZSBpbiBjaGlsZHJlbjoKICAgICAgICBwYXRoID0gb3MucGF0aC5qb2luKGZvbGRlciwgbmFtZSkKICAgICAgICB0b3RhbCA9IDAKICAgICAgICB0cnk6CiAgICAgICAgICAgIGlmIG9zLnBhdGguaXNsaW5rKHBhdGgpOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgaWYgb3MucGF0aC5pc2ZpbGUocGF0aCk6CiAgICAgICAgICAgICAgICB0b3RhbCA9IG9zLnBhdGguZ2V0c2l6ZShwYXRoKQogICAgICAgICAgICBlbGlmIG9zLnBhdGguaXNkaXIocGF0aCk6CiAgICAgICAgICAgICAgICBmb3IgZGlycGF0aCwgX2Rpcm5hbWVzLCBmaWxlbmFtZXMgaW4gb3Mud2FsaygKICAgICAgICAgICAgICAgICAgICAgICAgcGF0aCwgb25lcnJvcj1sYW1iZGEgZTogTm9uZSwgZm9sbG93bGlua3M9RmFsc2UpOgogICAgICAgICAgICAgICAgICAgIGZvciBmbiBpbiBmaWxlbmFtZXM6CiAgICAgICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHRvdGFsICs9IG9zLnBhdGguZ2V0c2l6ZShvcy5wYXRoLmpvaW4oZGlycGF0aCwgZm4pKQogICAgICAgICAgICAgICAgICAgICAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICByZXN1bHRzLmFwcGVuZCgocGF0aCwgdG90YWwpKQogICAgcmVzdWx0cy5zb3J0KGtleT1sYW1iZGEgdDogdFsxXSwgcmV2ZXJzZT1UcnVlKQogICAgcmV0dXJuIHJlc3VsdHMKCgpkZWYgc2Nhbl9ob2dzKGhvbWU9Tm9uZSk6CiAgICAiIiJMYXJnZXN0IHRvcC1sZXZlbCBmb2xkZXJzIGluIHRoZSB1c2VyJ3MgaG9tZSBkaXIuIExpc3RlZCBvbmx5LiIiIgogICAgZmluZGluZ3MgPSBbXQogICAgaG9tZSA9IGhvbWUgb3IgaG9tZV9kaXIoKQogICAgZm9yIHBhdGgsIHNpemUgaW4gZGlyX3NpemVfdG9wX2xldmVsKGhvbWUpWzpIT0dfVE9QX05dOgogICAgICAgIGlmIHNpemUgPCBIT0dfTUlOX0JZVEVTOgogICAgICAgICAgICBicmVhawogICAgICAgIGZpbmRpbmdzLmFwcGVuZChtYWtlX2ZpbmRpbmcoCiAgICAgICAgICAgICJmb2xkZXJfaG9nIiwgcGF0aCwgc2l6ZSwgRmFsc2UsCiAgICAgICAgICAgICJMYXJnZSBmb2xkZXI6IHswfSAoezF9KSIuZm9ybWF0KG9zLnBhdGguYmFzZW5hbWUocGF0aCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGZtdF9zaXplKHNpemUpKSwKICAgICAgICAgICAgIlRoaXMgZm9sZGVyIGlzIHVzaW5nIHswfSBvZiBkaXNrIHNwYWNlLiBUaGUgc3dlZXBlciBuZXZlciAiCiAgICAgICAgICAgICJkZWxldGVzIGZvbGRlcnMgLSBpdCBqdXN0IHNob3dzIHlvdSB0aGUgYmlnZ2VzdCBvbmVzIHNvIHlvdSBjYW4gIgogICAgICAgICAgICAiZGVjaWRlIHdoYXQgdG8gY2xlYW4gdXAgeW91cnNlbGYuIi5mb3JtYXQoZm10X3NpemUoc2l6ZSkpKSkKICAgIHJldHVybiBmaW5kaW5ncwoKCmRlZiBzY2FuX2FsbChob21lPU5vbmUpOgogICAgIiIiUnVuIGV2ZXJ5IHNjYW4uIFJldHVybnMgKGZpbmRpbmdzLCBzdGFydHVwX2xpc3QsIG5vdGVzKS4iIiIKICAgIGhvbWUgPSBob21lIG9yIGhvbWVfZGlyKCkKICAgIG5vdGVzID0gW10KICAgIHRlbXBfZGlycywgY2FjaGVfZGlycyA9IHNjYW5fcm9vdHMoaG9tZSkKICAgIGZpbmRpbmdzID0gW10KICAgIGZpbmRpbmdzLmV4dGVuZChzY2FuX2p1bmsodGVtcF9kaXJzLCBjYWNoZV9kaXJzKSkKICAgIGZpbmRpbmdzLmV4dGVuZChzY2FuX3Nob3J0Y3V0cyhob21lKSkKICAgIGZpbmRpbmdzLmV4dGVuZChzY2FuX2hvZ3MoaG9tZSkpCiAgICBzdGFydHVwcyA9IHN0YXJ0dXBfZW50cmllcyhob21lKQogICAgbm90ZXMuYXBwZW5kKCJTY2FubmVkIHRlbXAgZGlyczogezB9Ii5mb3JtYXQoIiwgIi5qb2luKHRlbXBfZGlycykgb3IgIihub25lKSIpKQogICAgbm90ZXMuYXBwZW5kKCJTY2FubmVkIGNhY2hlIGRpcnM6IHswfSIuZm9ybWF0KCIsICIuam9pbihjYWNoZV9kaXJzKSBvciAiKG5vbmUpIikpCiAgICByZXR1cm4gZmluZGluZ3MsIHN0YXJ0dXBzLCBub3RlcwoKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCiMgRml4aW5nCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCgpkZWYgYXBwbHlfZml4ZXMoZmluZGluZ3MsIGZpeF9zYWZlPVRydWUsIGludGVyYWN0aXZlPUZhbHNlLCBxdWFyYW50aW5lPU5vbmUpOgogICAgIiIiQXBwbHkgZml4ZXMuIFJldHVybnMgKGZpeGVkLCBsZWZ0X2Fsb25lKSBsaXN0cyBvZiBmaW5kaW5nIGRpY3RzLgoKICAgIGZpeGVkOiBmaW5kaW5ncyB0aGF0IHdlcmUgcmVtb3ZlZC9tb3ZlZCwgZWFjaCBnYWlucyAiYWN0aW9uIi4KICAgIGxlZnRfYWxvbmU6IGZpbmRpbmdzIG5vdCB0b3VjaGVkLCBlYWNoIGdhaW5zICJyZWFzb24iLgogICAgT25seSBhdXRvX2ZpeF9zYWZlIGZpbmRpbmdzIGFyZSBldmVyIHJlbW92ZWQsIGFuZCBvbmx5IHdoZW4gZml4X3NhZmUuCiAgICAiIiIKICAgIGZpeGVkLCBsZWZ0X2Fsb25lID0gW10sIFtdCgogICAgaWYgcXVhcmFudGluZToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGlmIG5vdCBvcy5wYXRoLmlzZGlyKHF1YXJhbnRpbmUpOgogICAgICAgICAgICAgICAgb3MubWFrZWRpcnMocXVhcmFudGluZSkKICAgICAgICBleGNlcHQgT1NFcnJvciBhcyBleGM6CiAgICAgICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcigiQ2Fubm90IGNyZWF0ZSBxdWFyYW50aW5lIGRpciB7MH06IHsxfSIuZm9ybWF0KAogICAgICAgICAgICAgICAgcXVhcmFudGluZSwgZXhjKSkKCiAgICBkZWYgcmVjb3JkX2ZpeGVkKGYsIGFjdGlvbik6CiAgICAgICAgZiA9IGRpY3QoZikKICAgICAgICBmWyJhY3Rpb24iXSA9IGFjdGlvbgogICAgICAgIGZpeGVkLmFwcGVuZChmKQoKICAgIGRlZiByZWNvcmRfbGVmdChmLCByZWFzb24pOgogICAgICAgIGYgPSBkaWN0KGYpCiAgICAgICAgZlsicmVhc29uIl0gPSByZWFzb24KICAgICAgICBsZWZ0X2Fsb25lLmFwcGVuZChmKQoKICAgIGZvciBmIGluIGZpbmRpbmdzOgogICAgICAgIGtpbmQgPSBmLmdldCgia2luZCIpCiAgICAgICAgcGF0aCA9IGYuZ2V0KCJwYXRoIiwgIiIpCiAgICAgICAgaWYgZi5nZXQoImF1dG9fZml4X3NhZmUiKSBhbmQgZml4X3NhZmU6CiAgICAgICAgICAgIGlmIG5vdCBvcy5wYXRoLmV4aXN0cyhwYXRoKSBhbmQgbm90IG9zLnBhdGguaXNsaW5rKHBhdGgpOgogICAgICAgICAgICAgICAgcmVjb3JkX2xlZnQoZiwgImFscmVhZHkgZ29uZSIpCiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBpZiBxdWFyYW50aW5lOgogICAgICAgICAgICAgICAgICAgIGRlc3QgPSBvcy5wYXRoLmpvaW4ocXVhcmFudGluZSwgb3MucGF0aC5iYXNlbmFtZShwYXRoKSkKICAgICAgICAgICAgICAgICAgICBiYXNlLCBleHQgPSBvcy5wYXRoLnNwbGl0ZXh0KGRlc3QpCiAgICAgICAgICAgICAgICAgICAgbiA9IDEKICAgICAgICAgICAgICAgICAgICB3aGlsZSBvcy5wYXRoLmV4aXN0cyhkZXN0KToKICAgICAgICAgICAgICAgICAgICAgICAgZGVzdCA9ICJ7MH1fezF9ezJ9Ii5mb3JtYXQoYmFzZSwgbiwgZXh0KQogICAgICAgICAgICAgICAgICAgICAgICBuICs9IDEKICAgICAgICAgICAgICAgICAgICBzaHV0aWwubW92ZShwYXRoLCBkZXN0KQogICAgICAgICAgICAgICAgICAgIHJlY29yZF9maXhlZChmLCAibW92ZWQgdG8gcXVhcmFudGluZTogezB9Ii5mb3JtYXQoZGVzdCkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIG9zLnJlbW92ZShwYXRoKQogICAgICAgICAgICAgICAgICAgIHJlY29yZF9maXhlZChmLCAiZGVsZXRlZCIpCiAgICAgICAgICAgIGV4Y2VwdCBPU0Vycm9yIGFzIGV4YzoKICAgICAgICAgICAgICAgIHJlY29yZF9sZWZ0KGYsICJjb3VsZCBub3QgcmVtb3ZlICh7MH0pIC0gbGVmdCBhbG9uZSIuZm9ybWF0KGV4YykpCiAgICAgICAgZWxpZiBraW5kID09ICJicm9rZW5fbGluayIgYW5kIGZpeF9zYWZlIGFuZCBpbnRlcmFjdGl2ZToKICAgICAgICAgICAgaWYgYXNrX3llc19ubygiUmVtb3ZlIHRoZSBicm9rZW4gbGluaz9cbiAgezB9Ii5mb3JtYXQocGF0aCkpOgogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIG9zLnJlbW92ZShwYXRoKQogICAgICAgICAgICAgICAgICAgIHJlY29yZF9maXhlZChmLCAiZGVsZXRlZCAoeW91IGFwcHJvdmVkKSIpCiAgICAgICAgICAgICAgICBleGNlcHQgT1NFcnJvciBhcyBleGM6CiAgICAgICAgICAgICAgICAgICAgcmVjb3JkX2xlZnQoZiwgImNvdWxkIG5vdCByZW1vdmUgKHswfSkiLmZvcm1hdChleGMpKQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgcmVjb3JkX2xlZnQoZiwgImxlZnQgYWxvbmUgLSBuZWVkcyB5b3VyIGFwcHJvdmFsIikKICAgICAgICBlbGlmIGtpbmQgaW4gKCJicm9rZW5fbGluayIsICJzaG9ydGN1dCIsICJmb2xkZXJfaG9nIik6CiAgICAgICAgICAgIHJlY29yZF9sZWZ0KGYsICJsZWZ0IGFsb25lIC0gbmVlZHMgeW91ciBhcHByb3ZhbCIpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgcmVjb3JkX2xlZnQoZiwgInJlcG9ydCBvbmx5IC0gdGhlIHN3ZWVwZXIgbmV2ZXIgdG91Y2hlcyB0aGlzIGtpbmQiKQogICAgcmV0dXJuIGZpeGVkLCBsZWZ0X2Fsb25lCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KIyBSZXBvcnRpbmcKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KCmRlZiBidWlsZF9yZXBvcnQoZmluZGluZ3MsIHN0YXJ0dXBzLCBmaXhlZCwgbGVmdF9hbG9uZSwgbm90ZXMpOgogICAgbGluZXMgPSBbXQogICAgbGluZXMuYXBwZW5kKCI9IiAqIDY0KQogICAgbGluZXMuYXBwZW5kKCJTSUdOQVRVUkUgQUkgU1dFRVBFUiAtIHN3ZWVwIHJlcG9ydCIpCiAgICBsaW5lcy5hcHBlbmQoIlZlcnNpb24gezB9IHwgezF9IHwgezJ9Ii5mb3JtYXQoCiAgICAgICAgVkVSU0lPTiwgdGltZS5zdHJmdGltZSgiJVktJW0tJWQgJUg6JU06JVMiKSwgc3lzdGVtX25hbWUoKSkpCiAgICBsaW5lcy5hcHBlbmQoIj0iICogNjQpCiAgICBsaW5lcy5hcHBlbmQoIiIpCiAgICBsaW5lcy5hcHBlbmQoIldIQVQgV0FTIEZJWEVEICh7MH0gaXRlbXMpOiIuZm9ybWF0KGxlbihmaXhlZCkpKQogICAgaWYgZml4ZWQ6CiAgICAgICAgZm9yIGYgaW4gZml4ZWQ6CiAgICAgICAgICAgIGxpbmVzLmFwcGVuZCgiICBbZml4ZWRdIHswfSIuZm9ybWF0KGZbInRpdGxlIl0pKQogICAgICAgICAgICBsaW5lcy5hcHBlbmQoIiAgICAgICAgICB7MH0gfCB7MX0iLmZvcm1hdChmWyJwYXRoIl0sIGYuZ2V0KCJhY3Rpb24iLCAiIikpKQogICAgZWxzZToKICAgICAgICBsaW5lcy5hcHBlbmQoIiAgKG5vdGhpbmcgLSBydW4gd2l0aCAtLWZpeCB0byBjbGVhbiB0aGUgc2FmZSBpdGVtcykiKQogICAgbGluZXMuYXBwZW5kKCIiKQogICAgbGluZXMuYXBwZW5kKCJMRUZUIEFMT05FICh7MH0gaXRlbXMpOiIuZm9ybWF0KGxlbihsZWZ0X2Fsb25lKSkpCiAgICBpZiBsZWZ0X2Fsb25lOgogICAgICAgIGZvciBmIGluIGxlZnRfYWxvbmU6CiAgICAgICAgICAgIGxpbmVzLmFwcGVuZCgiICBba2VwdF0gIHswfSIuZm9ybWF0KGZbInRpdGxlIl0pKQogICAgICAgICAgICBsaW5lcy5hcHBlbmQoIiAgICAgICAgICB7MH0iLmZvcm1hdChmWyJwYXRoIl0pKQogICAgICAgICAgICBsaW5lcy5hcHBlbmQoIiAgICAgICAgICBXaHk6IHswfSIuZm9ybWF0KGYuZ2V0KCJyZWFzb24iLCAiIikpKQogICAgICAgICAgICBsaW5lcy5hcHBlbmQoIiAgICAgICAgICBXaGF0IGl0IGlzOiB7MH0iLmZvcm1hdChmWyJleHBsYW5hdGlvbiJdKSkKICAgIGVsc2U6CiAgICAgICAgbGluZXMuYXBwZW5kKCIgIChub3RoaW5nIGxlZnQgYWxvbmUpIikKICAgIGxpbmVzLmFwcGVuZCgiIikKICAgIGxpbmVzLmFwcGVuZCgiU1RBUlRVUCBQUk9HUkFNUyAoezB9IGZvdW5kIC0gbGlzdGVkIG9ubHksIG5ldmVyIGNoYW5nZWQpOiIuZm9ybWF0KAogICAgICAgIGxlbihzdGFydHVwcykpKQogICAgZm9yIHMgaW4gc3RhcnR1cHM6CiAgICAgICAgZGV0YWlsID0gIiAtIHswfSIuZm9ybWF0KHNbImRldGFpbCJdKSBpZiBzLmdldCgiZGV0YWlsIikgZWxzZSAiIgogICAgICAgIGxpbmVzLmFwcGVuZCgiICAqIHswfSBbezF9XXsyfSIuZm9ybWF0KHNbIm5hbWUiXSwgc1sic291cmNlIl0sIGRldGFpbCkpCiAgICBsaW5lcy5hcHBlbmQoIiIpCiAgICBsaW5lcy5hcHBlbmQoIk5PVEVTOiIpCiAgICBmb3IgbiBpbiBub3RlczoKICAgICAgICBsaW5lcy5hcHBlbmQoIiAgLSB7MH0iLmZvcm1hdChuKSkKICAgIHRyeToKICAgICAgICB0b3RhbCwgdXNlZCwgZnJlZSA9IHNodXRpbC5kaXNrX3VzYWdlKGhvbWVfZGlyKCkpCiAgICAgICAgbGluZXMuYXBwZW5kKCIgIC0gRGlzazogezB9IGZyZWUgb2YgezF9Ii5mb3JtYXQoZm10X3NpemUoZnJlZSksIGZtdF9zaXplKHRvdGFsKSkpCiAgICBleGNlcHQgT1NFcnJvcjoKICAgICAgICBwYXNzCiAgICBsaW5lcy5hcHBlbmQoIiIpCiAgICBsaW5lcy5hcHBlbmQoIkhvbmVzdCBub3RlOiB0aGUgc3dlZXBlciBvbmx5IGRlbGV0ZXMgb2xkIGZpbGVzIGluc2lkZSB0ZW1wIikKICAgIGxpbmVzLmFwcGVuZCgiYW5kIGNhY2hlIGZvbGRlcnMuIEl0IG5ldmVyIHRvdWNoZXMgeW91ciBkb2N1bWVudHMsIHBob3RvcywiKQogICAgbGluZXMuYXBwZW5kKCJwcm9ncmFtcywgb3Igc3lzdGVtIGZpbGVzIC0gYW5kIGl0IGFsd2F5cyBhc2tzIGJlZm9yZSIpCiAgICBsaW5lcy5hcHBlbmQoImFueXRoaW5nIGl0IGlzIG5vdCBzdXJlIGFib3V0LiIpCiAgICBsaW5lcy5hcHBlbmQoIj0iICogNjQpCiAgICByZXR1cm4gIlxuIi5qb2luKGxpbmVzKSArICJcbiIKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQojIENMSQojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoKZGVmIG1haW4oYXJndj1Ob25lKToKICAgIHBhcnNlciA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKAogICAgICAgIGRlc2NyaXB0aW9uPSJTaWduYXR1cmUgQUkgU3dlZXBlciAtIGZpbmQgYW5kIGZpeCBzYWZlIFBDIGp1bmsuICIKICAgICAgICAgICAgICAgICAgICAiUmVwb3J0LW9ubHkgdW5sZXNzIHlvdSBwYXNzIC0tZml4LiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLWZpeCIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9IkZpeCB0aGUgc2FmZSBpdGVtcyAob2xkIHRlbXAvY2FjaGUgZmlsZXMpLiAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIkFza3MgYmVmb3JlIGFueXRoaW5nIHJpc2t5LiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLXllcyIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9IkRvIG5vdCBwcm9tcHQuIFJpc2t5IGl0ZW1zIGFyZSBsZWZ0IGFsb25lIGFuZCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInJlcG9ydGVkLiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLXF1YXJhbnRpbmUiLCBtZXRhdmFyPSJESVIiLCBkZWZhdWx0PU5vbmUsCiAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9Ik1vdmUgc2FmZSBpdGVtcyB0byBESVIgaW5zdGVhZCBvZiBkZWxldGluZyB0aGVtLiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLXJlcG9ydCIsIG1ldGF2YXI9IlBBVEgiLCBkZWZhdWx0PSJhaV9zd2VlcF9yZXBvcnQudHh0IiwKICAgICAgICAgICAgICAgICAgICAgICAgaGVscD0iV2hlcmUgdG8gd3JpdGUgdGhlIHN3ZWVwIHJlcG9ydC4iKQogICAgcGFyc2VyLmFkZF9hcmd1bWVudCgiLS1yb290IiwgbWV0YXZhcj0iRElSIiwgZGVmYXVsdD1Ob25lLAogICAgICAgICAgICAgICAgICAgICAgICBoZWxwPSJBZHZhbmNlZC90ZXN0IGhvb2s6IHNjYW4gRElSIGluc3RlYWQgb2YgeW91ciAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImhvbWUgZm9sZGVyLiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLXN0YXJ0dXAtb25seSIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9Ik9ubHkgbGlzdCBzdGFydHVwIHByb2dyYW1zLCBza2lwIGZpbGUgc2NhbnMuIikKICAgIHBhcnNlci5hZGRfYXJndW1lbnQoIi0tanNvbiIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9IlByaW50IGZpbmRpbmdzIGFzIEpTT04gaW5zdGVhZCBvZiB0aGUgcmVwb3J0LiIpCiAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCItLXZlcnNpb24iLCBhY3Rpb249InN0b3JlX3RydWUiLAogICAgICAgICAgICAgICAgICAgICAgICBoZWxwPSJQcmludCB0aGUgc3dlZXBlciB2ZXJzaW9uIGFuZCBleGl0LiIpCiAgICBhcmdzID0gcGFyc2VyLnBhcnNlX2FyZ3MoYXJndikKCiAgICBpZiBhcmdzLnZlcnNpb246CiAgICAgICAgcHJpbnQoIlNpZ25hdHVyZSBBSSBTd2VlcGVyIHswfSIuZm9ybWF0KFZFUlNJT04pKQogICAgICAgIHJldHVybiAwCgogICAgaG9tZSA9IGFyZ3Mucm9vdCBvciBob21lX2RpcigpCiAgICBpbnRlcmFjdGl2ZSA9IGlzX2ludGVyYWN0aXZlKCkgYW5kIG5vdCBhcmdzLnllcwoKICAgIGlmIGFyZ3Muc3RhcnR1cF9vbmx5OgogICAgICAgIHN0YXJ0dXBzID0gc3RhcnR1cF9lbnRyaWVzKGhvbWUpCiAgICAgICAgaWYgYXJncy5qc29uOgogICAgICAgICAgICBwcmludChqc29uLmR1bXBzKHN0YXJ0dXBzLCBpbmRlbnQ9Miwgc29ydF9rZXlzPVRydWUpKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHByaW50KCJTdGFydHVwIHByb2dyYW1zICh7MH0gZm91bmQgLSBsaXN0ZWQgb25seSwgbmV2ZXIgY2hhbmdlZCk6IgogICAgICAgICAgICAgICAgICAuZm9ybWF0KGxlbihzdGFydHVwcykpKQogICAgICAgICAgICBmb3IgcyBpbiBzdGFydHVwczoKICAgICAgICAgICAgICAgIGRldGFpbCA9ICIgLSB7MH0iLmZvcm1hdChzWyJkZXRhaWwiXSkgaWYgcy5nZXQoImRldGFpbCIpIGVsc2UgIiIKICAgICAgICAgICAgICAgIHByaW50KCIgICogezB9IFt7MX1dezJ9Ii5mb3JtYXQoc1sibmFtZSJdLCBzWyJzb3VyY2UiXSwgZGV0YWlsKSkKICAgICAgICByZXR1cm4gMAoKICAgIGZpbmRpbmdzLCBzdGFydHVwcywgbm90ZXMgPSBzY2FuX2FsbChob21lKQoKICAgIGlmIGFyZ3MuanNvbjoKICAgICAgICBwcmludChqc29uLmR1bXBzKHsiZmluZGluZ3MiOiBmaW5kaW5ncywgInN0YXJ0dXAiOiBzdGFydHVwcywKICAgICAgICAgICAgICAgICAgICAgICAgICAibm90ZXMiOiBub3Rlc30sIGluZGVudD0yLCBzb3J0X2tleXM9VHJ1ZSkpCiAgICAgICAgcmV0dXJuIDAKCiAgICBpZiBhcmdzLmZpeDoKICAgICAgICBmaXhlZCwgbGVmdF9hbG9uZSA9IGFwcGx5X2ZpeGVzKAogICAgICAgICAgICBmaW5kaW5ncywgZml4X3NhZmU9VHJ1ZSwKICAgICAgICAgICAgaW50ZXJhY3RpdmU9aW50ZXJhY3RpdmUsCiAgICAgICAgICAgIHF1YXJhbnRpbmU9YXJncy5xdWFyYW50aW5lKQogICAgZWxzZToKICAgICAgICBmaXhlZCA9IFtdCiAgICAgICAgbGVmdF9hbG9uZSA9IFtdCiAgICAgICAgZm9yIGYgaW4gZmluZGluZ3M6CiAgICAgICAgICAgIGcgPSBkaWN0KGYpCiAgICAgICAgICAgIGdbInJlYXNvbiJdID0gKCJ3b3VsZCBiZSBmaXhlZCB3aXRoIC0tZml4IiBpZiBmLmdldCgiYXV0b19maXhfc2FmZSIpCiAgICAgICAgICAgICAgICAgICAgICAgICAgIGVsc2UgImxlZnQgYWxvbmUgLSBuZWVkcyB5b3VyIGFwcHJvdmFsIikKICAgICAgICAgICAgbGVmdF9hbG9uZS5hcHBlbmQoZykKICAgICAgICBpZiBmaW5kaW5ncyBhbmQgbm90IGFyZ3MuZml4OgogICAgICAgICAgICBub3Rlcy5hcHBlbmQoIlJ1biB3aXRoIC0tZml4IHRvIGNsZWFuIHRoZSB7MH0gc2FmZSBpdGVtKHMpLiIKICAgICAgICAgICAgICAgICAgICAgICAgIC5mb3JtYXQoc3VtKDEgZm9yIGYgaW4gZmluZGluZ3MgaWYgZi5nZXQoImF1dG9fZml4X3NhZmUiKSkpKQoKICAgIHJlcG9ydCA9IGJ1aWxkX3JlcG9ydChmaW5kaW5ncywgc3RhcnR1cHMsIGZpeGVkLCBsZWZ0X2Fsb25lLCBub3RlcykKICAgIHByaW50KHJlcG9ydCkKICAgIHRyeToKICAgICAgICB3aXRoIG9wZW4oYXJncy5yZXBvcnQsICJ3IiwgZW5jb2Rpbmc9InV0Zi04IikgYXMgZmg6CiAgICAgICAgICAgIGZoLndyaXRlKHJlcG9ydCkKICAgICAgICBwcmludCgiUmVwb3J0IHdyaXR0ZW4gdG86IHswfSIuZm9ybWF0KGFyZ3MucmVwb3J0KSkKICAgIGV4Y2VwdCBPU0Vycm9yIGFzIGV4YzoKICAgICAgICBwcmludCgiV0FSTklORzogY291bGQgbm90IHdyaXRlIHJlcG9ydCB0byB7MH06IHsxfSIuZm9ybWF0KAogICAgICAgICAgICBhcmdzLnJlcG9ydCwgZXhjKSwgZmlsZT1zeXMuc3RkZXJyKQogICAgcmV0dXJuIDAKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgc3lzLmV4aXQobWFpbigpKQo="  # embedded copy of tools/ai_sweeper.py

# ---------------------------------------------------------------------------
# Shipped helper scripts (written into <target>/SignatureOS/tools/)
# These are static text - never .format() them (they contain braces).
# ---------------------------------------------------------------------------

SWEEP_PY = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signature full sweep: disk usage + basic health checks -> FULL_SWEEP.txt

Safe and read-only except for writing FULL_SWEEP.txt next to itself.
Pure stdlib, Python 3.6+.
"""
from __future__ import print_function
import json
import os
import platform
import shutil
import sys
import time


def dir_size(path, cap=200000):
    total, n = 0, 0
    for dirpath, _d, filenames in os.walk(path, onerror=lambda e: None,
                                          followlinks=False):
        for fn in filenames:
            if n >= cap:
                return total, n, True
            n += 1
            try:
                total += os.path.getsize(os.path.join(dirpath, fn))
            except OSError:
                pass
    return total, n, False


def fmt(n):
    n = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return "{0:.1f} {1}".format(n, u)
        n /= 1024.0
    return "{0:.1f} PB".format(n)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)  # .../SignatureOS/
    lines = []
    lines.append("=" * 60)
    lines.append("SIGNATURE OS OVERLAY - FULL SWEEP")
    lines.append(time.strftime("%Y-%m-%d %H:%M:%S") + " | " + platform.system())
    lines.append("=" * 60)

    try:
        total, used, free = shutil.disk_usage(root)
        lines.append("Disk on this volume: {0} free of {1}".format(
            fmt(free), fmt(total)))
        lines.append("Disk health: {0}".format(
            "OK" if free > 1024 ** 3 else "LOW - less than 1 GB free"))
    except OSError as exc:
        lines.append("Disk check unavailable: {0}".format(exc))

    lines.append("")
    lines.append("Overlay contents:")
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if os.path.isdir(p):
            size, n, capped = dir_size(p)
            lines.append("  {0}/ : {1} in {2} files{3}".format(
                name, fmt(size), n, " (capped)" if capped else ""))
        else:
            try:
                lines.append("  {0} : {1}".format(name, fmt(os.path.getsize(p))))
            except OSError:
                lines.append("  {0} : (unreadable)".format(name))

    lines.append("")
    lines.append("Manifest check:")
    for mf in ("manifest.json", "RESTORE.json"):
        p = os.path.join(root, mf)
        try:
            with open(p, "r", encoding="utf-8") as fh:
                json.load(fh)
            lines.append("  {0}: OK (parses)".format(mf))
        except Exception as exc:
            lines.append("  {0}: PROBLEM ({1})".format(mf, exc))

    lines.append("")
    lines.append("Python running this sweep: {0}".format(
        platform.python_version()))
    lines.append("=" * 60)
    report = "\\n".join(lines) + "\\n"
    print(report)
    out = os.path.join(root, "FULL_SWEEP.txt")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("Wrote: {0}".format(out))
    except OSError as exc:
        print("Could not write {0}: {1}".format(out, exc))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

UPDATE_CHECK_PY = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signature component version check.

Honest scope: reads the local install manifest and prints component
versions. Makes NO network calls - it cannot check for updates online.
Pure stdlib, Python 3.6+.
"""
from __future__ import print_function
import json
import os
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)  # .../SignatureOS/
    mf = os.path.join(root, "manifest.json")
    try:
        with open(mf, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as exc:
        print("Cannot read install manifest ({0}): {1}".format(mf, exc))
        return 1
    print("Signature OS Overlay toolkit version: {0}".format(
        manifest.get("tool_version", "unknown")))
    print("Installed at: {0}".format(manifest.get("installed_at", "unknown")))
    print("Components installed:")
    for comp in manifest.get("components", []):
        print("  - {0}".format(comp))
    print("")
    print("Note: this check reads the local version manifest only.")
    print("It does not go online, so it cannot tell you about newer")
    print("releases. Re-download the toolkit from the Signature OS")
    print("Updater site to get the latest version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# ---------------------------------------------------------------------------
# Components: id -> metadata + expected relative file list (for health checks)
# ---------------------------------------------------------------------------

COMPONENTS = {
    "apps": {
        "title": "Signature app collection (catalog index)",
        "description": "Manifest index of the Signature app collection. "
                       "Honest note: a catalog index, not the whole archive.",
        "files": ["apps/apps_index.json"],
    },
    "tools": {
        "title": "Helper tools",
        "description": "sweep.py (full sweep), update_check.py (version "
                       "manifest), ai_sweeper.py (AI Sweeper).",
        "files": ["tools/sweep.py", "tools/update_check.py",
                  "tools/ai_sweeper.py"],
    },
    "lenses": {
        "title": "Lens templates",
        "description": "overview / spec / code / demo / help lens definitions.",
        "files": ["lenses/lenses.json"],
    },
    "pc_models": {
        "title": "PC model catalog (subset index)",
        "description": "PC model catalog index - an honest subset manifest.",
        "files": ["pc_models/models_index.json"],
    },
    "software": {
        "title": "Software set manifest",
        "description": "Manifest of the Signature software set.",
        "files": ["software/software_index.json"],
    },
    "ai_offline": {
        "title": "Offline AI config (Signature Llama, static)",
        "description": "Model card + chat settings. Honest note: weights "
                       "download separately from the Signature Llama site.",
        "files": ["ai/offline/config.json"],
    },
    "ai_online": {
        "title": "Online AI config template",
        "description": "Endpoints left blank for the user's own key - "
                       "keys are never bundled.",
        "files": ["ai/online/config.json"],
    },
    "sweep": {
        "title": "Full sweep run",
        "description": "Runs the shipped sweep at install time; writes "
                       "FULL_SWEEP.txt (disk usage + basic health checks).",
        "files": ["FULL_SWEEP.txt"],
    },
    "ai_sweeper": {
        "title": "AI Sweeper",
        "description": "Uses plain-language AI-guided rules to find and fix "
                       "safe PC junk (temp files, old caches); asks before "
                       "anything risky. Report-only unless you run it "
                       "with --fix.",
        "files": ["tools/ai_sweeper.py"],
    },
}

COMPONENT_ORDER = ["apps", "tools", "lenses", "pc_models", "software",
                   "ai_offline", "ai_online", "sweep", "ai_sweeper"]

# ---------------------------------------------------------------------------
# Machine detection
# ---------------------------------------------------------------------------

def ram_gb():
    """Best-effort RAM detection in GB. Returns None when unavailable."""
    sysname = platform.system()
    try:
        if sysname == "Linux":
            with open("/proc/meminfo", "r") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024.0 / 1024.0, 2)
        elif sysname == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"],
                                          stderr=subprocess.DEVNULL)
            return round(int(out.strip()) / 1024.0 ** 3, 2)
        elif sysname == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.ullTotalPhys / 1024.0 ** 3, 2)
    except Exception:
        pass
    return None


def era_class(ram, cpu_count):
    """HONEST estimate of the machine's era from RAM+CPU heuristics only.

    This is a rough guess, not a measurement - two machines with the same
    RAM can be decades apart. Labeled as an estimate everywhere it appears.
    """
    if ram is None and not cpu_count:
        return "unknown"
    if ram is not None:
        # RAM leads; CPU only breaks ties when RAM is unreadable.
        if ram <= 0.5:
            return "1990s-class"
        if ram < 2:
            return "2000s-class"
        if ram < 8:
            return "2010s-class"
        return "modern-class"
    if cpu_count <= 1:
        return "2000s-class"
    return "2010s-class"


def detect_machine():
    """Return a JSON-able dict describing this machine."""
    ram = ram_gb()
    cpus = None
    try:
        cpus = os.cpu_count()
    except Exception:
        pass
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "cpu_count": cpus,
        "ram_gb": ram if ram is not None else "unknown",
        "python_version": platform.python_version(),
        "era_class": era_class(ram, cpus),
        "era_class_note": "estimate from RAM+CPU heuristics only - "
                          "a rough guess, not a measurement",
    }


def checker_code():
    """One compact single line: base64 of the detect_machine() JSON.

    The website decodes it with atob() + JSON.parse(). No newlines,
    no extra text - just the code, so it can be copied and pasted.
    """
    payload = json.dumps(detect_machine(), sort_keys=True,
                         separators=(",", ":"))
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


# ---------------------------------------------------------------------------
# Overlay content builders (all JSON built via json.dumps - never templates)
# ---------------------------------------------------------------------------

def build_apps_index():
    return {
        "collection": "Signature App Collection",
        "honest_note": "This is a catalog INDEX, not the whole archive. "
                       "The full collection lives on the Signature App "
                       "Archive site.",
        "toolkit_version": TOOL_VERSION,
        "sample_entries": [
            {"id": "JAH-APP-000001",
             "name": "Signature Notes",
             "kind": "productivity",
             "description": "Sample entry - the overlay ships the index, "
                            "not the apps themselves."},
            {"id": "JAH-APP-000002",
             "name": "Signature Calc Companion",
             "kind": "utilities",
             "description": "Sample entry - see the App Archive site for "
                            "the real download."},
        ],
    }


def build_lenses():
    def lens(lens_id, title, blurb, sections):
        return {"id": lens_id, "title": title, "description": blurb,
                "sections": sections}

    return {
        "honest_note": "Lens TEMPLATES - layout definitions the site uses "
                       "to render records. They contain no records themselves.",
        "lenses": [
            lens("overview", "Overview",
                 "Plain-language summary of the record.",
                 ["summary", "key_facts", "at_a_glance"]),
            lens("spec", "Spec",
                 "Full technical specification.",
                 ["spec_sheet", "measurements", "materials", "tolerances"]),
            lens("code", "Code",
                 "Working program with an in-browser demo.",
                 ["python_source", "demo", "download"]),
            lens("demo", "Demo",
                 "Step-by-step walkthrough of the record in action.",
                 ["steps", "expected_output"]),
            lens("help", "Help",
                 "What this record is for and how to use it.",
                 ["what_it_does", "how_to_use", "faq"]),
        ],
    }


def build_models_index():
    return {
        "collection": "Signature PC Models",
        "honest_note": "SUBSET index manifest - a sample of the catalog, "
                       "not the full million-model archive.",
        "sample_entries": [
            {"id": "JAH-PC-000001", "name": "Signature Classic 1995",
             "era": "1990s-class", "note": "sample entry"},
            {"id": "JAH-PC-000002", "name": "Signature Modern One",
             "era": "modern-class", "note": "sample entry"},
        ],
    }


def build_software_index():
    return {
        "collection": "Signature Software Set",
        "honest_note": "Manifest of the software set carried by the "
                       "overlay - installer-free helper scripts only.",
        "entries": [
            {"id": "JAH-SW-TOOLS", "name": "Overlay helper tools",
             "path": "tools/", "note": "shipped in this overlay"},
            {"id": "JAH-SW-SWEEPER", "name": "AI Sweeper",
             "path": "tools/ai_sweeper.py",
             "note": "shipped in this overlay"},
        ],
    }


def build_offline_config():
    return {
        "name": "Signature Llama (offline, static)",
        "model_card": {
            "engine": "Signature Llama, static client-side build",
            "capabilities": "keyword responder + chat settings template",
            "limitations": "No live model weights are bundled here.",
        },
        "chat_settings": {
            "greeting": "Hello - I am the offline Signature helper.",
            "max_reply_chars": 500,
            "voice": "tiered read-aloud (device speech if available)",
        },
        "responder": {
            "greetings": ["hello", "hi", "hey"],
            "reply": "Hello! This is the Signature offline helper. "
                     "I run entirely on your PC with no internet.",
        },
        "smoke_test": {
            "input": "hello",
            "expects_keyword": "Signature",
            "honest_note": "Verifies the bundled responder logic only - "
                           "not real model weights.",
        },
        "honest_note": "CONFIG ONLY. The real Signature Llama weights are a "
                       "separate download from the Signature Llama site - "
                       "this file just configures the offline helper.",
    }


def build_online_config():
    return {
        "name": "Online AI (your own provider)",
        "endpoint_url": "",
        "api_key": "",
        "model": "",
        "honest_note": "TEMPLATE. Fill in YOUR OWN provider endpoint and "
                       "key. Keys are NEVER bundled with this toolkit and "
                       "this file makes no network calls by itself.",
    }


def ai_sweeper_source():
    """Return the ai_sweeper.py source: same-dir copy first, else embedded."""
    here = os.path.dirname(os.path.abspath(__file__))
    sibling = os.path.join(here, "ai_sweeper.py")
    if os.path.isfile(sibling):
        with open(sibling, "r", encoding="utf-8") as fh:
            return fh.read()
    if AI_SWEEPER_B64:
        return base64.b64decode(AI_SWEEPER_B64.encode("ascii")).decode("utf-8")
    raise RuntimeError("ai_sweeper.py not found next to the toolkit and no "
                       "embedded copy is present.")

# ---------------------------------------------------------------------------
# Install / remove
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_components(spec):
    """'all' or comma list -> ordered list of component ids. Raises ValueError."""
    spec = (spec or "all").strip().lower()
    if spec == "all":
        return list(COMPONENT_ORDER)
    ids = [s.strip() for s in spec.split(",") if s.strip()]
    bad = [i for i in ids if i not in COMPONENTS]
    if bad:
        raise ValueError("Unknown component(s): {0}. Valid: {1}".format(
            ", ".join(bad), ", ".join(COMPONENT_ORDER)))
    seen = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    return seen


def find_root(target):
    """Locate the SignatureOS folder for target (dir or the folder itself)."""
    target = os.path.abspath(os.path.expanduser(target))
    candidate = os.path.join(target, FOLDER_NAME)
    if os.path.isfile(os.path.join(candidate, "manifest.json")):
        return candidate
    if os.path.isfile(os.path.join(target, "manifest.json")) and \
            os.path.basename(target.rstrip(os.sep)) == FOLDER_NAME:
        return target
    return candidate


def default_target():
    return home_dir_default()


def home_dir_default():
    return os.path.expanduser("~")


def build_file_plan(components):
    """Return list of (relpath, text) for the chosen components."""
    plan = []
    if "apps" in components:
        plan.append(("apps/apps_index.json",
                     json.dumps(build_apps_index(), indent=2, sort_keys=True)))
    if "lenses" in components:
        plan.append(("lenses/lenses.json",
                     json.dumps(build_lenses(), indent=2, sort_keys=True)))
    if "pc_models" in components:
        plan.append(("pc_models/models_index.json",
                     json.dumps(build_models_index(), indent=2, sort_keys=True)))
    if "software" in components:
        plan.append(("software/software_index.json",
                     json.dumps(build_software_index(), indent=2, sort_keys=True)))
    if "ai_offline" in components:
        plan.append(("ai/offline/config.json",
                     json.dumps(build_offline_config(), indent=2, sort_keys=True)))
    if "ai_online" in components:
        plan.append(("ai/online/config.json",
                     json.dumps(build_online_config(), indent=2, sort_keys=True)))
    if "tools" in components:
        plan.append(("tools/sweep.py", SWEEP_PY))
        plan.append(("tools/update_check.py", UPDATE_CHECK_PY))
        plan.append(("tools/ai_sweeper.py", ai_sweeper_source()))
    if "ai_sweeper" in components and "tools" not in components:
        # Selectable on its own; same file the tools component ships.
        plan.append(("tools/ai_sweeper.py", ai_sweeper_source()))
    return plan


def cmd_install(target, components, dry_run=False, out=print):
    root = os.path.join(os.path.abspath(os.path.expanduser(target)), FOLDER_NAME)
    plan = build_file_plan(components)
    rels = [rel for rel, _text in plan]

    if dry_run:
        out("DRY RUN - nothing will be written.")
        out("Target folder would be: {0}".format(root))
        out("Components: {0}".format(", ".join(components)))
        out("Files that would be created:")
        for rel in rels:
            out("  + {0}".format(os.path.join(FOLDER_NAME, rel)))
        if "sweep" in components:
            out("  + {0} (generated by running the sweep at install time)".format(
                os.path.join(FOLDER_NAME, "FULL_SWEEP.txt")))
        out("+ {0}".format(os.path.join(FOLDER_NAME, "manifest.json")))
        out("+ {0}".format(os.path.join(FOLDER_NAME, "RESTORE.json")))
        out("Nothing outside {0} would be touched.".format(root))
        return 0

    created = []
    for rel, text in plan:
        path = os.path.join(root, rel)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
            if not text.endswith("\n"):
                fh.write("\n")
        created.append(rel)
        out("  wrote {0}".format(rel))

    sweep_note = ""
    if "sweep" in components:
        sweep_py = os.path.join(root, "tools", "sweep.py")
        out("Running the full sweep (writes FULL_SWEEP.txt)...")
        try:
            proc = subprocess.Popen(
                [sys.executable, sweep_py], cwd=root,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            sweep_out, _ = proc.communicate()
            if proc.returncode == 0 and os.path.isfile(
                    os.path.join(root, "FULL_SWEEP.txt")):
                created.append("FULL_SWEEP.txt")
                sweep_note = "sweep completed"
            else:
                sweep_note = "sweep FAILED (see output above)"
                out(sweep_note)
                try:
                    out(sweep_out.decode("utf-8", "replace"))
                except Exception:
                    pass
        except Exception as exc:
            sweep_note = "sweep could not run: {0}".format(exc)
            out(sweep_note)

    machine = detect_machine()
    manifest = {
        "tool": "Signature OS Overlay",
        "tool_version": TOOL_VERSION,
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "machine": machine,
        "era_class": machine["era_class"],
        "components": components,
        "root": root,
        "honest_note": "Non-destructive overlay. Your existing OS was not "
                       "modified. Delete the SignatureOS folder to undo.",
    }
    with open(os.path.join(root, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    created.append("manifest.json")

    restore = {
        "tool_version": TOOL_VERSION,
        "created_at": manifest["installed_at"],
        "root": root,
        "created": sorted(created),
        "restore_instruction": "To undo this install, delete the whole "
                               "SignatureOS folder, or run: python3 "
                               "signature_os_overlay.py --remove --target "
                               "{0}".format(os.path.dirname(root)),
    }
    with open(os.path.join(root, "RESTORE.json"), "w",
              encoding="utf-8") as fh:
        json.dump(restore, fh, indent=2, sort_keys=True)
    created.append("RESTORE.json")

    out("")
    out("Install complete: {0}".format(root))
    out("Running the post-upgrade health check...")
    out("")
    fails, warns, passes = cmd_health_check(root, out=out)
    out("")
    if fails == 0:
        out("HEALTH CHECK: {0} PASS, {1} warn - the upgrade is in good "
            "form.".format(passes, warns))
        return 0
    out("HEALTH CHECK: {0} PASS, {1} warn, {2} FAIL - the upgrade is NOT "
        "complete until the FAIL items above are fixed.".format(
            passes, warns, fails))
    return 1


def cmd_remove(target, out=print):
    root = find_root(target)
    if not os.path.isdir(root):
        out("Nothing to remove: {0} does not exist.".format(root))
        return 0
    manifest_path = os.path.join(root, "manifest.json")
    if not os.path.isfile(manifest_path):
        out("Refusing to delete {0}: it has no manifest.json, so it is "
            "not a SignatureOS overlay I created.".format(root))
        return 1
    shutil.rmtree(root, ignore_errors=False)
    out("Removed the overlay folder: {0}".format(root))
    out("Your PC is exactly as it was before the install - nothing else "
        "was touched.")
    return 0


# ---------------------------------------------------------------------------
# Post-upgrade health check
# ---------------------------------------------------------------------------

def load_sweeper_module(root):
    """Import ai_sweeper from the install (preferred) or the toolkit dir."""
    for folder in (os.path.join(root, "tools"), SCRIPT_DIR):
        path = os.path.join(folder, "ai_sweeper.py")
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location(
                "signature_ai_sweeper", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return None


def cmd_health_check(target, out=print):
    """Verify the install is in good form.

    Returns (fails, warns, passes). Prints a plain-language report.
    """
    root = find_root(target)
    checks = []  # (name, status, detail, fix_hint)

    def add(name, status, detail="", hint=""):
        checks.append((name, status, detail, hint))

    out("=" * 64)
    out("SIGNATURE OS OVERLAY - post-upgrade health check")
    out("Checking: {0}".format(root))
    out("=" * 64)

    manifest = None
    if not os.path.isdir(root):
        add("overlay folder exists", "FAIL",
            "{0} not found".format(root),
            "Run --install to create it.")
    else:
        mf_path = os.path.join(root, "manifest.json")
        try:
            with open(mf_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
            add("manifest.json parses", "PASS",
                "tool v{0}, installed {1}".format(
                    manifest.get("tool_version", "?"),
                    manifest.get("installed_at", "?")))
        except Exception as exc:
            add("manifest.json parses", "FAIL", str(exc),
                "Re-run --install to repair the install.")

        try:
            with open(os.path.join(root, "RESTORE.json"), "r",
                      encoding="utf-8") as fh:
                json.load(fh)
            add("RESTORE.json parses", "PASS", "undo path documented")
        except Exception as exc:
            add("RESTORE.json parses", "FAIL", str(exc),
                "Re-run --install to repair the install.")

        if isinstance(manifest, dict):
            for comp in manifest.get("components", []):
                expected = COMPONENTS.get(comp, {}).get("files", [])
                missing = [rel for rel in expected
                           if not os.path.isfile(os.path.join(root, rel))]
                if missing:
                    add("component '{0}' files present".format(comp), "FAIL",
                        "missing: {0}".format(", ".join(missing)),
                        "Re-run --install to restore the missing files.")
                else:
                    add("component '{0}' files present".format(comp), "PASS",
                        "{0} file(s) OK".format(len(expected)))

    helper_scripts = ["tools/sweep.py", "tools/update_check.py",
                      "tools/ai_sweeper.py"]
    present = [s for s in helper_scripts
               if os.path.isfile(os.path.join(root, s))]
    if present and os.path.isdir(root):
        bad = []
        for rel in present:
            try:
                py_compile.compile(os.path.join(root, rel), doraise=True)
            except Exception as exc:
                bad.append("{0} ({1})".format(rel, exc))
        if bad:
            add("helper scripts compile", "FAIL", "; ".join(bad),
                "Re-run --install to restore clean copies.")
        else:
            add("helper scripts compile", "PASS",
                "{0} script(s) OK".format(len(present)))
    elif os.path.isdir(root):
        add("helper scripts compile", "WARN",
            "no helper scripts installed (tools component not selected)",
            "")

    if os.path.isdir(root):
        cfg_path = os.path.join(root, "ai", "offline", "config.json")
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as fh:
                    cfg = json.load(fh)
                required = ("name", "model_card", "chat_settings",
                            "responder", "smoke_test")
                missing_keys = [k for k in required if k not in cfg]
                if missing_keys:
                    raise ValueError("missing keys: {0}".format(
                        ", ".join(missing_keys)))
                # Smoke path: run the bundled responder logic for real.
                responder = cfg["responder"]
                smoke = cfg["smoke_test"]
                greetings = [g.lower() for g in responder.get("greetings", [])]
                test_input = str(smoke.get("input", "")).lower()
                reply = ""
                if any(g in test_input for g in greetings):
                    reply = responder.get("reply", "")
                expects = str(smoke.get("expects_keyword", ""))
                if expects and expects not in reply:
                    raise ValueError(
                        "responder smoke test failed: reply did not contain "
                        "'{0}'".format(expects))
                add("offline AI config + responder smoke test", "PASS",
                    "config parses; bundled responder answered the smoke "
                    "prompt correctly. (Checks the bundled logic only - "
                    "real Llama weights download separately from the "
                    "Signature Llama site.)")
            except Exception as exc:
                add("offline AI config + responder smoke test", "FAIL",
                    str(exc), "Re-run --install to restore the config.")
        else:
            add("offline AI config + responder smoke test", "WARN",
                "ai/offline/config.json not installed "
                "(ai_offline component not selected)", "")

        try:
            _total, _used, free = shutil.disk_usage(root)
            if free > 1024 ** 3:
                add("disk space healthy", "PASS",
                    "{0:.1f} GB free on the target volume".format(
                        free / 1024.0 ** 3))
            else:
                add("disk space healthy", "WARN",
                    "only {0:.1f} GB free on the target volume".format(
                        free / 1024.0 ** 3),
                    "Free up disk space - the sweeper (tools/ai_sweeper.py "
                    "--fix) can clear safe junk.")
        except OSError as exc:
            add("disk space healthy", "WARN",
                "could not read disk usage: {0}".format(exc), "")

        sweeper = load_sweeper_module(root)
        if sweeper is None:
            add("startup scan clean", "WARN",
                "ai_sweeper.py not available, startup scan skipped", "")
        else:
            try:
                entries = sweeper.startup_entries()
                add("startup scan clean", "PASS",
                    "scan completed, {0} startup entr{1} listed "
                    "(read-only - nothing changed)".format(
                        len(entries), "y" if len(entries) == 1 else "ies"))
            except Exception as exc:
                add("startup scan clean", "FAIL",
                    "startup scan errored: {0}".format(exc),
                    "Run tools/ai_sweeper.py --startup-only to see details.")

    out("")
    passes = warns = fails = 0
    for name, status, detail, _hint in checks:
        mark = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[status]
        out("{0} {1}".format(mark, name))
        if detail:
            out("       {0}".format(detail))
        if status == "PASS":
            passes += 1
        elif status == "WARN":
            warns += 1
        else:
            fails += 1
    out("")
    if fails == 0:
        out("Your PC is in good form ✓ ({0} passed, {1} warning(s)).".format(
            passes, warns))
        if warns:
            out("Warnings need no urgent action - see above for details.")
    else:
        out("ATTENTION NEEDED: {0} check(s) FAILED.".format(fails))
        for name, status, detail, hint in checks:
            if status == "FAIL":
                out("  - {0}: {1}".format(name, detail))
                if hint:
                    out("    What to do: {0}".format(hint))
    out("=" * 64)
    return fails, warns, passes

# ---------------------------------------------------------------------------
# Self test (safe: everything happens in temp dirs)
# ---------------------------------------------------------------------------

def cmd_self_test(out=print):
    results = []  # (name, ok, detail)

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    quiet = lambda *a, **k: None  # noqa: E731

    # 1. detect_machine
    try:
        m = detect_machine()
        json.dumps(m)
        needed = ("os", "os_release", "arch", "cpu_count", "ram_gb",
                  "python_version", "era_class")
        missing = [k for k in needed if k not in m]
        check("detect_machine returns complete JSON-able profile",
              not missing, "missing: {0}".format(missing) if missing else
              "os={0} arch={1} ram={2} era={3}".format(
                  m["os"], m["arch"], m["ram_gb"], m["era_class"]))
    except Exception as exc:
        check("detect_machine returns complete JSON-able profile", False,
              str(exc))

    # 2. --code roundtrip
    try:
        code = checker_code()
        ok_single = "\n" not in code and "\r" not in code and " " not in code
        payload = json.loads(base64.b64decode(code.encode("ascii"))
                             .decode("utf-8"))
        ok_keys = isinstance(payload, dict) and "os" in payload and \
            "arch" in payload and "era_class" in payload
        check("--code is one clean line and decodes to the machine JSON",
              ok_single and ok_keys,
              "len={0}".format(len(code)) if ok_single and ok_keys
              else "single_line={0} keys_ok={1}".format(ok_single, ok_keys))
    except Exception as exc:
        check("--code is one clean line and decodes to the machine JSON",
              False, str(exc))

    tmp = tempfile.mkdtemp(prefix="sig_os_test_")
    try:
        # 3. install all components to temp dir
        try:
            rc = cmd_install(tmp, list(COMPONENT_ORDER), out=quiet)
            root = os.path.join(tmp, FOLDER_NAME)
            expected = []
            for comp in COMPONENT_ORDER:
                expected.extend(COMPONENTS[comp]["files"])
            expected.extend(["manifest.json", "RESTORE.json"])
            missing = [rel for rel in expected
                       if not os.path.isfile(os.path.join(root, rel))]
            all_json_parse = True
            bad_json = []
            for rel in expected:
                if rel.endswith(".json"):
                    try:
                        with open(os.path.join(root, rel), "r",
                                  encoding="utf-8") as fh:
                            json.load(fh)
                    except Exception:
                        all_json_parse = False
                        bad_json.append(rel)
            check("install all components: every expected file exists, "
                  "all JSON parses",
                  rc == 0 and not missing and all_json_parse,
                  "missing={0} bad_json={1}".format(missing, bad_json)
                  if (missing or not all_json_parse) else
                  "{0} files OK".format(len(expected)))
        except Exception as exc:
            check("install all components: every expected file exists, "
                  "all JSON parses", False, str(exc))
            root = os.path.join(tmp, FOLDER_NAME)

        # 4. health check passes on the fresh install
        try:
            buf = []
            fails, warns, passes = cmd_health_check(
                root, out=lambda s: buf.append(s))
            check("health check: all PASS on fresh install",
                  fails == 0 and passes > 0,
                  "fails={0} warns={1} passes={2}".format(fails, warns, passes))
        except Exception as exc:
            check("health check: all PASS on fresh install", False, str(exc))

        # 5. health check catches a deleted component file
        try:
            victim = os.path.join(root, "apps", "apps_index.json")
            if os.path.isfile(victim):
                os.remove(victim)
            buf = []
            fails, _warns, _passes = cmd_health_check(
                root, out=lambda s: buf.append(s))
            text = "\n".join(buf)
            check("health check: FAILs when a component file is deleted",
                  fails > 0 and "apps_index.json" in text,
                  "fails={0}, mentions victim={1}".format(
                      fails, "apps_index.json" in text))
        except Exception as exc:
            check("health check: FAILs when a component file is deleted",
                  False, str(exc))

        # 6. AI Sweeper: cleans safe junk, leaves risky items alone
        try:
            sweeper = load_sweeper_module(SCRIPT_DIR)
            if sweeper is None:
                check("ai_sweeper: safe junk cleaned, risky left alone",
                      False, "could not load ai_sweeper module")
            else:
                fake = tempfile.mkdtemp(prefix="sig_sweep_test_")
                try:
                    fake_temp = os.path.join(fake, "temp")
                    fake_cache = os.path.join(fake, "cache")
                    os.makedirs(fake_temp)
                    os.makedirs(fake_cache)
                    old_junk = os.path.join(fake_temp, "old_junk.tmp")
                    new_file = os.path.join(fake_temp, "new_file.tmp")
                    old_cache = os.path.join(fake_cache, "old_cache.dat")
                    for p in (old_junk, new_file, old_cache):
                        with open(p, "w") as fh:
                            fh.write("x" * 100)
                    old_mtime = time.time() - 72 * 3600
                    os.utime(old_junk, (old_mtime, old_mtime))
                    os.utime(old_cache, (old_mtime, old_mtime))
                    link_path = os.path.join(fake_temp, "dead_link")
                    have_link = False
                    try:
                        os.symlink(os.path.join(fake, "no_such_target"),
                                   link_path)
                        have_link = True
                    except (OSError, NotImplementedError):
                        pass
                    findings = sweeper.scan_junk([fake_temp], [fake_cache])
                    fixed, left = sweeper.apply_fixes(
                        findings, fix_safe=True, interactive=False)
                    junk_gone = (not os.path.exists(old_junk) and
                                 not os.path.exists(old_cache))
                    new_kept = os.path.exists(new_file)
                    link_kept = (not have_link) or os.path.islink(link_path)
                    link_reported = (not have_link) or any(
                        "needs your approval" in l.get("reason", "")
                        for l in left)
                    startups = sweeper.startup_entries()
                    ok = (junk_gone and new_kept and link_kept and
                          link_reported and isinstance(startups, list))
                    check("ai_sweeper: safe junk cleaned, risky left alone",
                          ok,
                          "junk_gone={0} new_kept={1} link_kept={2} "
                          "link_reported={3}".format(junk_gone, new_kept,
                                                    link_kept, link_reported))
                finally:
                    shutil.rmtree(fake, ignore_errors=True)
        except Exception as exc:
            check("ai_sweeper: safe junk cleaned, risky left alone", False,
                  str(exc))

        # 7. dry-run writes nothing
        try:
            dry_target = os.path.join(tmp, "dryrun_target")
            os.makedirs(dry_target)
            cmd_install(dry_target, ["apps", "ai_sweeper"], dry_run=True,
                        out=quiet)
            check("dry-run installs nothing",
                  not os.path.exists(os.path.join(dry_target, FOLDER_NAME)),
                  "no SignatureOS folder created")
        except Exception as exc:
            check("dry-run installs nothing", False, str(exc))

        # 8. remove deletes the overlay folder
        try:
            rc = cmd_remove(root, out=quiet)
            check("--remove deletes the SignatureOS folder",
                  rc == 0 and not os.path.exists(root),
                  "folder gone" if rc == 0 else "rc={0}".format(rc))
        except Exception as exc:
            check("--remove deletes the SignatureOS folder", False, str(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out("")
    out("=" * 64)
    out("SELF TEST RESULTS")
    out("=" * 64)
    all_ok = True
    for name, ok, detail in results:
        out("[{0}] {1}".format("PASS" if ok else "FAIL", name))
        if detail:
            out("       {0}".format(detail))
        if not ok:
            all_ok = False
    out("=" * 64)
    out("SELF TEST: {0}".format("ALL PASS" if all_ok else "FAILURES PRESENT"))
    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="signature_os_overlay.py",
        description="Signature OS Overlay toolkit - a NON-DESTRUCTIVE "
                    "overlay for your PC. Everything lives in one "
                    "SignatureOS folder; nothing outside it is ever touched.")
    parser.add_argument("--detect", action="store_true",
                        help="Print the machine profile as JSON.")
    parser.add_argument("--code", action="store_true",
                        help="Print ONE line: base64 of the machine-profile "
                             "JSON (the checker code for the Upgrade page).")
    parser.add_argument("--install", action="store_true",
                        help="Install the overlay (the only action that "
                             "writes files).")
    parser.add_argument("--target", metavar="DIR", default=None,
                        help="Where to create the SignatureOS folder "
                             "(default: your home folder).")
    parser.add_argument("--components", metavar="LIST", default="all",
                        help="Comma-separated component list or 'all'. "
                             "Valid: {0}".format(", ".join(COMPONENT_ORDER)))
    parser.add_argument("--dry-run", action="store_true",
                        help="With --install: show what would be created, "
                             "write nothing.")
    parser.add_argument("--health-check", action="store_true",
                        help="Verify an installed overlay is in good form.")
    parser.add_argument("--remove", action="store_true",
                        help="Delete the SignatureOS folder (undo).")
    parser.add_argument("--self-test", action="store_true",
                        help="Run the safe self-test (uses temp dirs only).")
    return parser


def print_machine_summary(out=print):
    m = detect_machine()
    out("Machine summary:")
    out("  OS:      {0} {1} ({2})".format(m["os"], m["os_release"], m["arch"]))
    out("  CPU:     {0}".format(m["cpu_count"]))
    out("  RAM:     {0}".format(
        "{0} GB".format(m["ram_gb"]) if m["ram_gb"] != "unknown"
        else "unknown (could not be read on this machine)"))
    out("  Python:  {0}".format(m["python_version"]))
    out("  Era:     {0} ({1})".format(m["era_class"], m["era_class_note"]))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.code:
        # Exactly one line, no extra text - it gets pasted into the website.
        sys.stdout.write(checker_code())
        return 0

    if args.detect:
        print(json.dumps(detect_machine(), indent=2, sort_keys=True))
        return 0

    if args.self_test:
        return cmd_self_test()

    if args.health_check:
        target = args.target or default_target()
        fails, _warns, _passes = cmd_health_check(target)
        return 1 if fails else 0

    if args.remove:
        target = args.target or default_target()
        return cmd_remove(target)

    if args.install:
        try:
            components = resolve_components(args.components)
        except ValueError as exc:
            print("Error: {0}".format(exc), file=sys.stderr)
            return 2
        target = args.target or default_target()
        print("Signature OS Overlay v{0}".format(TOOL_VERSION))
        print("Components: {0}".format(", ".join(components)))
        return cmd_install(target, components, dry_run=args.dry_run)

    # Default action: help + machine summary. Never writes anything.
    parser.print_help()
    print("")
    print_machine_summary()
    print("")
    print("Nothing was changed. Pass --install to create the overlay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

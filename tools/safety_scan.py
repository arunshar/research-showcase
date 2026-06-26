#!/usr/bin/env python3
"""
safety_scan.py — gate before publishing the public showcase.

Verifies the generated README.md / showcase.html contain ONLY public content:
  1. every github.com/arunshar/<repo> link points to a PUBLIC, non-fork repo
  2. no local filesystem paths or file:// links
  3. no SEVIS / compensation secret shapes
  4. no private-repo names or sensitive substrings

Queries GitHub live for visibility. Exit 0 = safe to publish, 1 = blocked.
Run: python3 tools/safety_scan.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN = [
    "doc-atlas", "moss-pigrpo", "-anon", "immigration", "harbormaster",
    "career-narratives", "temporal-prep", "gm-validation", "databricks-production",
    "spatial-program", "claude-state", "skills-harness", "skills-manage",
    "immigration-dossier", "mirror-platform", "desktop-tutorial",
    " eb-1a", "eb1a", " niw ", "sevis",
]
SECRET = re.compile(r"N0\d{7,10}|1[89][0-9][Kk] ?[-–] ?2[0-8][0-9][Kk]"
                    r"|\$ ?[12][0-9]{2},?000|\b(1[89][0-9]|2[0-8][0-9])[Kk]\b")


def gh_visibility():
    out = subprocess.run(
        ["gh", "repo", "list", "arunshar", "--limit", "500",
         "--json", "name,visibility,isFork"],
        capture_output=True, text=True, check=True).stdout
    repos = json.loads(out)
    public = {r["name"].lower() for r in repos
              if r["visibility"] == "PUBLIC" and not r["isFork"]}
    private = {r["name"].lower() for r in repos if r["visibility"] == "PRIVATE"}
    return public, private


def main():
    text = ""
    for fn in ("README.md", "showcase.html"):
        fp = os.path.join(ROOT, fn)
        if os.path.exists(fp):
            text += open(fp, encoding="utf-8", errors="ignore").read()
    public, private = gh_visibility()
    fail = 0

    slugs = {s for s in re.findall(r"github\.com/arunshar/([A-Za-z0-9._-]+)", text)
             if s.lower() != "arunshar"}
    bad = [s for s in slugs if s.lower() not in public]
    if bad:
        print("  LINK-FAIL (not public/non-fork):", bad); fail += 1
    print(f"[1] {len(slugs)} repo links, all public: {'YES' if not bad else 'NO'}")

    if re.search(r"/Users/|file://", text):
        print("  PATH-FAIL: local path / file:// present"); fail += 1
    else:
        print("[2] no local paths / file:// : OK")

    if SECRET.search(text):
        print("  SECRET-FAIL:", SECRET.findall(text)[:3]); fail += 1
    else:
        print("[3] no secret shapes : OK")

    low = text.lower()
    hits = [w for w in FORBIDDEN if w in low]
    if hits:
        print("  SUBSTR-FAIL:", hits); fail += 1
    else:
        print("[4] no forbidden substrings : OK")

    print("\nSAFETY:", "PASS" if fail == 0 else f"FAIL ({fail})")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

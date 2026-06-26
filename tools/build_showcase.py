#!/usr/bin/env python3
"""
build_showcase.py — generate a PUBLIC research/code showcase index for Arun Sharma.

Curated, theme-grouped index of PUBLIC GitHub repositories + live sites. It queries
GitHub live and, for every curated repo, includes it ONLY if GitHub reports it as
PUBLIC and non-fork. A private repo therefore can never appear here, even if it is
listed in the curation below by mistake.

Outputs (repo root): README.md, showcase.html
Run: python3 tools/build_showcase.py
"""
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

OWNER = "arunshar"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# Curation: theme -> [(repo_name, fallback_one_liner)]
# Repos tied to active double-blind submissions (moss-pigrpo*, pcrf*-anon) and
# stale coursework are deliberately omitted.
# ---------------------------------------------------------------------------
THEMES = [
    ("PhD thesis: distortion-aware spatial AI", [
        ("Thesis-Final", "Distortion-Aware Spatial Data Science (PhD dissertation, UMN)."),
        ("stagd-trajectory-gap", "Space-time prism + Abnormal Gap Measure; numpy reference implementation."),
        ("tgard-rendezvous", "TGARD reachable-set intersection for possible-rendezvous areas."),
        ("tss-rendezvous-region", "Space-time-prism intersection for rendezvous regions."),
        ("AbnormalGapMeasure", "Abnormal trajectory-gap detection."),
        ("RendezvousDetection", "Maritime rendezvous detection."),
    ]),
    ("Spatial & trajectory ML", [
        ("geotrace-agent", "Spatiotemporal reasoning agent with space-time-prism geometry."),
        ("darkvessel-stack", "Dark-vessel / remote-sensing detection stack."),
        ("mapfix-spatial", "Distortion-aware interactive geospatial map correction."),
        ("pin-service", "Production-grade gRPC PUDO pin-selection microservice for AVs."),
        ("trajprompt", "Trajectory prompting / representation."),
        ("stdm-survey-toolkit", "Moran's I + spatial outlier detection; numpy reference."),
        ("webglobe-raster", "Tiled map-reduce raster aggregation; numpy reference."),
    ]),
    ("3D vision & remote sensing", [
        ("sat-splat-distort", "Satellite Gaussian-splat / distortion experiments."),
        ("geosam-3d", "Geospatial SAM in 3D."),
        ("physflow-earth", "Physics-flow modeling for Earth data."),
    ]),
    ("Physics-informed & generative ML", [
        ("pi-grpo", "Physics-informed PPO / DPO / GRPO trajectory reward stack."),
        ("Kriging-Diffusion", "Kriging-informed diffusion for spatial downscaling."),
        ("Physics-Informed-Diffusion-Probabilistic-Model", "Physics-informed diffusion probabilistic model (KDD 2025 track)."),
        ("pcrf-keynote", "Physics-Constrained Rectified Flow keynote deck (Ray / PyTorch Summit)."),
    ]),
    ("Agents, systems & infrastructure", [
        ("atria", "Production-grade primitives for AI agents on Temporal (durable execution)."),
        ("slurm-dag", "Content-addressed dependency DAGs over Slurm (fan-out / merge)."),
        ("recce", "AI location scouting, script to shoot day."),
        ("spatial-atlas", "Spatial-aware research agent for the AgentBeats Challenge."),
        ("researchbench-leaderboard", "Leaderboard for the ResearchToolBench benchmark."),
    ]),
    ("Languages & fundamentals", [
        ("lox-go", "Lox programming language in Go."),
        ("lox-rust", "Lox programming language in Rust."),
    ]),
    ("Teaching & Claude Code", [
        ("claude-code-course", "Self-paced two-day course on advanced Claude Code."),
    ]),
    ("Portfolio & web", [
        ("portfolio", "Academic portfolio site (per-project paper pages + publications)."),
        ("arunshar.github.io", "Root mirror of the academic portfolio."),
    ]),
]

LIVE_SITES = [
    ("https://arunshar.com/", "Academic site — research, publications, projects."),
    ("https://arunshar.com/portfolio", "Full portfolio with a paper page per project."),
    ("https://arunshar.com/pcrf-keynote/", "Physics-Constrained Rectified Flow keynote deck."),
]

# ---------------------------------------------------------------------------
def gh_repos():
    out = subprocess.run(
        ["gh", "repo", "list", OWNER, "--limit", "500", "--json",
         "name,visibility,isFork,description,url,pushedAt,primaryLanguage,stargazerCount"],
        capture_output=True, text=True, check=True).stdout
    repos = json.load(io_str(out))
    m = {}
    for r in repos:
        r["lang"] = (r.get("primaryLanguage") or {}).get("name", "") if r.get("primaryLanguage") else ""
        m[r["name"].lower()] = r
    return m

def io_str(s):
    import io
    return io.StringIO(s)

def main():
    repos = gh_repos()
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    included, skipped = [], []

    themes_out = []
    for theme, items in THEMES:
        cards = []
        for name, fallback in items:
            r = repos.get(name.lower())
            # HARD GATE: must exist, be PUBLIC, and not a fork.
            if not r or r.get("visibility") != "PUBLIC" or r.get("isFork"):
                skipped.append(name)
                continue
            desc = (r.get("description") or "").strip() or fallback
            cards.append({"name": r["name"], "url": r["url"], "desc": desc,
                          "lang": r["lang"], "stars": r.get("stargazerCount", 0)})
            included.append(r["name"])
        if cards:
            themes_out.append((theme, cards))

    write_readme(themes_out, gen)
    write_html(themes_out, gen)

    print(f"included {len(included)} repos across {len(themes_out)} themes", file=sys.stderr)
    if skipped:
        print("skipped (not found / not public / fork): " + ", ".join(skipped), file=sys.stderr)

def write_readme(themes, gen):
    L = ["# Arun Sharma — Research & Code", "",
         "Spatial data science, GeoAI, and trustworthy / physics-informed machine "
         "learning. A curated index of public repositories and live sites.", "",
         f"_Generated {gen} from public GitHub repositories._", "",
         "## Live", ""]
    for url, d in LIVE_SITES:
        L.append(f"- [{url}]({url}) — {d}")
    L.append("")
    for theme, cards in themes:
        L.append(f"## {theme}")
        L.append("")
        for c in cards:
            meta = " · ".join(x for x in [c["lang"], (f"⭐ {c['stars']}" if c["stars"] else "")] if x)
            tail = f"  _( {meta} )_" if meta else ""
            L.append(f"- [{c['name']}]({c['url']}) — {c['desc']}{tail}")
        L.append("")
    L.append("---")
    L.append("")
    L.append("Profile: [github.com/arunshar](https://github.com/arunshar)")
    with open(os.path.join(ROOT, "README.md"), "w") as f:
        f.write("\n".join(L))

def write_html(themes, gen):
    def esc(s):
        return html.escape(str(s), quote=True)
    nav, main = [], []
    for theme, cards in themes:
        tid = "t-" + re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")
        nav.append(f'<a href="#{tid}" class="navitem">{esc(theme)}<span class="cnt">{len(cards)}</span></a>')
        main.append(f'<section id="{tid}"><h2>{esc(theme)}</h2><div class="grid">')
        for c in cards:
            meta = " · ".join(x for x in [esc(c["lang"]), (f"★ {c['stars']}" if c["stars"] else "")] if x)
            main.append(
                f'<a class="card" href="{esc(c["url"])}" target="_blank" rel="noopener">'
                f'<div class="name">{esc(c["name"])}</div>'
                f'<div class="desc">{esc(c["desc"])}</div>'
                f'<div class="meta">{meta}</div></a>')
        main.append('</div></section>')
    live = "".join(
        f'<a class="livechip" href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a>'
        for u, _ in LIVE_SITES)
    doc = SHOWCASE_TMPL.replace("__GEN__", gen).replace("__NAV__", "\n".join(nav)) \
                       .replace("__MAIN__", "\n".join(main)).replace("__LIVE__", live)
    with open(os.path.join(ROOT, "showcase.html"), "w") as f:
        f.write(doc)

SHOWCASE_TMPL = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arun Sharma — Research & Code</title>
<style>
:root{--bg:#0f1115;--panel:#161922;--ink:#e6e8ee;--mut:#9aa3b2;--line:#252a36;--acc:#6ea8fe}
@media(prefers-color-scheme:light){:root{--bg:#f6f7f9;--panel:#fff;--ink:#1b1f27;--mut:#5b6472;--line:#e4e7ec;--acc:#2563eb}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
.wrap{display:flex;min-height:100vh}
.side{width:280px;flex:0 0 280px;background:var(--panel);border-right:1px solid var(--line);
position:sticky;top:0;height:100vh;overflow:auto;padding:20px 14px}
.side h1{font-size:16px;margin:0 0 2px}.side .sub{color:var(--mut);font-size:12px;margin-bottom:14px}
.navitem{display:flex;gap:8px;padding:6px 8px;border-radius:8px;color:var(--ink);font-size:13px}
.navitem:hover{background:var(--bg)}.navitem .cnt{margin-left:auto;color:var(--mut)}
.main{flex:1;padding:30px 34px;max-width:1100px}
.lead{font-size:15px;color:var(--mut);margin:0 0 14px;max-width:70ch}
.live{margin:0 0 22px}.livechip{display:inline-block;background:var(--panel);border:1px solid var(--line);
border-radius:20px;padding:4px 12px;margin:3px;font-size:13px}
section{margin:26px 0;border-top:1px solid var(--line);padding-top:10px}
section h2{font-size:17px;margin:6px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:13px 15px;color:var(--ink)}
.card:hover{border-color:var(--acc)}
.card .name{font-weight:700;color:var(--acc)}
.card .desc{font-size:13px;color:var(--mut);margin:5px 0 8px}
.card .meta{font-size:11px;color:var(--mut)}
@media(max-width:780px){.wrap{flex-direction:column}.side{width:100%;height:auto;position:static}.main{padding:18px}}
</style></head>
<body><div class="wrap">
<aside class="side"><h1>Arun Sharma</h1><div class="sub">Research &amp; Code · __GEN__</div>
<nav>__NAV__</nav></aside>
<main class="main">
<h1 style="font-size:22px;margin:0 0 8px">Research &amp; Code</h1>
<p class="lead">Spatial data science, GeoAI, and trustworthy / physics-informed machine learning. Curated public repositories and live sites.</p>
<div class="live">__LIVE__</div>
__MAIN__
<p style="color:var(--mut);font-size:12.5px;margin-top:26px">Profile: <a href="https://github.com/arunshar" target="_blank" rel="noopener">github.com/arunshar</a></p>
</main></div></body></html>"""

if __name__ == "__main__":
    main()

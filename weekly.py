"""Weekly UFO banner + daily words of wisdom for the GitHub profile README.

Run by launchd every weekday at 09:00 (see launchd/com.pauldawson.ufo-profile.plist), or by hand:

    python3 weekly.py                     # catch up the current week
    python3 weekly.py --dry-run           # generate and update files, but no git commit/push
    python3 weekly.py --today 2026-11-16  # pretend it's that date (testing)
    python3 weekly.py --no-claude         # use the built-in generator / skip Claude calls

What a run does, for the current week (Monday-Friday):
  1. If this week has no banner yet: ask Claude CLI to design a new animated SVG banner,
     validate it, and fall back to the built-in generator (make_svgs.py) if anything is off.
  2. For every weekday from Monday up to today that has no word of wisdom yet: ask Claude
     CLI for one.
  3. Rewrite the README's wisdom and calendar sections, commit, move this week's tag
     (ufo-YYYY-MM-DD) to the new commit, and push.
Nothing changes -> nothing is committed. Safe to re-run.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import make_svgs

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state.json"
README = ROOT / "README.md"
HERO = ROOT / "assets" / "ufo-hero.svg"
REPO = "pauldawson-blacklane/pauldawson-blacklane"
CLAUDE = os.environ.get("UFO_CLAUDE", str(Path.home() / ".local/bin/claude"))
GH = os.environ.get("UFO_GH", "/opt/homebrew/bin/gh")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MAX_SVG_BYTES = 120_000


def log(msg):
    print(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def tag_for(monday):
    return f"ufo-{monday.isoformat()}"


# ---------------------------------------------------------------- state

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"weeks": {}}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- Claude CLI

def ask_claude(prompt, timeout):
    """Headless Claude call with every tool disabled; returns stdout text."""
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    with tempfile.TemporaryDirectory() as tmp:  # neutral cwd: no project CLAUDE.md or settings
        r = subprocess.run(
            [CLAUDE, "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--output-format", "text"],
            input=prompt, capture_output=True, text=True, timeout=timeout, cwd=tmp, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"claude exited {r.returncode}: {r.stderr.strip()[:300]}")
    return r.stdout


BANNER_PROMPT = """You are designing this week's animated banner for a GitHub profile README.
Output ONLY one standalone SVG document: start with <svg and end with </svg>. No markdown fences, no commentary.

Hard requirements:
- Root element exactly: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 420" width="100%" role="img" aria-label="(short description of the scene)">
- First child: a comment <!-- concept: (one sentence describing the scene) -->
- The star is a UFO / flying saucer beaming something up with a tractor beam. Space and UFO theme, playful,
  with a nod to platform security, DevSecOps or cloud (padlocks, keys, shields, servers, secrets, tokens, bugs,
  containers, clouds, rubber ducks, cows...). The idea, palette, landscape and cargo are your choice.
- Text, exactly as written: "PAUL DAWSON" (bold monospace, ~64px, letter-spacing ~4px, light fill, left side,
  x=64, baseline y=150) and below it "BLACKLANE PLATFORM SECURITY" (~22px monospace, accent colour, baseline y=196).
  Optionally a third terminal-style line under that starting with "> " (max 44 characters, a space/security pun).
  Keep all text inside x 40..620 and keep the artwork clear of it.
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace
- Animate with CSS @keyframes inside a <style> element and/or SMIL <animate>/<animateTransform>; loops forever, smoothly.
  Include: @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
- The backdrop (sky and ground) must fade to fully transparent at all four edges, using <mask> elements filled with
  linear gradients (about 12% at left/right, 20% at top/bottom), so the banner blends into the GitHub page with no
  visible rectangle. Use a dark night palette; the UFO and text sit on top unmasked.
- Self-contained and safe: NO <script>, <foreignObject>, <image>, <iframe>, <a>; no external URLs, fonts or @import;
  no on* event attributes; href only to internal "#id" references. Under 60 KB.
- Make it look polished: gradients, glows (feGaussianBlur), depth, twinkling stars, subtle motion.

Make this week feel clearly different from recent weeks. Recent concepts (do not repeat): {recent}
This banner is for the week of {week}."""

WISDOM_PROMPT = """Write one short technical "word of wisdom" for a platform security engineer's GitHub profile, for {day_name} {date}.
Topics: cloud and platform security, AWS, Kubernetes, CI/CD and supply-chain security, GitHub, secrets, IAM,
infrastructure as code, observability, incident response, or general engineering craft. Practical, punchy,
optionally witty; it can be an original aphorism or a concrete tip.
Rules: ONE line, max 160 characters, plain text (inline `code` allowed), no quotation marks around it, no hashtags,
no @-mentions, no URLs, no emoji, no attribution. Output only the line itself.
Do not repeat or closely paraphrase any of these earlier ones:
{history}"""


FORBIDDEN_TAGS = {"script", "foreignobject", "image", "iframe", "a", "use", "object", "embed", "audio", "video", "canvas"}


def validate_svg(raw):
    """Extract and safety-check an SVG from Claude's output; returns (svg_text, concept)."""
    start, end = raw.find("<svg"), raw.rfind("</svg>")
    if start < 0 or end < 0:
        raise ValueError("no <svg>...</svg> in output")
    svg = raw[start:end + len("</svg>")].strip() + "\n"
    if len(svg.encode()) > MAX_SVG_BYTES:
        raise ValueError(f"too large ({len(svg.encode())} bytes)")
    root = ET.fromstring(svg)  # raises on malformed XML
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError(f"root is {root.tag}")
    if (root.get("viewBox") or "").split() != ["0", "0", "1200", "420"]:
        raise ValueError(f"viewBox is {root.get('viewBox')!r}")
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if tag in FORBIDDEN_TAGS:
            raise ValueError(f"forbidden element <{tag}>")
        for k, v in el.attrib.items():
            name = k.split("}")[-1].lower()
            if name.startswith("on"):
                raise ValueError(f"event attribute {name}")
            if name == "href" and not v.startswith("#"):
                raise ValueError(f"external href {v[:60]}")
    low = svg.lower()
    for bad in ("javascript:", "@import", "http://", "https://", "data:"):
        # the SVG namespace URI is the only allowed URL
        if bad in low.replace("http://www.w3.org/2000/svg", "").replace("http://www.w3.org/1999/xlink", ""):
            raise ValueError(f"forbidden content {bad!r}")
    text = " ".join(t for t in root.itertext())
    for must in ("PAUL DAWSON", "BLACKLANE PLATFORM SECURITY"):
        if must not in text:
            raise ValueError(f"missing text {must!r}")
    if "<mask" not in svg:
        raise ValueError("no edge-fade <mask>")
    m = re.search(r"<!--\s*concept:\s*(.*?)\s*-->", svg, re.S)
    concept = re.sub(r"\s+", " ", m.group(1)).strip()[:200] if m else "Claude-designed scene"
    return svg, concept


def clean_wisdom(raw):
    line = raw.strip().splitlines()[0].strip() if raw.strip() else ""
    line = line.strip('"“”\'').strip()
    if not 15 <= len(line) <= 200:
        raise ValueError(f"bad length {len(line)}")
    if re.search(r"https?://|[<>@#|]", line):
        raise ValueError("contains a URL, HTML, @-mention, # or |")
    return line


# ---------------------------------------------------------------- generation

def make_banner(monday, state, use_claude):
    if monday <= make_svgs.LAUNCH:
        return make_svgs.write(monday).replace("built-in generator", "original launch design")
    if use_claude:
        recent = [w.get("banner", "") for _, w in sorted(state["weeks"].items())[-8:]] or ["(none yet)"]
        prompt = BANNER_PROMPT.format(recent="; ".join(recent), week=monday.isoformat())
        for attempt in (1, 2):
            try:
                log(f"asking Claude for the {monday} banner (attempt {attempt})")
                svg, concept = validate_svg(ask_claude(prompt, timeout=900))
                HERO.write_text(svg)
                (ROOT / "assets" / "ufo-divider.svg").write_text(make_svgs.divider())
                return f"Claude: {concept}"
            except Exception as e:  # noqa: BLE001 - any failure -> retry, then fall back
                log(f"Claude banner rejected: {e}")
    desc = make_svgs.write(monday)
    log(f"used fallback: {desc}")
    return desc


def make_wisdom(day, date, state, use_claude):
    if not use_claude:
        return None
    history = [w for _, wk in sorted(state["weeks"].items()) for w in wk.get("wisdom", {}).values()][-60:]
    prompt = WISDOM_PROMPT.format(day_name=DAY_NAMES[day], date=date.isoformat(), history="\n".join(f"- {h}" for h in history) or "(none yet)")
    for attempt in (1, 2):
        try:
            log(f"asking Claude for {DAYS[day]} {date} wisdom (attempt {attempt})")
            return clean_wisdom(ask_claude(prompt, timeout=300))
        except Exception as e:  # noqa: BLE001
            log(f"wisdom rejected: {e}")
    return None


# ---------------------------------------------------------------- README sections

def fmt_date(d):
    return f"{d.day} {d:%b %Y}"


def wisdom_md(monday, week):
    entries = week.get("wisdom", {})
    lines = [f"### 🧠 Words of wisdom · week of {fmt_date(monday)}", ""]
    if not entries:
        lines.append("_Incoming transmission…_")
    for k, day in enumerate(DAYS):
        if day in entries:
            lines.append(f"- **{DAY_NAMES[k]}:** {entries[day]}")
    return "\n".join(lines)


def calendar_md(state, current):
    mondays = sorted(dt.date.fromisoformat(k) for k in state["weeks"])
    by_month = {}
    for m in mondays:
        by_month.setdefault((m.year, m.month), []).append(m)
    rows = []
    for (y, mo), ms in sorted(by_month.items(), reverse=True):
        cells = []
        for m in ms:
            url = f"https://github.com/{REPO}/blob/{tag_for(m)}/README.md"
            label = f"🛸 <b>{m.day}</b>" if m == current else str(m.day)
            cells.append(f'<td align="center"><a href="{url}">{label}</a></td>')
        cells += ['<td></td>'] * (5 - len(cells))
        rows.append(f'<tr><td><b>{dt.date(y, mo, 1):%b %Y}</b></td>{"".join(cells)}</tr>')
    head = '<tr><th>Month</th><th colspan="5">Mondays · click a date to see that week\'s UFO and words of wisdom</th></tr>'
    recent, older = rows[:6], rows[6:]
    out = ["### 📅 UFO sightings", "", "<table>", head, *recent, "</table>"]
    if older:
        out += ["", "<details><summary>Older sightings</summary>", "", "<table>", head, *older, "</table>", "", "</details>"]
    return "\n".join(out)


def replace_section(text, name, body):
    pat = re.compile(rf"(<!-- {name}:start -->).*?(<!-- {name}:end -->)", re.S)
    if not pat.search(text):
        raise RuntimeError(f"README is missing the <!-- {name}:start --> / <!-- {name}:end --> markers")
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), text)


# ---------------------------------------------------------------- git

def git(*args, check=True):
    cred = ["-c", "credential.helper=", "-c", f"credential.helper=!{GH} auth git-credential"]
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    r = subprocess.run(["git", *cred, *args], cwd=ROOT, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()[:400]}")
    return r


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-claude", action="store_true")
    a = ap.parse_args()
    use_claude = not a.no_claude
    today = a.today
    monday = make_svgs.monday_of(today)
    last_day = min(today.weekday(), 4)
    log(f"run for {today} (week {monday}); dry_run={a.dry_run} claude={use_claude}")

    if not a.dry_run:
        git("pull", "--rebase", "--autostash", "--quiet", "origin", "main")

    state = load_state()
    week = state["weeks"].setdefault(monday.isoformat(), {"wisdom": {}})
    changed = False

    if not week.get("banner"):
        week["banner"] = make_banner(monday, state, use_claude)
        log(f"banner: {week['banner']}")
        changed = True

    for k in range(last_day + 1):
        if DAYS[k] not in week["wisdom"]:
            w = make_wisdom(k, monday + dt.timedelta(days=k), state, use_claude)
            if w:
                week["wisdom"][DAYS[k]] = w
                log(f"{DAYS[k]}: {w}")
                changed = True

    if not changed:
        log("nothing new for this week")
        return 0

    save_state(state)
    text = README.read_text()
    text = replace_section(text, "wisdom", wisdom_md(monday, week))
    text = replace_section(text, "calendar", calendar_md(state, monday))
    README.write_text(text)

    if a.dry_run:
        log("dry run: files updated, no commit")
        return 0

    git("add", "README.md", "state.json", "assets")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        log("no file changes to commit")
        return 0
    days_done = ", ".join(d for d in DAYS if d in week["wisdom"])
    git("commit", "-q", "-m", f"UFO sighting: week of {monday} ({days_done or 'banner'})")
    tag = tag_for(monday)
    git("tag", "-f", tag)
    git("push", "-q", "origin", "main")
    git("push", "-q", "-f", "origin", f"refs/tags/{tag}")
    log(f"pushed main and {tag}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 - log for launchd, non-zero exit
        log(f"FAILED: {e}")
        sys.exit(1)

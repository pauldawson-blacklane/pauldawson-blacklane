"""Built-in animated UFO banner generator (pure SVG + CSS/SMIL, no JS).

weekly.py asks Claude CLI to design each Monday's banner; this module is the fallback when
Claude is unavailable or returns an invalid SVG, and it renders the launch week's original
design. Each Monday gets its own scene derived from the date (palette, planet, terrain,
cargo, terminal line). Same date in -> identical SVG out.

    python3 make_svgs.py                 # this week's Monday
    python3 make_svgs.py 2026-11-16      # a specific Monday
"""
import datetime as dt
import random
import sys
from html import escape
from pathlib import Path

OUT = Path(__file__).parent / "assets"
LAUNCH = dt.date(2026, 11, 9)
W, H = 1200, 420
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
CHAR_W = 10.85  # approx advance of an 18px monospace glyph

# name, sky (top, mid, bottom), nebula 1, nebula 2, accent, planet, ring, rim lights
PALETTES = [
    ("deep space", ("#05010f", "#120a2e", "#1d0f3f"), "#7b2cff", "#00e5ff", "#7dffb2", "#ff7ad9", "#ffd1f3", ("#ffe45e", "#ff4fd8", "#4fd8ff")),
    ("crimson nebula", ("#0a0205", "#2a0a14", "#3d0f1f"), "#ff3d6e", "#ffb347", "#ffd166", "#4fd8ff", "#c9f4ff", ("#ffd166", "#ff3d6e", "#ffffff")),
    ("deep ocean", ("#010812", "#06223a", "#0b3352"), "#00b4d8", "#7b2cff", "#90f1ff", "#ffb347", "#ffe2b8", ("#90f1ff", "#ffb347", "#c77dff")),
    ("emerald aurora", ("#020b08", "#06261c", "#0b3a2a"), "#2bff88", "#00e5ff", "#b9ff66", "#c77dff", "#ead6ff", ("#b9ff66", "#00e5ff", "#ff7ad9")),
    ("synthwave sunset", ("#0b0414", "#3a0f3d", "#6b1e4a"), "#ff7a3d", "#ff3dc8", "#ffe45e", "#5ef2d6", "#c9fff4", ("#ffe45e", "#ff3dc8", "#5ef2d6")),
    ("ice moon", ("#03060f", "#101c3a", "#1c2c55"), "#a0c4ff", "#e0aaff", "#caf0f8", "#ff8fab", "#ffd6e0", ("#caf0f8", "#e0aaff", "#ff8fab")),
    ("toxic swamp", ("#050705", "#141f0a", "#22330f"), "#a3ff12", "#00ffd5", "#d4ff3d", "#ff5ef2", "#ffd1fb", ("#d4ff3d", "#00ffd5", "#ff5ef2")),
]
CARGO = ["code", "cow", "duck", "padlock", "server", "key", "shield"]
TERRAIN = ["classic", "mountains", "craters", "dunes", "crystals"]
LINES = [
    "> scanning for intelligent life in CI/CD...",
    "> beaming up unpinned GitHub Actions...",
    "> abducting stale access tokens...",
    "> rotating secrets across the galaxy...",
    "> probing for public S3 buckets...",
    "> enforcing rulesets on planet Earth...",
    "> reviewing Wiz findings from orbit...",
    "> no public repos detected. probably.",
    "> checking CODEOWNERS on Mars...",
    "> force-push attempt intercepted...",
]


def monday_of(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def week_index(monday: dt.date) -> int:
    return (monday - LAUNCH).days // 7


def mix(a: str, b: str, t: float) -> str:
    ca, cb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def theme_for(monday: dt.date) -> dict:
    i = week_index(monday)
    rng = random.Random(monday.isoformat())
    if i <= 0:  # launch week: the original design
        return {"rng": rng, "palette": PALETTES[0], "cargo": "code", "terrain": "classic", "line": LINES[0], "ring": True, "moons": 0, "planet_x": 1085}
    return {
        "rng": rng,
        "palette": PALETTES[i % len(PALETTES)],
        "cargo": CARGO[(i * 3) % len(CARGO)],
        "terrain": TERRAIN[(i * 2) % len(TERRAIN)],
        "line": LINES[(i * 7) % len(LINES)],
        "ring": rng.random() < 0.6,
        "moons": rng.choice([0, 1, 2]),
        "planet_x": rng.choice([1085, 1060, 640, 560]),
    }


# ---------------------------------------------------------------- pieces

def stars(rng, n, w, h, max_y=None):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, max_y or h)
        r = rng.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        d, dl = rng.uniform(2, 5), rng.uniform(0, 5)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="tw" style="animation-duration:{d:.1f}s;animation-delay:-{dl:.1f}s"/>')
    return "\n    ".join(out)


def typing(attr, n):
    """Discrete SMIL animation: one character per step, hold, then restart."""
    vals = [f"{k * CHAR_W:.1f}" for k in range(n + 1)] + [f"{n * CHAR_W:.1f}"]
    kt = [f"{0.6 * k / n:.4f}" for k in range(n + 1)] + ["1"]
    return f'<animate attributeName="{attr}" dur="6s" repeatCount="indefinite" calcMode="discrete" values="{";".join(vals)}" keyTimes="{";".join(kt)}"/>'


def cargo_svg(kind, accent, dark):
    """A ~34px object centred on (0,0)."""
    if kind == "code":
        return f'<rect x="-16" y="-16" width="32" height="32" rx="7" fill="{accent}"/><text y="6" text-anchor="middle" font-family="{MONO}" font-size="15" font-weight="800" fill="{dark}">&lt;/&gt;</text>'
    if kind == "cow":
        return ('<g transform="scale(.9)"><ellipse rx="20" ry="12" fill="#f5f5f5"/><ellipse cx="-6" cy="-3" rx="6" ry="4" fill="#222"/><ellipse cx="9" cy="4" rx="5" ry="3.5" fill="#222"/>'
                '<rect x="-15" y="9" width="4" height="9" rx="1.5" fill="#f5f5f5"/><rect x="-6" y="9" width="4" height="9" rx="1.5" fill="#f5f5f5"/><rect x="5" y="9" width="4" height="9" rx="1.5" fill="#f5f5f5"/><rect x="13" y="9" width="4" height="9" rx="1.5" fill="#f5f5f5"/>'
                '<ellipse cx="22" cy="-8" rx="8" ry="7" fill="#f5f5f5"/><ellipse cx="26" cy="-5" rx="4" ry="3" fill="#ffb3c7"/><circle cx="20" cy="-10" r="1.4" fill="#222"/><path d="M17 -14 l-3 -4 M24 -14 l2 -4" stroke="#ddd" stroke-width="2" stroke-linecap="round"/></g>')
    if kind == "duck":
        return ('<ellipse cy="5" rx="17" ry="11" fill="#ffd93b"/><circle cx="8" cy="-8" r="9" fill="#ffd93b"/><path d="M15 -8 l9 2 l-9 3 z" fill="#ff8c1a"/>'
                '<circle cx="10" cy="-10" r="1.6" fill="#222"/><path d="M-6 2 q6 8 14 0" stroke="#e6b800" stroke-width="2" fill="none"/>')
    if kind == "padlock":
        return (f'<path d="M-9 -2 v-8 a9 9 0 0 1 18 0 v8" stroke="#d9dde8" stroke-width="5" fill="none"/><rect x="-15" y="-3" width="30" height="22" rx="5" fill="{accent}"/>'
                f'<circle cy="6" r="3.5" fill="{dark}"/><rect x="-1.5" y="7" width="3" height="7" rx="1" fill="{dark}"/>')
    if kind == "server":
        return ('<rect x="-14" y="-18" width="28" height="36" rx="4" fill="#3a3f55" stroke="#8a90a8" stroke-width="2"/>'
                + "".join(f'<rect x="-9" y="{y}" width="18" height="7" rx="1.5" fill="#1b1e2b"/><circle cx="5" cy="{y + 3.5}" r="1.8" fill="{accent}" class="led" style="animation-delay:{k * .3:.1f}s"/>' for k, y in enumerate((-13, -3, 7))))
    if kind == "key":
        return (f'<circle cx="-10" r="9" fill="none" stroke="{accent}" stroke-width="5"/><rect x="-2" y="-2.5" width="24" height="5" rx="2" fill="{accent}"/>'
                f'<rect x="14" y="1" width="4" height="8" rx="1" fill="{accent}"/><rect x="8" y="1" width="4" height="6" rx="1" fill="{accent}"/>')
    if kind == "shield":
        return (f'<path d="M0 -18 l15 6 v8 c0 10 -7 17 -15 21 c-8 -4 -15 -11 -15 -21 v-8 z" fill="{accent}"/>'
                f'<path d="M-7 0 l5 5 l9 -10" stroke="{dark}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    raise ValueError(kind)


def terrain_svg(kind, rng, ground_bot, accent):
    if kind == "classic":
        return (f'<path d="M0 360 C120 330 220 372 340 350 S560 318 700 352 S940 380 1060 346 S1180 340 1200 352 V420 H0 Z" fill="url(#ground)"/>'
                f'<path d="M0 382 C160 370 300 396 470 380 S780 392 940 384 S1140 376 1200 386 V420 H0 Z" fill="{ground_bot}"/>'
                f'<g fill="{ground_bot}"><path d="M120 362 l6 -26 l6 26 z"/><path d="M560 346 l5 -20 l5 20 z"/><path d="M1130 350 l6 -24 l6 24 z"/></g>')

    def ridge(base, amp, step, smooth):
        pts = []
        for x in range(0, W + step, step):
            y = base + rng.uniform(-amp, amp)
            if 780 <= x <= 940:
                y = base + 6  # keep the beam's landing spot flat
            pts.append((x, y))
        if not smooth:
            return "M" + " L".join(f"{x} {y:.0f}" for x, y in pts) + f" V{H} H0 Z"
        d = f"M{pts[0][0]} {pts[0][1]:.0f}"
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d += f" Q{x0} {y0:.0f} {(x0 + x1) / 2:.0f} {(y0 + y1) / 2:.0f}"
        return d + f" T{pts[-1][0]} {pts[-1][1]:.0f} V{H} H0 Z"

    if kind == "mountains":
        return f'<path d="{ridge(330, 34, 60, False)}" fill="url(#ground)"/><path d="{ridge(372, 10, 90, True)}" fill="{ground_bot}"/>'
    if kind == "dunes":
        return f'<path d="{ridge(352, 18, 200, True)}" fill="url(#ground)"/><path d="{ridge(380, 10, 160, True)}" fill="{ground_bot}"/>'
    if kind == "craters":
        craters = "".join(
            f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.0f}" ry="{rx / 4:.0f}" fill="{ground_bot}" opacity=".7"/>'
            for x, y, rx in ((rng.choice([rng.uniform(60, 700), rng.uniform(1000, 1150)]), rng.uniform(374, 396), rng.uniform(18, 44)) for _ in range(6)))
        return f'<path d="{ridge(356, 12, 150, True)}" fill="url(#ground)"/>{craters}<path d="{ridge(392, 6, 200, True)}" fill="{ground_bot}"/>'
    if kind == "crystals":
        xs = [rng.uniform(40, 720) for _ in range(5)] + [rng.uniform(990, 1160) for _ in range(3)]
        cr = "".join(
            f'<path d="M{x:.0f} 372 l{w:.0f} -{h:.0f} l{w:.0f} {h:.0f} z" fill="{accent}" opacity=".55" class="glowpulse" style="animation-delay:-{rng.uniform(0, 3):.1f}s"/>'
            for x, w, h in ((x, rng.uniform(5, 9), rng.uniform(18, 42)) for x in xs))
        return f'<path d="{ridge(360, 14, 120, True)}" fill="url(#ground)"/>{cr}<path d="{ridge(386, 6, 180, True)}" fill="{ground_bot}"/>'
    raise ValueError(kind)


# ---------------------------------------------------------------- scenes

def hero(monday: dt.date) -> str:
    t = theme_for(monday)
    rng = t["rng"]
    name, (s0, s1, s2), n1, n2, accent, planet, ring, lights_c = t["palette"]
    dark = mix(s0, "#000000", .3)
    ground_top, ground_bot = mix(s2, "#ffffff", .1), mix(s0, "#000000", .2)
    line_txt = t["line"]
    n = len(line_txt)
    lights = "\n      ".join(f'<circle cx="{x}" cy="2" r="5" class="lt" style="animation-delay:{k * 0.18:.2f}s"/>' for k, x in enumerate(range(-96, 97, 32)))
    particles = "\n      ".join(
        f'<circle cx="{rng.uniform(-40, 40):.0f}" cy="0" r="{rng.choice([1.5, 2, 2.5])}" class="pt" style="animation-delay:-{rng.uniform(0, 3):.2f}s;animation-duration:{rng.uniform(2.2, 3.6):.1f}s"/>'
        for _ in range(18))
    px = t["planet_x"]
    py = 70 if px > 900 else 60
    planet_svg = f'<circle r="26" fill="{planet}" opacity=".85"/>'
    if t["ring"]:
        planet_svg += f'<ellipse rx="46" ry="9" fill="none" stroke="{ring}" stroke-width="3" opacity=".7" transform="rotate(-18)"/>'
    for k in range(t["moons"]):
        planet_svg += f'<g class="orbit" style="animation-duration:{9 + k * 5}s"><circle cx="{44 + k * 16}" r="{4 - k}" fill="{ring}"/></g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Animated UFO beaming up a {t["cargo"]} above a planet, week of {monday.isoformat()}">
  <!-- week of {monday.isoformat()} · built-in generator · palette: {name} · cargo: {t["cargo"]} · terrain: {t["terrain"]} -->
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{s0}"/><stop offset=".6" stop-color="{s1}"/><stop offset="1" stop-color="{s2}"/>
    </linearGradient>
    <radialGradient id="neb1" cx=".22" cy=".35" r=".45"><stop offset="0" stop-color="{n1}" stop-opacity=".35"/><stop offset="1" stop-color="{n1}" stop-opacity="0"/></radialGradient>
    <radialGradient id="neb2" cx=".85" cy=".2" r=".35"><stop offset="0" stop-color="{n2}" stop-opacity=".22"/><stop offset="1" stop-color="{n2}" stop-opacity="0"/></radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{accent}" stop-opacity=".85"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="dome" cx=".4" cy=".3" r=".8"><stop offset="0" stop-color="#e6fffa"/><stop offset=".45" stop-color="{mix(accent, '#5ef2d6', .5)}" stop-opacity=".8"/><stop offset="1" stop-color="{mix(accent, '#0b2b3a', .7)}" stop-opacity=".9"/></radialGradient>
    <linearGradient id="hull" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9dde8"/><stop offset=".5" stop-color="#8a90a8"/><stop offset="1" stop-color="#3a3f55"/></linearGradient>
    <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ground_top}"/><stop offset="1" stop-color="{ground_bot}"/></linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <!-- soft edges: backdrop fades to transparent so it blends into GitHub's page colour (dark or light) -->
    <linearGradient id="fxg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".12" stop-color="#fff"/><stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <linearGradient id="fyg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000"/><stop offset=".2" stop-color="#fff"/><stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <mask id="fx" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fxg)"/></mask>
    <mask id="fy" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fyg)"/></mask>
  </defs>
  <style>
    .tw {{ fill:#fff; animation: tw ease-in-out infinite alternate; }}
    @keyframes tw {{ from {{ opacity:.15 }} to {{ opacity:1 }} }}
    .ufo {{ animation: bob 4s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform: translate(860px,118px) rotate(-3deg) }} 50% {{ transform: translate(860px,132px) rotate(3deg) }} }}
    .lt {{ fill:{lights_c[0]}; animation: blink 1.26s steps(1) infinite; }}
    @keyframes blink {{ 0% {{ fill:{lights_c[0]} }} 33% {{ fill:{lights_c[1]} }} 66% {{ fill:{lights_c[2]} }} }}
    .beam {{ animation: pulse 2.4s ease-in-out infinite; transform-origin: 860px 150px; }}
    @keyframes pulse {{ 0%,100% {{ opacity:.55; transform: scaleX(.92) }} 50% {{ opacity:.95; transform: scaleX(1.05) }} }}
    .pt {{ fill:{mix(accent, '#ffffff', .6)}; animation: rise linear infinite; }}
    @keyframes rise {{ from {{ transform: translateY(210px); opacity:0 }} 15% {{ opacity:1 }} to {{ transform: translateY(0); opacity:0 }} }}
    .cargo {{ animation: lift 6s ease-in-out infinite; }}
    @keyframes lift {{ 0%,10% {{ transform: translate(860px,352px) rotate(0) }} 55% {{ transform: translate(860px,215px) rotate(200deg) }} 60%,100% {{ transform: translate(860px,190px) rotate(360deg) scale(0); }} }}
    .shoot {{ animation: shoot 7s linear infinite; }}
    @keyframes shoot {{ 0%,86% {{ transform: translate(0,0); opacity:0 }} 88% {{ opacity:1 }} 100% {{ transform: translate(-520px,260px); opacity:0 }} }}
    .orbit {{ animation: orbit linear infinite; }}
    @keyframes orbit {{ to {{ transform: rotate(360deg) }} }}
    .led {{ animation: cur 0.9s steps(1) infinite; }}
    .glowpulse {{ animation: gp 3s ease-in-out infinite alternate; }}
    @keyframes gp {{ from {{ opacity:.3 }} to {{ opacity:.8 }} }}
    .title {{ font: 800 64px {MONO}; fill:#f4f0ff; letter-spacing:4px; }}
    .sub {{ font: 600 22px {MONO}; fill:{accent}; letter-spacing:3px; }}
    .term {{ font: 500 18px {MONO}; fill:{mix(accent, '#b9a8ff', .6)}; }}
    .cursor {{ fill:{accent}; animation: cur 1s steps(1) infinite; }}
    @keyframes cur {{ 50% {{ opacity:0 }} }}
    .glitch {{ animation: glitch 6s infinite; }}
    @keyframes glitch {{ 0%,92%,100% {{ transform:none }} 93% {{ transform: translate(3px,-1px) skewX(8deg) }} 95% {{ transform: translate(-3px,1px) }} 97% {{ transform: none }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>

  <g mask="url(#fy)"><g mask="url(#fx)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <rect width="{W}" height="{H}" fill="url(#neb1)"/>
  <rect width="{W}" height="{H}" fill="url(#neb2)"/>
  <g>
    {stars(rng, 140, W, H, 330)}
  </g>
  </g></g>
  <g class="shoot"><line x1="1150" y1="20" x2="1215" y2="-12" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".9"/></g>

  <!-- planet -->
  <g transform="translate({px},{py})">{planet_svg}</g>

  <!-- tractor beam -->
  <polygon class="beam" points="828,150 892,150 960,372 760,372" fill="url(#beam)"/>
  <g transform="translate(860,160)">
      {particles}
  </g>

  <!-- abducted cargo -->
  <g class="cargo"><g filter="url(#glow)">{cargo_svg(t["cargo"], accent, dark)}</g></g>

  <!-- UFO -->
  <g class="ufo">
    <ellipse cx="0" cy="-22" rx="46" ry="38" fill="url(#dome)"/>
    <path d="M-18 -40 q10 -14 26 -10" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none" opacity=".8"/>
    <ellipse cx="0" cy="2" rx="118" ry="26" fill="url(#hull)"/>
    <ellipse cx="0" cy="-4" rx="118" ry="12" fill="#eef1f7" opacity=".35"/>
    <ellipse cx="0" cy="22" rx="42" ry="8" fill="{accent}" filter="url(#glow)"/>
    <g filter="url(#glow)">
      {lights}
    </g>
  </g>

  <!-- planet surface -->
  <g mask="url(#fy)"><g mask="url(#fx)">
  {terrain_svg(t["terrain"], rng, ground_bot, accent)}
  </g></g>
  <ellipse cx="860" cy="372" rx="100" ry="10" fill="{accent}" opacity=".25" class="beam"/>

  <!-- text -->
  <g transform="translate(64,150)">
    <g class="glitch"><text class="title">PAUL DAWSON</text></g>
    <text y="46" class="sub">BLACKLANE PLATFORM SECURITY</text>
    <clipPath id="typeclip"><rect x="0" y="80" height="30" width="0">{typing("width", n)}</rect></clipPath>
    <text y="100" class="term" clip-path="url(#typeclip)">{escape(line_txt)}</text>
    <rect x="0" y="104" width="11" height="3" class="cursor">{typing("x", n)}</rect>
  </g>
</svg>
'''


def divider() -> str:
    rng = random.Random("divider")
    w, h = 1200, 60
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Divider">
  <style>
    .tw {{ fill:#b9a8ff; animation: tw ease-in-out infinite alternate; }}
    @keyframes tw {{ from {{ opacity:.1 }} to {{ opacity:.9 }} }}
    .mini {{ animation: fly 9s linear infinite; }}
    @keyframes fly {{ from {{ transform: translate(-60px,30px) }} to {{ transform: translate(1260px,30px) }} }}
    .lt {{ fill:#7dffb2; animation: b 0.8s steps(1) infinite; }} @keyframes b {{ 50% {{ fill:#ff4fd8 }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <line x1="0" y1="30" x2="{w}" y2="30" stroke="#7b2cff" stroke-opacity=".35" stroke-dasharray="2 8"/>
  {stars(rng, 40, w, h)}
  <g class="mini">
    <ellipse cy="-6" rx="10" ry="8" fill="#5ef2d6" opacity=".85"/>
    <ellipse rx="26" ry="6" fill="#a5abc0"/>
    <circle cx="-14" r="2" class="lt"/><circle r="2" class="lt" style="animation-delay:.27s"/><circle cx="14" r="2" class="lt" style="animation-delay:.54s"/>
  </g>
</svg>
'''


def write(monday: dt.date) -> str:
    """Write the built-in banner for this Monday; returns a one-line description."""
    OUT.mkdir(exist_ok=True)
    (OUT / "ufo-hero.svg").write_text(hero(monday))
    (OUT / "ufo-divider.svg").write_text(divider())
    t = theme_for(monday)
    return f"built-in generator: {t['palette'][0]}, {t['cargo']}, {t['terrain']}"


if __name__ == "__main__":
    d = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    print(monday_of(d).isoformat(), write(monday_of(d)))

"""Generates the animated SVGs for the GitHub profile README (pure SVG + CSS, no JS)."""
import random
from pathlib import Path

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)
random.seed(42)
W, H = 1200, 420
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def stars(n, w, h, max_y=None):
    out = []
    for _ in range(n):
        x, y = random.uniform(0, w), random.uniform(0, max_y or h)
        r = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        d, dl = random.uniform(2, 5), random.uniform(0, 5)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="tw" style="animation-duration:{d:.1f}s;animation-delay:-{dl:.1f}s"/>')
    return "\n    ".join(out)


LINE = "&gt; scanning for intelligent life in CI/CD..."
LINE_LEN = 44   # visible characters
CHAR_W = 10.85  # approx advance of an 18px monospace glyph


def typing(attr):
    """Discrete SMIL animation: one character per step, hold, then restart."""
    steps = LINE_LEN + 1
    vals = [f"{i * CHAR_W:.1f}" for i in range(steps)] + [f"{LINE_LEN * CHAR_W:.1f}"]
    kt = [f"{0.6 * i / LINE_LEN:.4f}" for i in range(steps)] + ["1"]
    return f'<animate attributeName="{attr}" dur="6s" repeatCount="indefinite" calcMode="discrete" values="{";".join(vals)}" keyTimes="{";".join(kt)}"/>'


def hero():
    lights = "\n      ".join(
        f'<circle cx="{x}" cy="2" r="5" class="lt" style="animation-delay:{i*0.18:.2f}s"/>'
        for i, x in enumerate(range(-96, 97, 32))
    )
    particles = "\n      ".join(
        f'<circle cx="{random.uniform(-40, 40):.0f}" cy="0" r="{random.choice([1.5, 2, 2.5])}" class="pt" style="animation-delay:-{random.uniform(0, 3):.2f}s;animation-duration:{random.uniform(2.2, 3.6):.1f}s"/>'
        for _ in range(18)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Animated UFO beaming up code above a planet surface">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#05010f"/><stop offset=".6" stop-color="#120a2e"/><stop offset="1" stop-color="#1d0f3f"/>
    </linearGradient>
    <radialGradient id="neb1" cx=".22" cy=".35" r=".45"><stop offset="0" stop-color="#7b2cff" stop-opacity=".35"/><stop offset="1" stop-color="#7b2cff" stop-opacity="0"/></radialGradient>
    <radialGradient id="neb2" cx=".85" cy=".2" r=".35"><stop offset="0" stop-color="#00e5ff" stop-opacity=".22"/><stop offset="1" stop-color="#00e5ff" stop-opacity="0"/></radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7dffb2" stop-opacity=".85"/><stop offset="1" stop-color="#7dffb2" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="dome" cx=".4" cy=".3" r=".8"><stop offset="0" stop-color="#e6fffa"/><stop offset=".45" stop-color="#5ef2d6" stop-opacity=".8"/><stop offset="1" stop-color="#0b6b7a" stop-opacity=".9"/></radialGradient>
    <linearGradient id="hull" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9dde8"/><stop offset=".5" stop-color="#8a90a8"/><stop offset="1" stop-color="#3a3f55"/></linearGradient>
    <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1458"/><stop offset="1" stop-color="#0a0418"/></linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <style>
    .tw {{ fill:#fff; animation: tw ease-in-out infinite alternate; }}
    @keyframes tw {{ from {{ opacity:.15 }} to {{ opacity:1 }} }}
    .ufo {{ animation: bob 4s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform: translate(860px,118px) rotate(-3deg) }} 50% {{ transform: translate(860px,132px) rotate(3deg) }} }}
    .lt {{ fill:#ffe45e; animation: blink 1.26s steps(1) infinite; }}
    @keyframes blink {{ 0% {{ fill:#ffe45e }} 33% {{ fill:#ff4fd8 }} 66% {{ fill:#4fd8ff }} }}
    .beam {{ animation: pulse 2.4s ease-in-out infinite; transform-origin: 860px 150px; }}
    @keyframes pulse {{ 0%,100% {{ opacity:.55; transform: scaleX(.92) }} 50% {{ opacity:.95; transform: scaleX(1.05) }} }}
    .pt {{ fill:#c9ffe0; animation: rise linear infinite; }}
    @keyframes rise {{ from {{ transform: translateY(210px); opacity:0 }} 15% {{ opacity:1 }} to {{ transform: translateY(0); opacity:0 }} }}
    .cargo {{ animation: lift 6s ease-in-out infinite; }}
    @keyframes lift {{ 0%,10% {{ transform: translate(860px,352px) rotate(0) }} 55% {{ transform: translate(860px,215px) rotate(200deg) }} 60%,100% {{ transform: translate(860px,190px) rotate(360deg) scale(0); }} }}
    .shoot {{ animation: shoot 7s linear infinite; }}
    @keyframes shoot {{ 0%,86% {{ transform: translate(0,0); opacity:0 }} 88% {{ opacity:1 }} 100% {{ transform: translate(-520px,260px); opacity:0 }} }}
    .title {{ font: 800 64px {MONO}; fill:#f4f0ff; letter-spacing:4px; }}
    .sub {{ font: 600 22px {MONO}; fill:#7dffb2; letter-spacing:3px; }}
    .term {{ font: 500 18px {MONO}; fill:#b9a8ff; }}
    .type {{ animation: type 5s steps(44) infinite; }}
    @keyframes type {{ 0% {{ width:0 }} 60%,90% {{ width:520px }} 100% {{ width:520px }} }}
    .cursor {{ fill:#7dffb2; animation: cur 1s steps(1) infinite; }}
    @keyframes cur {{ 50% {{ opacity:0 }} }}
    .glitch {{ animation: glitch 6s infinite; }}
    @keyframes glitch {{ 0%,92%,100% {{ transform:none }} 93% {{ transform: translate(3px,-1px) skewX(8deg) }} 95% {{ transform: translate(-3px,1px) }} 97% {{ transform: none }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>

  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <rect width="{W}" height="{H}" fill="url(#neb1)"/>
  <rect width="{W}" height="{H}" fill="url(#neb2)"/>
  <g>
    {stars(140, W, H, 330)}
  </g>
  <g class="shoot"><line x1="1150" y1="20" x2="1215" y2="-12" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".9"/></g>

  <!-- ringed planet -->
  <g transform="translate(1085,70)">
    <circle r="26" fill="#ff7ad9" opacity=".85"/>
    <ellipse rx="46" ry="9" fill="none" stroke="#ffd1f3" stroke-width="3" opacity=".7" transform="rotate(-18)"/>
  </g>

  <!-- tractor beam -->
  <polygon class="beam" points="828,150 892,150 960,372 760,372" fill="url(#beam)"/>
  <g transform="translate(860,160)">
      {particles}
  </g>

  <!-- abducted cargo: a git commit node -->
  <g class="cargo">
    <g transform="translate(-16,-16)" filter="url(#glow)">
      <rect width="32" height="32" rx="7" fill="#7dffb2"/>
      <text x="16" y="22" text-anchor="middle" font-family="{MONO}" font-size="15" font-weight="800" fill="#0a0418">&lt;/&gt;</text>
    </g>
  </g>

  <!-- UFO -->
  <g class="ufo">
    <ellipse cx="0" cy="-22" rx="46" ry="38" fill="url(#dome)"/>
    <path d="M-18 -40 q10 -14 26 -10" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none" opacity=".8"/>
    <ellipse cx="0" cy="2" rx="118" ry="26" fill="url(#hull)"/>
    <ellipse cx="0" cy="-4" rx="118" ry="12" fill="#eef1f7" opacity=".35"/>
    <ellipse cx="0" cy="22" rx="42" ry="8" fill="#7dffb2" filter="url(#glow)"/>
    <g filter="url(#glow)">
      {lights}
    </g>
  </g>

  <!-- planet surface -->
  <path d="M0 360 C120 330 220 372 340 350 S560 318 700 352 S940 380 1060 346 S1180 340 1200 352 V420 H0 Z" fill="url(#ground)"/>
  <path d="M0 382 C160 370 300 396 470 380 S780 392 940 384 S1140 376 1200 386 V420 H0 Z" fill="#0a0418"/>
  <g fill="#0a0418">
    <path d="M120 362 l6 -26 l6 26 z"/><path d="M560 346 l5 -20 l5 20 z"/><path d="M1130 350 l6 -24 l6 24 z"/>
  </g>
  <ellipse cx="860" cy="372" rx="100" ry="10" fill="#7dffb2" opacity=".25" class="beam"/>

  <!-- text -->
  <g transform="translate(64,150)">
    <g class="glitch"><text class="title">PAUL DAWSON</text></g>
    <text y="46" class="sub">BLACKLANE PLATFORM SECURITY</text>
    <clipPath id="typeclip"><rect x="0" y="80" height="30" width="0">{typing("width")}</rect></clipPath>
    <text y="100" class="term" clip-path="url(#typeclip)">{LINE}</text>
    <rect x="0" y="104" width="11" height="3" class="cursor">{typing("x")}</rect>
  </g>
</svg>
'''


def divider():
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
  {stars(40, w, h)}
  <g class="mini">
    <ellipse cy="-6" rx="10" ry="8" fill="#5ef2d6" opacity=".85"/>
    <ellipse rx="26" ry="6" fill="#a5abc0"/>
    <circle cx="-14" r="2" class="lt"/><circle r="2" class="lt" style="animation-delay:.27s"/><circle cx="14" r="2" class="lt" style="animation-delay:.54s"/>
  </g>
</svg>
'''


(OUT / "ufo-hero.svg").write_text(hero())
(OUT / "ufo-divider.svg").write_text(divider())
print("written", *sorted(p.name for p in OUT.iterdir()))

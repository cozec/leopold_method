"""Build index.html: a one-page report of every Leopold screening step.

Reads the latest scored screen (results/screen_<date>.csv), the bottleneck
scores (results/bottleneck_scores.json) and the universe (src/universe.json),
and writes a self-contained index.html at the project root. The research
narrative for steps 2 and 5 lives in the constants below; update it when the
bottleneck scores are re-researched.

Usage:
    python src/build_report.py            # latest results/screen_*.csv
    python src/build_report.py --csv results/screen_2026-09-30.csv
"""

import argparse
import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# Step 2 research: (layer, score label, evidence, easing signal, source keys).
EVIDENCE = [
    ("memory", "5 (STX/WDC 4)",
     "All three HBM suppliers call 2026 output sold out. HBM3E spot ~$2,100 "
     "vs $300–400 on long-term contracts (Sep 4, 2026). Conventional DRAM "
     "contract +93–98% QoQ in Q1 2026. 30TB enterprise SSD $3.5k → $22.6k "
     "(Q3 2025 → Aug 2026).",
     "Samsung / SK Hynix new fabs ramp 2H 2027; consensus turn 2H27–2028. "
     "Memory stocks already sold off on oversupply fears.",
     ["wiki", "trendforce", "astute", "marketwise", "hynix2030"]),
    ("power_generation", "5 (BE 4)",
     "PJM 2027/28 capacity auction cleared at the $333.44/MW-day cap for the "
     "2nd year and still fell 6.6 GW short of the reliability target; ~5.1 GW "
     "of the 5.25 GW load growth is data centers. GE Vernova gas-turbine "
     "backlog 116 GW, slots booked to 2030.",
     "Capacity-price cap reform; large new gas/nuclear build coming online.",
     ["pjm", "gev"]),
    ("foundry_equipment", "4 (TSM 5, ASML 4, tools 3)",
     "TSMC CoWoS-S and CoWoS-L fully booked, 52–78 week lead times; NVIDIA "
     "holds ~60% of capacity; 2026 demand ~1.0M wafers vs ~370k in 2024.",
     "CoWoS capacity reaching 130–150k wafers/month by end-2026 — watch for "
     "lead times shrinking.",
     ["cowos"]),
    ("networking_optics", "4 (LITE 5, ANET/ALAB 3)",
     "200G-per-lane EML lasers (needed for 1.6T optics) are the tightest part "
     "of the optical chain; Lumentum is the only volume supplier. NVIDIA "
     "locked up $4B of Lumentum/Coherent laser capacity (Mar 2026).",
     "InP substrate / epi-wafer capacity additions.",
     ["eml"]),
    ("accelerators", "4 (AMD/MRVL 3)",
     "Output gated by CoWoS and HBM. Big-4 hyperscaler 2026 capex ~$725B; "
     "Alphabet and Meta raised guidance; 2027 modeled above $1T.",
     "Hyperscaler capex cuts; custom-ASIC share shifts.",
     ["capex", "creditsights"]),
    ("power_cooling_equipment", "4",
     "Average US transformer lead time ~128 weeks, 3–5 years for the largest "
     "units. Vertiv backlog $15B, book-to-bill 2.9× (Q4 2025).",
     "Lead times shortening; book-to-bill falling toward 1×.",
     ["transformers", "vertiv"]),
    ("datacenter_neocloud", "2 (EQIX/DLR 3)",
     "H100 rents ~$3.84/GPU-hr on average (Sep 2026) and prices fell after "
     "Blackwell shipped. GPUs are no longer the scarce input — capital is.",
     "Already commoditizing.",
     ["gpu"]),
]

SOURCES = {
    "wiki": ("Wikipedia — 2024–present memory shortage",
             "https://en.wikipedia.org/wiki/2024%E2%80%93present_global_memory_supply_shortage"),
    "trendforce": ("TrendForce — HBM contract price surge",
                   "https://www.trendforce.com/research/download/RP260527UC"),
    "astute": ("Astute — enterprise SSD prices up 80%",
               "https://www.astutegroup.com/news/memory-shortages/ai-memory-shortage-drives-enterprise-ssd-prices-up-80/"),
    "marketwise": ("MarketWise — memory stocks trending down",
                   "https://marketwise.com/investing/why-micron-sk-hynix-samsung-stock-is-tumbling-during-memory-shortage/"),
    "hynix2030": ("Tech-Insider — SK Hynix: shortage may last past 2030",
                  "https://tech-insider.org/memory-chip-shortage-2026-ai-consumer-electronics/"),
    "pjm": ("Power Engineering — PJM auction hits price cap again",
            "https://www.power-eng.com/business/pjm-capacity-auction-hits-price-cap-again-as-region-falls-short-of-reliability-target/"),
    "gev": ("Utility Dive — GE Vernova gas turbine backlog 116 GW",
            "https://www.utilitydive.com/news/ge-vernova-gas-turbine-backlog-climbs-to-116-gw/826039/"),
    "cowos": ("SiliconAnalysts — TSMC CoWoS sold out",
              "https://siliconanalysts.com/analysis/foundry-allocation-status-q1-2026"),
    "eml": ("TechTimes — NVIDIA $4B laser lockup",
            "https://www.techtimes.com/articles/317281/20260527/ai-data-center-optical-component-shortage-nvidias-4b-laser-lockup-pushes-rivals-past-2027.htm"),
    "capex": ("AI Weekly — $725B 2026 hyperscaler capex",
              "https://aiweekly.co/alerts/amazon-microsoft-alphabet-meta-plan-725b-ai-capex-in-2026"),
    "creditsights": ("CreditSights — raising hyperscaler capex estimates",
                     "https://know.creditsights.com/insights/tech-raising-hyperscaler-capex-2026-estimates/"),
    "transformers": ("TheNextWeb — US power firms scramble for transformers",
                     "https://thenextweb.com/news/us-power-companies-scramble-data-centre-equipment"),
    "vertiv": ("Nasdaq — Vertiv's $15B backlog",
               "https://www.nasdaq.com/articles/vertivs-15-billion-backlog-loudest-ai-signal-2026"),
    "gpu": ("Mercatus — GPU rental prices",
            "https://www.mercatus-ai.com/blog/gpu-rental-prices"),
}

# Step 5 judgement: (tickers, headline, what's priced in, thesis breaks if).
PRICED_IN = [
    ("MU · Samsung · SK Hynix · SNDK", "Memory — cheap on peak earnings",
     "4–7× forward P/E vs ~12–15× mid-cycle: the market already assumes peak "
     "earnings roughly halve after ~2 years, i.e. it prices the turn for "
     "2H27–2028 — exactly when new Korean fabs ramp. Upside needs the "
     "shortage to outlast 2028 (SK Hynix's CEO says past 2030). 12-1 momentum "
     "of +245% to +1,280% shows how much has already run.",
     "DRAM/HBM contract prices fall QoQ, or 2027 hyperscaler capex is cut."),
    ("TSM", "Sole CoWoS supplier at a normal multiple",
     "~21× forward — not a cyclical discount, and only 4% off its 52-week "
     "high. Priced as a durable compounder rather than a scarcity windfall.",
     "CoWoS doubling outruns demand (lead times shrink); Taiwan geopolitics."),
    ("VST", "Contrarian: bottleneck not yet in reported numbers",
     "Bottleneck 5 and cheap (13× forward, −34% off high, −30% momentum), but "
     "the economics score is weak (revenue −6%). Scarcity shows in PJM "
     "capacity prices that flow into earnings from 2026/27 onward.",
     "Capacity-price cap reform, or a wave of new gas supply."),
]

LAYER_LABEL = {
    "accelerators": "Accelerators",
    "memory": "HBM / memory",
    "foundry_equipment": "Foundry & equipment",
    "networking_optics": "Networking & optics",
    "datacenter_neocloud": "Data centers / neocloud",
    "power_generation": "Power generation",
    "power_cooling_equipment": "Power & cooling equipment",
}

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a64;--card:#fff;--line:#e4e2da;
--accent:#b4531f;--good:#2f7d4f;--bad:#b3261e;--bar:#d9a07c;--chip:#f1eee6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161614;
--fg:#ecebe6;--muted:#a3a198;--card:#1f1f1c;--line:#34332e;--accent:#e58a52;
--good:#6cc08f;--bad:#f07a70;--bar:#8a5434;--chip:#2a2926}}
:root[data-theme="dark"]{--bg:#161614;--fg:#ecebe6;--muted:#a3a198;--card:#1f1f1c;
--line:#34332e;--accent:#e58a52;--good:#6cc08f;--bad:#f07a70;--bar:#8a5434;--chip:#2a2926}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:2rem;margin:0 0 4px}h2{margin:48px 0 8px;font-size:1.35rem}
h2 .n{color:var(--accent);margin-right:8px}
.sub{color:var(--muted);margin:0 0 24px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.chain{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:12px 0}
.chain span{background:var(--chip);border:1px solid var(--line);border-radius:999px;
padding:4px 12px;font-size:.9rem}.chain i{color:var(--muted);font-style:normal}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{position:sticky;top:0;background:var(--card);color:var(--muted);font-weight:600}
td.l,th.l{text-align:left}td.w{white-space:normal;min-width:260px;text-align:left}
tr:last-child td{border-bottom:0}
.bar{position:relative;display:inline-block;width:64px;height:8px;background:var(--chip);
border-radius:4px;vertical-align:middle;margin-left:6px}
.bar b{position:absolute;left:0;top:0;bottom:0;background:var(--bar);border-radius:4px}
.dots{letter-spacing:1px;color:var(--accent)}
.flag{color:var(--bad);font-weight:600}.pos{color:var(--good)}.neg{color:var(--bad)}
.top td{font-weight:600}
code{background:var(--chip);padding:1px 5px;border-radius:4px;font-size:.88em}
.warn{border-left:4px solid var(--bad)}
ol.src{font-size:.85rem;color:var(--muted)}a{color:var(--accent)}
footer{margin-top:48px;color:var(--muted);font-size:.85rem}
"""


def esc(v):
    """HTML-escape any value as a string."""
    return html.escape(str(v))


def pct(v, signed=False):
    """Format a fraction as a percent, blank when missing."""
    if pd.isna(v):
        return ""
    s = f"{v:+.0%}" if signed else f"{v:.0%}"
    cls = "pos" if v > 0 else "neg" if v < 0 else ""
    return f'<span class="{cls}">{s}</span>' if signed else s


def num(v, fmt="{:.1f}"):
    """Format a number, blank when missing or non-positive (loss-makers)."""
    return "" if pd.isna(v) or v <= 0 else fmt.format(v)


def bar(v):
    """Render a 0–1 score as a number plus a small horizontal bar."""
    if pd.isna(v):
        return ""
    return f'{v:.2f}<span class="bar"><b style="width:{v * 100:.0f}%"></b></span>'


def dots(v):
    """Render a 1–5 bottleneck score as filled/empty dots."""
    if pd.isna(v):
        return ""
    n = int(v)
    return f'<span class="dots" title="{n}/5">{"●" * n}{"○" * (5 - n)}</span>'


def results_table(df):
    """Build the full scored-screen table (steps 4–5)."""
    head = ("<tr><th>#</th><th class='l'>Ticker</th><th class='l'>Layer</th>"
            "<th>Bottleneck</th><th>Composite</th><th>Economics</th>"
            "<th>Valuation</th><th>Rev growth</th><th>Op margin</th>"
            "<th>GM Δ YoY</th><th>Fwd P/E</th><th>Growth-adj P/E</th>"
            "<th>EV/Sales</th><th>12-1 mom</th><th>Off 52w high</th>"
            "<th>1y vol</th><th>Risk</th></tr>")
    rows = []
    for i, (t, r) in enumerate(df.iterrows(), 1):
        cls = ' class="top"' if i <= 5 else ""
        rows.append(
            f"<tr{cls}><td>{i}</td><td class='l' title='{esc(r['name'])}'>"
            f"{esc(t)}</td><td class='l'>{esc(LAYER_LABEL.get(r['layer'], r['layer']))}</td>"
            f"<td>{dots(r.get('bottleneck'))}</td><td>{bar(r['composite'])}</td>"
            f"<td>{bar(r['economics'])}</td><td>{bar(r['valuation'])}</td>"
            f"<td>{pct(r['rev_growth'])}</td><td>{pct(r['op_margin'])}</td>"
            f"<td>{pct(r['gm_change_yoy'], True)}</td><td>{num(r['fwd_pe'])}</td>"
            f"<td>{num(r['growth_adj_pe'], '{:.2f}')}</td><td>{num(r['ev_sales'])}</td>"
            f"<td>{pct(r['mom_12_1'], True)}</td><td>{pct(r['off_52w_high'], True)}</td>"
            f"<td>{pct(r['vol_1y'])}</td>"
            f"<td class='flag'>{esc(r['risk_flag']) if isinstance(r['risk_flag'], str) else ''}</td></tr>")
    return f"<div class='tw'><table>{head}{''.join(rows)}</table></div>"


def build(csv_path):
    """Assemble the full HTML report and return it as a string.

    Args:
        csv_path: path to a scored screen CSV from leopold_screen.py.

    Returns:
        HTML document string.
    """
    date = csv_path.stem.replace("screen_", "")
    df = pd.read_csv(csv_path, index_col=0)
    universe = json.loads((ROOT / "src" / "universe.json").read_text())
    scores = json.loads(
        (ROOT / "results" / "bottleneck_scores.json").read_text())

    src_ids = {k: i for i, k in enumerate(SOURCES, 1)}
    chain = " <i>→</i> ".join(
        f"<span>{esc(s.strip())}</span>" for s in universe["chain"].split("->"))

    ev_rows = "".join(
        f"<tr><td class='l'>{esc(LAYER_LABEL[layer])}</td>"
        f"<td>{dots(scores.get(layer))}</td><td class='l'>{esc(label)}</td>"
        f"<td class='w'>{esc(ev)} "
        + "".join(f"<sup><a href='#s{src_ids[k]}'>[{src_ids[k]}]</a></sup>"
                  for k in keys)
        + f"</td><td class='w'>{esc(ease)}</td></tr>"
        for layer, label, ev, ease, keys in EVIDENCE)

    uni_cards = "".join(
        f"<div class='card'><strong>{esc(LAYER_LABEL[k])}</strong>"
        f"<div class='sub' style='margin:4px 0 8px'>{esc(v['bottleneck'])}</div>"
        f"<code>{' · '.join(esc(t) for t in v['tickers'])}</code></div>"
        for k, v in universe["layers"].items())

    priced = "".join(
        f"<div class='card'><div class='sub' style='margin:0'>{esc(t)}</div>"
        f"<strong>{esc(h)}</strong><p>{esc(p)}</p>"
        f"<p><b>Thesis breaks if:</b> {esc(b)}</p></div>"
        for t, h, p, b in PRICED_IN)

    sources = "".join(
        f"<li id='s{i}'><a href='{esc(u)}'>{esc(n)}</a></li>"
        for i, (n, u) in enumerate(SOURCES.values(), 1))

    top = df.head(5).index.tolist()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Leopold Bottleneck Screen</title><style>{CSS}</style></head>
<body><main>
<h1>Leopold bottleneck screen</h1>
<p class="sub">AI-infrastructure stock screen in the style of Leopold Aschenbrenner's
<em>Situational Awareness</em>. Run date {esc(date)} · {len(df)} tickers · 7 layers ·
Top 5: <strong>{esc(', '.join(top))}</strong></p>

<div class="grid">
<div class="card"><strong>1. Mega-trend</strong><br>What could grow 5–10×?</div>
<div class="card"><strong>2. Bottleneck</strong><br>What scarce resource limits it?</div>
<div class="card"><strong>3. Supplier</strong><br>Who controls that bottleneck?</div>
<div class="card"><strong>4. Economics</strong><br>Is scarcity showing up as pricing power?</div>
<div class="card"><strong>5. Valuation</strong><br>Has the market already priced it in?</div>
</div>

<h2><span class="n">1</span>Mega-trend</h2>
<p>{esc(universe['thesis'])} Don't buy the famous AI name; follow the physical
supply chain and find where it runs out of something.</p>
<div class="chain">{chain}</div>

<h2><span class="n">2</span>Bottleneck — how scarce is each layer?</h2>
<p class="sub">Scored 1–5 from web research dated September 2026 (5 = acute scarcity, few
suppliers, rising prices). Ticker overrides shown in the label column. The
"easing" column is the exit signal.</p>
<div class="tw"><table><tr><th class="l">Layer</th><th>Score</th><th class="l">Overrides</th>
<th class="l">Evidence</th><th class="l">Easing signal to watch</th></tr>{ev_rows}</table></div>

<h2><span class="n">3</span>Supplier — who controls it?</h2>
<p class="sub">Universe from <code>src/universe.json</code>.</p>
<div class="grid">{uni_cards}</div>

<h2><span class="n">4–5</span>Economics &amp; valuation — the quant screen</h2>
<div class="card">
<p style="margin-top:0"><b>Economics</b> = mean percentile rank of revenue growth, EPS growth,
operating margin and YoY gross-margin change (margin expansion = pricing power).<br>
<b>Valuation</b> = mean inverse rank of forward P/E, PEG, EV/Sales and growth-adjusted P/E
(fwd P/E ÷ fwd EPS growth %); loss-makers rank worst.<br>
<b>Composite</b> = 0.4 × bottleneck (scaled 0–1) + 0.3 × economics + 0.3 × valuation.<br>
<b>Risk = HIGH</b> when 1-year volatility &gt; 70% or 1-year max drawdown worse than −50%.</p>
<p style="margin-bottom:0" class="sub">Data: yfinance fundamentals + 2y daily prices, pulled {esc(date)}.
Blank P/E-type cells are loss-makers or missing data.</p></div>
<p></p>
{results_table(df)}

<h2><span class="n">5</span>Priced in? — judging the finalists</h2>
<div class="grid">{priced}</div>

<h2>Risk</h2>
<div class="card warn">
<p style="margin-top:0">The top four are all memory and all flagged HIGH risk (1y vol 75–116%). They move
together, so together they are one bet on one cycle. The July 2026 AI-semis selloff hit this exact
book hard. Size positions accordingly; this page does not suggest leverage or options.</p>
<p style="margin-bottom:0">Yahoo data can be stale or wrong: Korean tickers mix currencies and lack
growth-adjusted P/E, and EV/Sales above 200× is dropped as an artifact (ASML). Verify anything that
drives a top pick against company filings.</p></div>

<h2>Sources</h2><ol class="src">{sources}</ol>

<footer>Research only, not financial advice. Generated by <code>src/build_report.py</code>
from <code>{esc(csv_path.name)}</code>.</footer>
</main></body></html>
"""


def main():
    """Parse CLI args and write index.html at the project root."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, help="scored screen CSV")
    args = ap.parse_args()
    csv_path = args.csv or max((ROOT / "results").glob("screen_*.csv"))
    out = ROOT / "index.html"
    out.write_text(build(csv_path))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

# Summary

## Status (2026-09-30)
- Built `/leopold-pick` skill + `src/leopold_screen.py` quant screen over 34 AI-infrastructure
  tickers across 7 bottleneck layers.
- First run is **without** bottleneck scores (composite = 0.5 economics + 0.5 valuation).
  Steps 1–3 now done: bottleneck-weighted run below.

## Bottleneck-weighted screen — 2026-09-30 (composite = 0.4·bottleneck + 0.3·economics + 0.3·valuation)
Bottleneck scores (1–5) in `results/bottleneck_scores.json`, from web research dated Sep 2026.

| Layer | Score | Evidence (Sep 2026) | Easing signal to watch |
|---|---|---|---|
| memory (HBM/DRAM/NAND) | 5 (HDD: 4) | HBM 2026 output sold out at all 3 suppliers; HBM3E spot ~$2,100 vs $300–400 LTA; DRAM contract +93–98% QoQ in Q1; 30TB eSSD $3.5k→$22.6k | Samsung/Hynix new fabs ramp 2H27; consensus turn 2H27–2028 |
| power_generation | 5 (BE: 4) | PJM 27/28 auction at $333/MW-day cap 2nd year, 6.6 GW short of reliability target; GEV gas-turbine backlog 116 GW, slots to 2030 | New gas/nuclear capacity; capacity-price cap reform |
| foundry (TSM) | 5 (ASML 4, tools 3) | CoWoS fully booked, 52–78 wk lead times; NVDA ~60% of capacity | CoWoS → 130–150k wpm by end-2026 |
| networking_optics | 4 (LITE 5; ANET/ALAB 3) | 200G EML shortage; LITE sole volume 200G EML supplier; NVDA $4B laser lockup | InP substrate/epi capacity adds |
| accelerators | 4 (AMD/MRVL 3) | Gated by CoWoS/HBM; hyperscaler 2026 capex ~$725B, 2027 >$1T modeled | Capex cuts; custom-ASIC share |
| power_cooling_equipment | 4 | Large transformer lead times ~128 wk (3–5 yr for biggest units) | Lead times shortening |
| datacenter_neocloud | 2 (EQIX/DLR 3) | H100 rent ~$3.84/hr, fell after Blackwell; GPUs no longer scarce, just capital | — (commoditizing) |

| Rank | Ticker | Layer | Bneck | Composite | Econ | Val | Rev growth | Op margin | GM Δ | Fwd P/E | 12-1 mom | Off 52w high | 1y vol | Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MU | memory | 5 | 0.95 | 0.98 | 0.85 | 346% | 80% | +47pp | 6.6 | 486% | -12% | 82% | HIGH |
| 2 | 005930.KS (Samsung) | memory | 5 | 0.88 | 0.88 | 0.73 | 130% | 52% | +35pp | 3.8 | 245% | -26% | 75% | HIGH |
| 3 | 000660.KS (SK Hynix) | memory | 5 | 0.88 | 0.92 | 0.68 | 257% | 76% | +29pp | 3.8 | 405% | -39% | 91% | HIGH |
| 4 | SNDK | memory | 5 | 0.81 | 0.74 | 0.63 | 372% | 78% | +58pp | 6.6 | 1280% | -25% | 116% | HIGH |
| 5 | TSM | foundry | 5 | 0.77 | 0.63 | 0.60 | 36% | 60% | +9pp | 20.8 | 53% | -4% | 40% | |
| 6 | STX | memory | 4 | 0.72 | 0.70 | 0.71 | 48% | 43% | +15pp | 16.7 | 265% | -16% | 75% | HIGH |
| 7 | AVGO | accelerators | 4 | 0.70 | 0.70 | 0.65 | 86% | 54% | +2pp | 18.1 | 14% | -27% | 47% | |
| 8 | NVDA | accelerators | 4 | 0.70 | 0.69 | 0.65 | 106% | 66% | +3pp | 14.6 | 22% | -3% | 38% | |
| 9 | VST | power_generation | 5 | 0.70 | 0.18 | 0.82 | -6% | 14% | -2pp | 13.4 | -30% | -34% | 48% | |
| 10 | WDC | memory | 4 | 0.66 | 0.72 | 0.49 | 44% | 44% | +13pp | 14.3 | 287% | -39% | 80% | HIGH |

Full table: `results/screen_2026-09-30.md`.

### Priced in? (top 5 + VST)
- **Memory (MU, Samsung, Hynix, SNDK):** 4–7× forward P/E vs ~12–15× mid-cycle means the market
  already assumes peak earnings roughly halve after ~2 years — i.e. it is pricing the turn for
  2H27–2028, exactly when new Korean fabs ramp. Upside needs the shortage to outlast 2028
  (Hynix CEO claims "past 2030"). Already up 2.5–13× on 12-1 momentum. Thesis breaks if DRAM/HBM
  contract prices fall QoQ or hyperscaler 2027 capex is cut.
- **TSM:** 21× fwd for the sole CoWoS supplier; not a cyclical multiple, only 4% off high. Breaks if
  CoWoS doubling outruns demand (lead times shrink) or on Taiwan geopolitical risk.
- **VST:** bottleneck 5 and cheap (13× fwd, -34% off high, negative momentum), but economics weak
  (rev -6%) — scarcity shows in PJM capacity prices, not yet in reported margins. Breaks on capacity-
  price cap reform or large new-build gas supply.

### Risk
- Top 4 are all memory, all HIGH risk (vol 75–116%), and highly correlated — a single-factor bet on
  one cycle. The July 2026 AI-semis selloff hit this exact book. Size accordingly; no leverage.
- Research only, not financial advice.

## First run without bottleneck scores — 2026-09-30

### Screen results — 2026-09-30 (top 10 of 34, by composite)
Data: yfinance fundamentals + 2y daily prices. Scores are percentile ranks within the universe.

| Ticker | Layer | Composite | Economics | Valuation | Rev growth | Op margin | GM Δ YoY | Fwd P/E | 12-1 mom | Off 52w high | 1y vol | Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MU | memory | 0.92 | 0.98 | 0.85 | 346% | 80% | +47pp | 6.6 | 486% | -12% | 82% | HIGH |
| 005930.KS (Samsung) | memory | 0.81 | 0.88 | 0.73 | 130% | 52% | +35pp | 3.8 | 245% | -26% | 75% | HIGH |
| 000660.KS (SK Hynix) | memory | 0.80 | 0.92 | 0.68 | 257% | 76% | +29pp | 3.8 | 405% | -39% | 91% | HIGH |
| STX | memory | 0.70 | 0.70 | 0.71 | 48% | 43% | +15pp | 16.7 | 265% | -16% | 75% | HIGH |
| SNDK | memory | 0.68 | 0.74 | 0.63 | 372% | 78% | +58pp | 6.6 | 1280% | -25% | 116% | HIGH |
| AVGO | accelerators | 0.67 | 0.70 | 0.65 | 86% | 54% | +2pp | 18.1 | 14% | -27% | 47% | |
| NVDA | accelerators | 0.67 | 0.69 | 0.65 | 106% | 66% | +3pp | 14.6 | 22% | -3% | 38% | |
| TSM | foundry_equipment | 0.62 | 0.63 | 0.60 | 36% | 60% | +9pp | 20.8 | 53% | -4% | 40% | |
| WDC | memory | 0.61 | 0.72 | 0.49 | 44% | 44% | +13pp | 14.3 | 287% | -39% | 80% | HIGH |
| AMD | accelerators | 0.53 | 0.62 | 0.44 | 50% | 17% | +14pp | 39.3 | 192% | -3% | 73% | HIGH |

Full table: `results/screen_2026-09-30.md`.

## Observations
- The screen independently lands on the same memory-heavy book the 13F showed (MU, SNDK top-5).
  Scarcity is visible in the numbers: gross margins up 30–58pp YoY.
- Memory's low forward P/E (4–7×) is the classic peak-cycle signal — step 5 must judge whether
  the HBM/NAND shortage outlasts what that multiple implies.
- Every memory name carries a HIGH risk flag (1y vol 75–116%).
- Neoclouds (NBIS, CRWV, IREN) rank last: loss-making, so valuation ranks worst.

## Known data caveats
- Korean tickers: no growth-adjusted P/E (Yahoo trailing EPS missing/currency mix).
- ASML EV/Sales returned ~1100× from Yahoo (currency mismatch) — dropped by the >200× filter.

---
name: leopold-pick
description: Pick stocks with Leopold Aschenbrenner's Situational Awareness method — start from a mega-trend, trace its physical supply chain, find the bottleneck, find who controls it, check whether scarcity shows up as pricing power, then ask how much is already priced in. Use when the user asks to pick/screen/rank stocks "Leopold style", find AI-infrastructure bottleneck plays, or re-run the bottleneck screen.
---

# Leopold bottleneck stock picker

Project root: `/Users/adam/trading/leopold_method`. Python: `.venv/bin/python`.

## The method (5-step screen)

| Step | Question | Who answers |
|---|---|---|
| 1. Mega-trend | What technology could grow 5–10×? | You (research) |
| 2. Bottleneck | What scarce resource limits that growth? | You (research) |
| 3. Supplier | Which companies control that bottleneck? | You → `src/universe.json` |
| 4. Economics | Is scarcity showing up as pricing power / margin expansion? | Script (`economics` score) |
| 5. Valuation | Has the market already priced the growth in? | Script (`valuation` score) + you |

Core idea: don't buy the famous AI name — buy the company sitting on the **physical constraint** the market underestimates. Default chain:
AI models → accelerators → HBM/memory → networking → data centers → electricity → cooling/power equipment.

## Workflow

1. **Frame the trend (step 1).** Default thesis is AI scaling. If the user names a different trend (robotics, nuclear, space, biotech…), write a new chain for it and a new universe JSON (same schema as `src/universe.json`).

2. **Score each bottleneck layer 1–5 (step 2).** Use WebSearch for *current* evidence, not memory. Look for: lead times, sold-out capacity, contract prices rising (e.g. DRAM/HBM spot & contract), hyperscaler capex guidance, interconnect queue lengths, supplier count. 5 = acute scarcity with few suppliers and rising prices; 1 = ample supply / commoditized. Also note any sign the bottleneck is *easing* (new capacity coming online, price declines) — that is the exit signal.
   Write scores to `results/bottleneck_scores.json` as `{"memory": 5, "power_generation": 4, ..., "MU": 5}` (layer keys; ticker keys override their layer).

3. **Check suppliers (step 3).** Confirm each layer's tickers in `src/universe.json` actually control the bottleneck (market share, capacity share). Add missing names or pass ad-hoc names with `--tickers`.

4. **Run the quant screen (steps 4–5):**
   ```bash
   cd /Users/adam/trading/leopold_method
   caffeinate -dimsu .venv/bin/python src/leopold_screen.py --bottleneck results/bottleneck_scores.json
   # ad-hoc: add  --tickers MU SNDK TSM
   ```
   Outputs `results/screen_<date>.csv` / `.md`, prices cached to `data/<ticker>.csv`, log in `logs/`.
   - `economics` = percentile rank of revenue growth, EPS growth, operating margin, YoY gross-margin change (margin expansion = pricing power).
   - `valuation` = inverse rank of forward P/E, PEG, EV/Sales, growth-adjusted P/E (fwd P/E ÷ fwd EPS growth %). Loss-makers rank worst.
   - `composite` = 0.4·bottleneck + 0.3·economics + 0.3·valuation (0.5/0.5 without bottleneck scores).
   - `risk_flag = HIGH` when 1y vol > 70% or 1y max drawdown worse than −50%.

5. **Judge "priced in?" for the top ~5 (step 5).** Low P/E on peak-cycle earnings is a trap for cyclicals (memory especially): a 5× forward P/E on record margins can mean the market expects the cycle to turn. For each finalist, state what the price implies (e.g. what earnings must hold for how long) and whether the bottleneck will outlast that. Use `mom_12_1` and `off_52w_high` to show how much has already run.

6. **Report.** For each pick give: the chain link it sits on, the bottleneck evidence (with sources/dates), economics, valuation, what's priced in, the risk flag, and the "thesis breaks if…" condition. Update `summary.md` with the ranked table and date.

## Guardrails

- This replicates a *concentrated* style. The July 2026 AI-semis selloff hit Aschenbrenner's fund hard. Always state position-sizing risk; never suggest leverage or options unless asked.
- Screen metrics come from Yahoo (`yfinance`) and can be stale or wrong (foreign tickers mix currencies; EV/Sales > 200 is dropped as a data artifact). Sanity-check anything that drives a top pick.
- No backtests here — if the user asks for one, follow the global backtest rules (next-open fills, $10k start, no lookahead).
- This is research, not financial advice; say so once in the report.

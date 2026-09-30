# Leopold Method — bottleneck stock picker

Stock-picking framework modeled on Leopold Aschenbrenner's *Situational Awareness* approach
(see `from_chapgpt.txt`): start from a mega-trend, trace its physical supply chain, find the
bottleneck, find who controls it, check whether scarcity shows up as pricing power, then ask
how much is already priced in.

## Pieces
- `.claude/skills/leopold-pick/SKILL.md` — Claude Code skill (`/leopold-pick`) that runs the full
  5-step process: research-based bottleneck scoring (steps 1–3) + the quant screen (steps 4–5) +
  a "priced in?" review of finalists.
- `src/universe.json` — the AI-infrastructure supply chain, by layer, with candidate tickers.
- `src/leopold_screen.py` — yfinance screen: economics score (growth, margins, margin expansion),
  valuation score (fwd P/E, PEG, EV/Sales, growth-adjusted P/E), momentum and risk flags.
- `src/build_report.py` — renders `index.html` (English) and `index_zh.html` (中文), one-page reports of all 5 steps and the latest
  screen results (`python src/build_report.py` after a screen run).

## Setup & run
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/leopold_screen.py                                   # default universe
python src/leopold_screen.py --tickers MU SNDK TSM             # ad-hoc list
python src/leopold_screen.py --bottleneck results/bottleneck_scores.json
```
Outputs go to `results/screen_<date>.csv|.md`; price CSVs to `data/`; logs to `logs/`.

Research tool, not financial advice. The style is concentrated and high-volatility by design.

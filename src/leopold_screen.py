"""Leopold-style bottleneck stock screen.

Quantifies steps 4 (Economics) and 5 (Valuation) of the 5-step screen for a
universe of AI-infrastructure bottleneck candidates, plus price-based risk
flags. Steps 1-3 (mega-trend, bottleneck, supplier) are judgement calls; pass
them in as per-layer or per-ticker bottleneck scores (1-5) via --bottleneck.

Usage:
    python src/leopold_screen.py
    python src/leopold_screen.py --tickers MU SNDK TSM
    python src/leopold_screen.py --bottleneck results/bottleneck_scores.json
"""

import argparse
import json
import logging
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
LOGS_DIR = ROOT / "logs"
UNIVERSE_FILE = ROOT / "src" / "universe.json"

log = logging.getLogger("leopold")


def load_universe(path):
    """Load the bottleneck universe and return a {ticker: layer} mapping.

    Args:
        path: Path to universe.json.

    Returns:
        dict mapping ticker symbol to its supply-chain layer name.
    """
    universe = json.loads(Path(path).read_text())
    return {t: layer for layer, spec in universe["layers"].items()
            for t in spec["tickers"]}


def download_prices(ticker):
    """Download ~2 years of daily prices and cache them as data/<ticker>.csv.

    Args:
        ticker: Yahoo Finance symbol.

    Returns:
        DataFrame indexed by Date with Open, High, Low, Close, Volume, or an
        empty DataFrame if no data came back.
    """
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.index.name = "Date"
    df.to_csv(DATA_DIR / f"{ticker}.csv")
    return df


def price_metrics(close):
    """Compute momentum and risk metrics from a daily close series.

    Args:
        close: Series of daily closes, oldest first.

    Returns:
        dict with ret_3m, mom_12_1, off_52w_high, vol_1y, max_dd_1y.
    """
    out = dict.fromkeys(
        ["ret_3m", "mom_12_1", "off_52w_high", "vol_1y", "max_dd_1y"], np.nan)
    if len(close) < 64:
        return out
    last = close.iloc[-252:]
    out["ret_3m"] = close.iloc[-1] / close.iloc[-64] - 1
    if len(close) >= 253:
        out["mom_12_1"] = close.iloc[-22] / close.iloc[-253] - 1
    out["off_52w_high"] = close.iloc[-1] / last.max() - 1
    out["vol_1y"] = last.pct_change().std() * np.sqrt(252)
    out["max_dd_1y"] = (last / last.cummax() - 1).min()
    return out


def gross_margin_change(tk):
    """Year-over-year change in quarterly gross margin (percentage points).

    Compares the latest quarter with the quarter four periods earlier, or the
    oldest available quarter if fewer than five are reported.

    Args:
        tk: yfinance Ticker object.

    Returns:
        float change in gross margin, or NaN if unavailable.
    """
    try:
        q = tk.quarterly_income_stmt
        gm = (q.loc["Gross Profit"] / q.loc["Total Revenue"]).dropna()
    except (KeyError, AttributeError, TypeError):
        return np.nan
    if len(gm) < 2:
        return np.nan
    return gm.iloc[0] - gm.iloc[min(4, len(gm) - 1)]


def fundamentals(tk):
    """Pull the economics and valuation fields used by the screen.

    Args:
        tk: yfinance Ticker object.

    Returns:
        dict of fundamentals; missing fields are NaN.
    """
    info = tk.info or {}
    g = lambda k: info.get(k, np.nan)  # noqa: E731
    fwd_eps, ttm_eps = g("forwardEps"), g("trailingEps")
    fwd_growth = (fwd_eps / ttm_eps - 1
                  if isinstance(ttm_eps, (int, float)) and ttm_eps > 0
                  else np.nan)
    return {
        "name": info.get("shortName", ""),
        "mkt_cap_b": g("marketCap") / 1e9,
        "rev_growth": g("revenueGrowth"),
        "eps_growth": g("earningsGrowth"),
        "gross_margin": g("grossMargins"),
        "op_margin": g("operatingMargins"),
        "gm_change_yoy": gross_margin_change(tk),
        "fwd_pe": g("forwardPE"),
        "peg": g("trailingPegRatio"),
        # >200x is a Yahoo currency-mismatch artifact (e.g. ASML), not real
        "ev_sales": (lambda v: v if v < 200 else np.nan)(
            g("enterpriseToRevenue")),
        "fwd_eps_growth": fwd_growth,
        "target_upside": (g("targetMeanPrice") / g("currentPrice") - 1),
    }


def rank(series, higher_is_better=True):
    """Percentile-rank a series in [0, 1]; NaN/invalid values rank worst.

    Args:
        series: numeric Series.
        higher_is_better: flip the ranking when lower values are better.

    Returns:
        Series of percentile ranks.
    """
    r = series.rank(pct=True, ascending=higher_is_better)
    return r.fillna(0.0)


def score(df, bottleneck=None):
    """Add economics, valuation, and composite scores to the screen table.

    Valuation treats non-positive P/E, PEG, or EV/Sales (loss-makers) as
    missing so they rank worst. Growth-adjusted P/E = forward P/E divided by
    forward EPS growth in percent.

    Args:
        df: DataFrame produced by the screen, indexed by ticker.
        bottleneck: optional dict {ticker or layer: score 1-5}.

    Returns:
        DataFrame sorted by composite score, descending.
    """
    df = df.copy()
    pos = lambda s: s.where(s > 0)  # noqa: E731
    growth_pct = pos(df["fwd_eps_growth"]) * 100
    df["growth_adj_pe"] = pos(df["fwd_pe"]) / growth_pct

    df["economics"] = pd.concat([
        rank(df["rev_growth"]),
        rank(df["eps_growth"]),
        rank(df["op_margin"]),
        rank(df["gm_change_yoy"]),
    ], axis=1).mean(axis=1)
    df["valuation"] = pd.concat([
        rank(pos(df["fwd_pe"]), higher_is_better=False),
        rank(pos(df["peg"]), higher_is_better=False),
        rank(pos(df["ev_sales"]), higher_is_better=False),
        rank(df["growth_adj_pe"], higher_is_better=False),
    ], axis=1).mean(axis=1)

    if bottleneck:
        b = [bottleneck.get(t, bottleneck.get(layer, np.nan))
             for t, layer in zip(df.index, df["layer"])]
        df["bottleneck"] = pd.Series(b, index=df.index, dtype=float)
        b_norm = ((df["bottleneck"] - 1) / 4).fillna(0.0)
        df["composite"] = (0.4 * b_norm + 0.3 * df["economics"]
                           + 0.3 * df["valuation"])
    else:
        df["composite"] = 0.5 * df["economics"] + 0.5 * df["valuation"]

    df["risk_flag"] = np.where(
        (df["vol_1y"] > 0.70) | (df["max_dd_1y"] < -0.50), "HIGH", "")
    return df.sort_values("composite", ascending=False)


def run_screen(tickers, layers):
    """Download data and build the raw metric table.

    Args:
        tickers: list of ticker symbols.
        layers: dict {ticker: layer}.

    Returns:
        DataFrame indexed by ticker with fundamentals and price metrics.
    """
    rows = {}
    for t in tickers:
        log.info("fetching %s", t)
        try:
            tk = yf.Ticker(t)
            prices = download_prices(t)
            row = fundamentals(tk)
            if not prices.empty:
                row.update(price_metrics(prices["Close"]))
            row["layer"] = layers.get(t, "custom")
            rows[t] = row
        except Exception as exc:  # yfinance raises many types on bad symbols
            log.warning("skipping %s: %s", t, exc)
    return pd.DataFrame.from_dict(rows, orient="index")


def to_markdown(df):
    """Render the key columns of a scored screen as a markdown table.

    Args:
        df: scored DataFrame.

    Returns:
        Markdown table string.
    """
    cols = ["layer", "composite", "economics", "valuation", "rev_growth",
            "op_margin", "gm_change_yoy", "fwd_pe", "growth_adj_pe",
            "ev_sales", "mom_12_1", "off_52w_high", "vol_1y", "risk_flag"]
    if "bottleneck" in df:
        cols.insert(1, "bottleneck")
    view = df[cols].copy()
    pct = ["rev_growth", "op_margin", "gm_change_yoy", "mom_12_1",
           "off_52w_high", "vol_1y"]
    for c in pct:
        view[c] = view[c].map(lambda v: "" if pd.isna(v) else f"{v:.0%}")
    for c in ["composite", "economics", "valuation", "fwd_pe",
              "growth_adj_pe", "ev_sales"]:
        view[c] = view[c].map(lambda v: "" if pd.isna(v) else f"{v:.2f}")
    return view.to_markdown()


def main():
    """Parse CLI args, run the screen, and write results/ outputs."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tickers", nargs="+", help="override the universe")
    ap.add_argument("--universe", default=str(UNIVERSE_FILE))
    ap.add_argument("--bottleneck",
                    help="JSON {ticker_or_layer: 1-5} from steps 1-3")
    args = ap.parse_args()

    for d in (DATA_DIR, RESULTS_DIR, LOGS_DIR):
        d.mkdir(exist_ok=True)
    stamp = date.today().isoformat()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGS_DIR / f"screen_{stamp}.log"),
                  logging.StreamHandler()])

    layers = load_universe(args.universe)
    tickers = args.tickers or list(layers)
    bottleneck = (json.loads(Path(args.bottleneck).read_text())
                  if args.bottleneck else None)

    scored = score(run_screen(tickers, layers), bottleneck)
    csv_path = RESULTS_DIR / f"screen_{stamp}.csv"
    md_path = RESULTS_DIR / f"screen_{stamp}.md"
    scored.to_csv(csv_path)
    md_path.write_text(to_markdown(scored) + "\n")
    print(to_markdown(scored))
    print(f"\nSaved {csv_path} and {md_path}")


if __name__ == "__main__":
    main()

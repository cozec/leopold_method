"""Build index.html / index_zh.html: one-page reports of every screening step.

Reads the latest scored screen (results/screen_<date>.csv), the bottleneck
scores (results/bottleneck_scores.json) and the universe (src/universe.json),
and writes self-contained English (index.html) and Chinese (index_zh.html)
reports at the project root. The research narrative for steps 2 and 5 lives in
the constants below, in both languages; update both when the bottleneck scores
are re-researched.

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
OUTPUTS = {"en": "index.html", "zh": "index_zh.html"}

# Step 2 research per layer: score label, evidence, easing signal, sources.
EVIDENCE_KEYS = [
    ("memory", ["wiki", "trendforce", "astute", "marketwise", "hynix2030"]),
    ("power_generation", ["pjm", "gev"]),
    ("foundry_equipment", ["cowos"]),
    ("networking_optics", ["eml"]),
    ("accelerators", ["capex", "creditsights"]),
    ("power_cooling_equipment", ["transformers", "vertiv"]),
    ("datacenter_neocloud", ["gpu"]),
]

EVIDENCE = {
    "en": {
        "memory": (
            "5 (STX/WDC 4)",
            "All three HBM suppliers call 2026 output sold out. HBM3E spot "
            "~$2,100 vs $300–400 on long-term contracts (Sep 4, 2026). "
            "Conventional DRAM contract +93–98% QoQ in Q1 2026. 30TB "
            "enterprise SSD $3.5k → $22.6k (Q3 2025 → Aug 2026).",
            "Samsung / SK Hynix new fabs ramp 2H 2027; consensus turn "
            "2H27–2028. Memory stocks already sold off on oversupply fears."),
        "power_generation": (
            "5 (BE 4)",
            "PJM 2027/28 capacity auction cleared at the $333.44/MW-day cap for "
            "the 2nd year and still fell 6.6 GW short of the reliability "
            "target; ~5.1 GW of the 5.25 GW load growth is data centers. GE "
            "Vernova gas-turbine backlog 116 GW, slots booked to 2030.",
            "Capacity-price cap reform; large new gas/nuclear build coming "
            "online."),
        "foundry_equipment": (
            "4 (TSM 5, ASML 4, tools 3)",
            "TSMC CoWoS-S and CoWoS-L fully booked, 52–78 week lead times; "
            "NVIDIA holds ~60% of capacity; 2026 demand ~1.0M wafers vs ~370k "
            "in 2024.",
            "CoWoS capacity reaching 130–150k wafers/month by end-2026 — watch "
            "for lead times shrinking."),
        "networking_optics": (
            "4 (LITE 5, ANET/ALAB 3)",
            "200G-per-lane EML lasers (needed for 1.6T optics) are the tightest "
            "part of the optical chain; Lumentum is the only volume supplier. "
            "NVIDIA locked up $4B of Lumentum/Coherent laser capacity "
            "(Mar 2026).",
            "InP substrate / epi-wafer capacity additions."),
        "accelerators": (
            "4 (AMD/MRVL 3)",
            "Output gated by CoWoS and HBM. Big-4 hyperscaler 2026 capex "
            "~$725B; Alphabet and Meta raised guidance; 2027 modeled above $1T.",
            "Hyperscaler capex cuts; custom-ASIC share shifts."),
        "power_cooling_equipment": (
            "4",
            "Average US transformer lead time ~128 weeks, 3–5 years for the "
            "largest units. Vertiv backlog $15B, book-to-bill 2.9× (Q4 2025).",
            "Lead times shortening; book-to-bill falling toward 1×."),
        "datacenter_neocloud": (
            "2 (EQIX/DLR 3)",
            "H100 rents ~$3.84/GPU-hr on average (Sep 2026) and prices fell "
            "after Blackwell shipped. GPUs are no longer the scarce input — "
            "capital is.",
            "Already commoditizing."),
    },
    "zh": {
        "memory": (
            "5（STX/WDC 4）",
            "三大 HBM 供应商均表示 2026 年产能已售罄。HBM3E 现货约 2,100 美元，"
            "长约价仅 300–400 美元（2026 年 9 月 4 日）。2026 年一季度常规 DRAM "
            "合约价环比上涨 93–98%。30TB 企业级 SSD 从 3,460 美元涨至约 22,600 "
            "美元（2025 年三季度 → 2026 年 8 月）。",
            "三星 / SK 海力士新晶圆厂 2027 年下半年投产；市场共识拐点在 2027 年"
            "下半年至 2028 年。存储股已因供过于求担忧而回调。"),
        "power_generation": (
            "5（BE 4）",
            "PJM 2027/28 容量拍卖连续第二年触及 333.44 美元/兆瓦·日的价格上限，"
            "仍比可靠性目标少 6.6 GW；5.25 GW 负荷增长中约 5.1 GW 来自数据中心。"
            "GE Vernova 燃气轮机积压订单 116 GW，交付排期已到 2030 年。",
            "容量价格上限改革；大量新建燃气 / 核电产能投运。"),
        "foundry_equipment": (
            "4（TSM 5，ASML 4，设备商 3）",
            "台积电 CoWoS-S 与 CoWoS-L 产能全部订满，交期 52–78 周；英伟达占约 "
            "60% 产能；2026 年需求约 100 万片晶圆，2024 年约 37 万片。",
            "CoWoS 产能到 2026 年底达每月 13–15 万片——关注交期是否缩短。"),
        "networking_optics": (
            "4（LITE 5，ANET/ALAB 3）",
            "单通道 200G EML 激光器（1.6T 光模块所需）是光通信链中最紧缺的环节；"
            "Lumentum 是唯一量产供应商。英伟达于 2026 年 3 月锁定 Lumentum / "
            "Coherent 共 40 亿美元激光器产能。",
            "磷化铟衬底 / 外延片产能扩张。"),
        "accelerators": (
            "4（AMD/MRVL 3）",
            "产量受 CoWoS 与 HBM 制约。四大云厂商 2026 年资本开支约 7,250 亿美元；"
            "Alphabet 与 Meta 上调指引；2027 年预测超过 1 万亿美元。",
            "云厂商削减资本开支；定制 ASIC 份额变化。"),
        "power_cooling_equipment": (
            "4",
            "美国变压器平均交期约 128 周，最大型号 3–5 年。Vertiv 积压订单 "
            "150 亿美元，订单出货比 2.9 倍（2025 年四季度）。",
            "交期缩短；订单出货比回落至 1 倍附近。"),
        "datacenter_neocloud": (
            "2（EQIX/DLR 3）",
            "H100 平均租金约 3.84 美元/GPU·小时（2026 年 9 月），Blackwell "
            "出货后价格下跌。GPU 已不再是稀缺要素——资本才是。",
            "已在商品化。"),
    },
}

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
PRICED_IN = {
    "en": [
        ("MU · Samsung · SK Hynix · SNDK", "Memory — cheap on peak earnings",
         "4–7× forward P/E vs ~12–15× mid-cycle: the market already assumes "
         "peak earnings roughly halve after ~2 years, i.e. it prices the turn "
         "for 2H27–2028 — exactly when new Korean fabs ramp. Upside needs the "
         "shortage to outlast 2028 (SK Hynix's CEO says past 2030). 12-1 "
         "momentum of +245% to +1,280% shows how much has already run.",
         "DRAM/HBM contract prices fall QoQ, or 2027 hyperscaler capex is "
         "cut."),
        ("TSM", "Sole CoWoS supplier at a normal multiple",
         "~21× forward — not a cyclical discount, and only 4% off its 52-week "
         "high. Priced as a durable compounder rather than a scarcity "
         "windfall.",
         "CoWoS doubling outruns demand (lead times shrink); Taiwan "
         "geopolitics."),
        ("VST", "Contrarian: bottleneck not yet in reported numbers",
         "Bottleneck 5 and cheap (13× forward, −34% off high, −30% momentum), "
         "but the economics score is weak (revenue −6%). Scarcity shows in "
         "PJM capacity prices that flow into earnings from 2026/27 onward.",
         "Capacity-price cap reform, or a wave of new gas supply."),
    ],
    "zh": [
        ("MU · 三星 · SK 海力士 · SNDK", "存储——按峰值盈利看很便宜",
         "远期市盈率 4–7 倍，而周期中值约 12–15 倍：市场已假设峰值盈利约两年后"
         "腰斩，即已计入 2027 年下半年至 2028 年的周期拐点——恰好是韩国新厂投产"
         "的时间。要获得超额收益，短缺必须持续到 2028 年以后（SK 海力士 CEO "
         "称将持续到 2030 年以后）。12-1 动量 +245% 至 +1,280%，说明股价已大幅"
         "上涨。",
         "DRAM/HBM 合约价环比下跌，或 2027 年云厂商削减资本开支。"),
        ("TSM", "唯一的 CoWoS 供应商，估值正常",
         "远期市盈率约 21 倍——没有周期折价，距 52 周高点仅 4%。市场把它当作"
         "长期复利股定价，而非稀缺带来的一次性暴利。",
         "CoWoS 产能翻倍超过需求（交期缩短）；台海地缘风险。"),
        ("VST", "逆向选择：瓶颈尚未反映在财报中",
         "瓶颈评分 5 且估值便宜（远期 13 倍，距高点 −34%，动量 −30%），但经济性"
         "评分偏弱（营收 −6%）。稀缺体现在 PJM 容量价格上，将从 2026/27 年起"
         "逐步计入盈利。",
         "容量价格上限改革，或大量新增燃气发电供给。"),
    ],
}

LAYER_LABEL = {
    "en": {
        "accelerators": "Accelerators",
        "memory": "HBM / memory",
        "foundry_equipment": "Foundry & equipment",
        "networking_optics": "Networking & optics",
        "datacenter_neocloud": "Data centers / neocloud",
        "power_generation": "Power generation",
        "power_cooling_equipment": "Power & cooling equipment",
    },
    "zh": {
        "accelerators": "加速器",
        "memory": "HBM / 存储",
        "foundry_equipment": "晶圆代工与设备",
        "networking_optics": "网络与光通信",
        "datacenter_neocloud": "数据中心 / 新型云",
        "power_generation": "发电",
        "power_cooling_equipment": "电力与冷却设备",
    },
}

# Chinese versions of universe.json text (English comes from the file).
UNIVERSE_ZH = {
    "thesis": "AI 能力持续扩张；其背后的实体供应链会率先出现稀缺。",
    "chain": ["AI 模型", "加速器", "HBM / 存储", "网络", "数据中心", "电力",
              "冷却 / 电力设备"],
    "bottleneck": {
        "accelerators": "GPU/ASIC 供应与 CoWoS 封装产能",
        "memory": "HBM/DRAM/NAND 产能；供应商少，建厂周期长",
        "foundry_equipment": "先进制程晶圆与先进封装产能",
        "networking_optics": "高速互连、光模块、重定时器",
        "datacenter_neocloud": "已通电、已获批的数据中心机房与 GPU 云产能",
        "power_generation": "电网并网排队；稳定、可调度的电力",
        "power_cooling_equipment": "变压器、开关柜、液冷、电网建设劳动力",
    },
}

TEXT = {
    "en": {
        "lang": "en", "title": "Leopold Bottleneck Screen",
        "h1": "Leopold bottleneck screen",
        "switch": '<a href="index_zh.html">中文</a>',
        "intro": ("AI-infrastructure stock screen in the style of Leopold "
                  "Aschenbrenner's <em>Situational Awareness</em>. Run date "
                  "{date} · {n} tickers · 7 layers · Top 5: "),
        "steps": [("1. Mega-trend", "What could grow 5–10×?"),
                  ("2. Bottleneck", "What scarce resource limits it?"),
                  ("3. Supplier", "Who controls that bottleneck?"),
                  ("4. Economics", "Is scarcity showing up as pricing power?"),
                  ("5. Valuation", "Has the market already priced it in?")],
        "h_trend": "Mega-trend",
        "trend_tail": ("Don't buy the famous AI name; follow the physical "
                       "supply chain and find where it runs out of something."),
        "h_bneck": "Bottleneck — how scarce is each layer?",
        "bneck_sub": ("Scored 1–5 from web research dated September 2026 "
                      "(5 = acute scarcity, few suppliers, rising prices). "
                      "Ticker overrides shown in the label column. The "
                      '"easing" column is the exit signal.'),
        "bneck_cols": ["Layer", "Score", "Overrides", "Evidence",
                       "Easing signal to watch"],
        "h_supplier": "Supplier — who controls it?",
        "supplier_sub": "Universe from <code>src/universe.json</code>.",
        "h_quant": "Economics &amp; valuation — the quant screen",
        "method": (
            "<b>Economics</b> = mean percentile rank of revenue growth, EPS "
            "growth, operating margin and YoY gross-margin change (margin "
            "expansion = pricing power).<br><b>Valuation</b> = mean inverse "
            "rank of forward P/E, PEG, EV/Sales and growth-adjusted P/E (fwd "
            "P/E ÷ fwd EPS growth %); loss-makers rank worst.<br>"
            "<b>Composite</b> = 0.4 × bottleneck (scaled 0–1) + 0.3 × "
            "economics + 0.3 × valuation.<br><b>Risk = HIGH</b> when 1-year "
            "volatility &gt; 70% or 1-year max drawdown worse than −50%."),
        "data_note": ("Data: yfinance fundamentals + 2y daily prices, pulled "
                      "{date}. Blank P/E-type cells are loss-makers or "
                      "missing data."),
        "cols": ["#", "Ticker", "Layer", "Bottleneck", "Composite",
                 "Economics", "Valuation", "Rev growth", "Op margin",
                 "GM Δ YoY", "Fwd P/E", "Growth-adj P/E", "EV/Sales",
                 "12-1 mom", "Off 52w high", "1y vol", "Risk"],
        "high": "HIGH",
        "h_priced": "Priced in? — judging the finalists",
        "breaks": "Thesis breaks if:",
        "h_risk": "Risk",
        "risk1": ("The top four are all memory and all flagged HIGH risk (1y "
                  "vol 75–116%). They move together, so together they are one "
                  "bet on one cycle. The July 2026 AI-semis selloff hit this "
                  "exact book hard. Size positions accordingly; this page does "
                  "not suggest leverage or options."),
        "risk2": ("Yahoo data can be stale or wrong: Korean tickers mix "
                  "currencies and lack growth-adjusted P/E, and EV/Sales above "
                  "200× is dropped as an artifact (ASML). Verify anything that "
                  "drives a top pick against company filings."),
        "h_sources": "Sources",
        "footer": ("Research only, not financial advice. Generated by "
                   "<code>src/build_report.py</code> from <code>{csv}</code>."),
    },
    "zh": {
        "lang": "zh-CN", "title": "Leopold 瓶颈选股",
        "h1": "Leopold 瓶颈选股筛选",
        "switch": '<a href="index.html">English</a>',
        "intro": ("仿照 Leopold Aschenbrenner《Situational Awareness》思路的 AI "
                  "基础设施选股筛选。运行日期 {date} · {n} 只股票 · 7 个层级 · "
                  "前五名："),
        "steps": [("1. 大趋势", "什么技术可能增长 5–10 倍？"),
                  ("2. 瓶颈", "什么稀缺资源限制了增长？"),
                  ("3. 供应商", "谁控制着这个瓶颈？"),
                  ("4. 经济性", "稀缺是否体现为定价权？"),
                  ("5. 估值", "市场是否已经计入了增长？")],
        "h_trend": "大趋势",
        "trend_tail": "不要买最出名的 AI 公司；沿着实体供应链，找出最先短缺的环节。",
        "h_bneck": "瓶颈——每一层有多稀缺？",
        "bneck_sub": ("根据 2026 年 9 月的网络调研按 1–5 打分（5 = 严重短缺、"
                      "供应商少、价格上涨）。“个股调整”列显示覆盖层级分数的个股"
                      "分数；“缓解信号”列即退出信号。"),
        "bneck_cols": ["层级", "分数", "个股调整", "证据", "需关注的缓解信号"],
        "h_supplier": "供应商——谁控制瓶颈？",
        "supplier_sub": "股票池来自 <code>src/universe.json</code>。",
        "h_quant": "经济性与估值——量化筛选",
        "method": (
            "<b>经济性</b> = 营收增长、EPS 增长、营业利润率、毛利率同比变化的"
            "百分位排名均值（毛利率扩张 = 定价权）。<br><b>估值</b> = 远期市盈率、"
            "PEG、企业价值/销售额、增长调整市盈率（远期市盈率 ÷ 远期 EPS 增长率%）"
            "的反向排名均值；亏损公司排名最差。<br><b>综合分</b> = 0.4 × 瓶颈"
            "（归一化到 0–1）+ 0.3 × 经济性 + 0.3 × 估值。<br><b>风险 = 高</b>："
            "1 年波动率 &gt; 70% 或 1 年最大回撤超过 −50%。"),
        "data_note": ("数据：yfinance 基本面 + 2 年日线价格，获取于 {date}。"
                      "市盈率类空白表示亏损或数据缺失。"),
        "cols": ["#", "代码", "层级", "瓶颈", "综合", "经济性", "估值",
                 "营收增长", "营业利润率", "毛利率同比", "远期市盈率",
                 "增长调整市盈率", "EV/销售额", "12-1 动量", "距 52 周高点",
                 "1 年波动率", "风险"],
        "high": "高",
        "h_priced": "是否已计入价格？——评估入围股票",
        "breaks": "论点失效条件：",
        "h_risk": "风险",
        "risk1": ("前四名全部是存储股，且均被标记为高风险（1 年波动率 75–116%）。"
                  "它们高度同涨同跌，合起来就是押注同一个周期。2026 年 7 月 AI "
                  "半导体抛售正是重创了这一组合。请据此控制仓位；本页不建议使用"
                  "杠杆或期权。"),
        "risk2": ("Yahoo 数据可能过时或有误：韩国股票混用币种且缺少增长调整市盈率；"
                  "EV/销售额超过 200 倍视为数据错误并剔除（ASML）。任何影响前几名"
                  "的数据都应以公司财报核实。"),
        "h_sources": "资料来源",
        "footer": ("仅供研究，不构成投资建议。由 <code>src/build_report.py</code> "
                   "根据 <code>{csv}</code> 生成。"),
    },
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
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,"PingFang SC",
"Hiragino Sans GB","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 64px}
.lang{float:right;font-size:.9rem;margin-top:10px}
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


def results_table(df, lang):
    """Build the full scored-screen table (steps 4–5).

    Args:
        df: scored screen DataFrame, sorted by composite.
        lang: "en" or "zh".

    Returns:
        HTML string for the table.
    """
    t = TEXT[lang]
    labels = LAYER_LABEL[lang]
    head = "<tr>" + "".join(
        f"<th class='l'>{c}</th>" if i in (1, 2) else f"<th>{c}</th>"
        for i, c in enumerate(t["cols"])) + "</tr>"
    rows = []
    for i, (tk, r) in enumerate(df.iterrows(), 1):
        cls = ' class="top"' if i <= 5 else ""
        risk = t["high"] if r["risk_flag"] == "HIGH" else ""
        rows.append(
            f"<tr{cls}><td>{i}</td><td class='l' title='{esc(r['name'])}'>"
            f"{esc(tk)}</td><td class='l'>{esc(labels.get(r['layer'], r['layer']))}</td>"
            f"<td>{dots(r.get('bottleneck'))}</td><td>{bar(r['composite'])}</td>"
            f"<td>{bar(r['economics'])}</td><td>{bar(r['valuation'])}</td>"
            f"<td>{pct(r['rev_growth'])}</td><td>{pct(r['op_margin'])}</td>"
            f"<td>{pct(r['gm_change_yoy'], True)}</td><td>{num(r['fwd_pe'])}</td>"
            f"<td>{num(r['growth_adj_pe'], '{:.2f}')}</td><td>{num(r['ev_sales'])}</td>"
            f"<td>{pct(r['mom_12_1'], True)}</td><td>{pct(r['off_52w_high'], True)}</td>"
            f"<td>{pct(r['vol_1y'])}</td><td class='flag'>{risk}</td></tr>")
    return f"<div class='tw'><table>{head}{''.join(rows)}</table></div>"


def build(csv_path, lang="en"):
    """Assemble the full HTML report and return it as a string.

    Args:
        csv_path: path to a scored screen CSV from leopold_screen.py.
        lang: "en" or "zh".

    Returns:
        HTML document string.
    """
    t = TEXT[lang]
    labels = LAYER_LABEL[lang]
    date = csv_path.stem.replace("screen_", "")
    df = pd.read_csv(csv_path, index_col=0)
    universe = json.loads((ROOT / "src" / "universe.json").read_text())
    scores = json.loads(
        (ROOT / "results" / "bottleneck_scores.json").read_text())

    if lang == "zh":
        thesis, links = UNIVERSE_ZH["thesis"], UNIVERSE_ZH["chain"]
        bneck_desc = UNIVERSE_ZH["bottleneck"]
    else:
        thesis = universe["thesis"]
        links = [s.strip() for s in universe["chain"].split("->")]
        bneck_desc = {k: v["bottleneck"]
                      for k, v in universe["layers"].items()}

    src_ids = {k: i for i, k in enumerate(SOURCES, 1)}
    chain = " <i>→</i> ".join(f"<span>{esc(s)}</span>" for s in links)

    ev_rows = ""
    for layer, keys in EVIDENCE_KEYS:
        label, ev, ease = EVIDENCE[lang][layer]
        refs = "".join(
            f"<sup><a href='#s{src_ids[k]}'>[{src_ids[k]}]</a></sup>"
            for k in keys)
        ev_rows += (
            f"<tr><td class='l'>{esc(labels[layer])}</td>"
            f"<td>{dots(scores.get(layer))}</td><td class='l'>{esc(label)}</td>"
            f"<td class='w'>{esc(ev)} {refs}</td>"
            f"<td class='w'>{esc(ease)}</td></tr>")
    ev_head = "".join(
        f"<th>{c}</th>" if i == 1 else f"<th class='l'>{c}</th>"
        for i, c in enumerate(t["bneck_cols"]))

    uni_cards = "".join(
        f"<div class='card'><strong>{esc(labels[k])}</strong>"
        f"<div class='sub' style='margin:4px 0 8px'>{esc(bneck_desc[k])}</div>"
        f"<code>{' · '.join(esc(x) for x in v['tickers'])}</code></div>"
        for k, v in universe["layers"].items())

    step_cards = "".join(
        f'<div class="card"><strong>{esc(a)}</strong><br>{esc(b)}</div>'
        for a, b in t["steps"])

    priced = "".join(
        f"<div class='card'><div class='sub' style='margin:0'>{esc(tk)}</div>"
        f"<strong>{esc(h)}</strong><p>{esc(p)}</p>"
        f"<p><b>{t['breaks']}</b> {esc(b)}</p></div>"
        for tk, h, p, b in PRICED_IN[lang])

    sources = "".join(
        f"<li id='s{i}'><a href='{esc(u)}'>{esc(n)}</a></li>"
        for i, (n, u) in enumerate(SOURCES.values(), 1))

    top = ", ".join(df.head(5).index.tolist())
    intro = t["intro"].format(date=esc(date), n=len(df))
    return f"""<!doctype html>
<html lang="{t['lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title><style>{CSS}</style></head>
<body><main>
<div class="lang">{t['switch']}</div>
<h1>{t['h1']}</h1>
<p class="sub">{intro}<strong>{esc(top)}</strong></p>

<div class="grid">{step_cards}</div>

<h2><span class="n">1</span>{t['h_trend']}</h2>
<p>{esc(thesis)} {t['trend_tail']}</p>
<div class="chain">{chain}</div>

<h2><span class="n">2</span>{t['h_bneck']}</h2>
<p class="sub">{t['bneck_sub']}</p>
<div class="tw"><table><tr>{ev_head}</tr>{ev_rows}</table></div>

<h2><span class="n">3</span>{t['h_supplier']}</h2>
<p class="sub">{t['supplier_sub']}</p>
<div class="grid">{uni_cards}</div>

<h2><span class="n">4–5</span>{t['h_quant']}</h2>
<div class="card">
<p style="margin-top:0">{t['method']}</p>
<p style="margin-bottom:0" class="sub">{t['data_note'].format(date=esc(date))}</p></div>
<p></p>
{results_table(df, lang)}

<h2><span class="n">5</span>{t['h_priced']}</h2>
<div class="grid">{priced}</div>

<h2>{t['h_risk']}</h2>
<div class="card warn">
<p style="margin-top:0">{t['risk1']}</p>
<p style="margin-bottom:0">{t['risk2']}</p></div>

<h2>{t['h_sources']}</h2><ol class="src">{sources}</ol>

<footer>{t['footer'].format(csv=esc(csv_path.name))}</footer>
</main></body></html>
"""


def main():
    """Parse CLI args and write the English and Chinese reports."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, help="scored screen CSV")
    args = ap.parse_args()
    csv_path = args.csv or max((ROOT / "results").glob("screen_*.csv"))
    for lang, name in OUTPUTS.items():
        out = ROOT / name
        out.write_text(build(csv_path, lang))
        print(f"wrote {out}")


if __name__ == "__main__":
    main()

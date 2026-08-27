#!/usr/bin/env python3
"""Write the two published chart SVGs from the v4 tabulated values.

The checked-in files in charts/ are the figures used in the article.
This script rebuilds them from the same numbers. It does not invent a
crossover between 128K and 256K; those two points are plotted as measured.

Usage:
  python3 analysis/plot_charts.py --out charts
"""
from __future__ import annotations

import argparse
from pathlib import Path

# Headline BF16 arm, from summaries/sweep_summary_v4.md
CONTEXTS = [2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144]
LABELS = ["2K", "4K", "8K", "16K", "32K", "64K", "128K", "256K"]
TRUE_PEAK = [311, 155, 77, 38, 19, 9, 4, 2]
BOOT_CEILING = [311.02, 155.51, 77.76, 38.88, 19.44, 9.72, 4.86, 2.43]
TOTAL_TPS = [19089.8, 18812.3, 17933.2, 16214.8, 13929.6, 11048.2, 7988.2, 4967.2]
HOURLY_RATE = 4.47
PIN = 512


def cost_per_million(tps: float, util: float = 1.0) -> float:
    return HOURLY_RATE / (tps * 3600.0 * util) * 1e6


def log2(x: float) -> float:
    import math
    return math.log(x, 2)


def x_of(ctx: int) -> float:
    return 80.0 + (log2(ctx) - log2(2048)) / 7.0 * 780.0


def y_conc(c: float) -> float:
    return 60.0 + (log2(PIN) - log2(c)) / 9.0 * 390.0


def y_cost(dollars: float) -> float:
    # $0 at y=450, $0.30 at y=60 (linear in dollars, matching published SVG)
    return 450.0 - (dollars / 0.30) * 390.0


def concurrency_svg() -> str:
    xs = [x_of(c) for c in CONTEXTS]
    y_true = [y_conc(v) for v in TRUE_PEAK]
    y_boot = [y_conc(v) for v in BOOT_CEILING]
    pts_true = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, y_true))
    pts_boot = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, y_boot))
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#0069ff"/>'
        for x, y in zip(xs, y_true)
    )
    xticks = []
    for x, lab in zip(xs, LABELS):
        xticks.append(
            f'<line x1="{x:.1f}" y1="450" x2="{x:.1f}" y2="456" stroke="#374151" stroke-width="1"/>\n'
            f'<text x="{x:.1f}" y="474" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="12" fill="#111827">{lab}</text>'
        )
    yticks = []
    for exp, y in ((9, 60.0), (8, 103.3), (7, 146.7), (6, 190.0), (5, 233.3),
                   (4, 276.7), (3, 320.0), (2, 363.3), (1, 406.7), (0, 450.0)):
        yticks.append(
            f'<line x1="80" y1="{y}" x2="860" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>\n'
            f'<text x="70" y="{y + 4:.1f}" text-anchor="end" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="11" fill="#374151">{2 ** exp}</text>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520" role="img" aria-labelledby="chartTitle chartDesc">
  <title id="chartTitle">Concurrent requests the KV cache pool holds versus context length</title>
  <desc id="chartDesc">Measured sustained concurrency falls from 311 requests at 2K tokens of context to 2 requests at 256K tokens, plotted on a log base 2 vertical axis against context length on a log base 2 horizontal axis. A dashed reference line shows the continuous pool-divided-by-context ratio before flooring to whole requests. The scheduler pin at 512 concurrent requests is marked at the top of the chart and sits above every measured point, confirming the KV cache pool rather than the scheduler set batch size throughout the sweep.</desc>
  <rect width="900" height="520" fill="#ffffff"/>
  <text x="450.0" y="28" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="16" font-weight="600" fill="#111827">Concurrent requests held by the KV cache pool vs context length</text>
  <text x="450.0" y="48" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#4b5563">Ministral 3 14B Instruct BF16 on H200 · vLLM 0.27.1 · measured vs continuous pool / context</text>
{''.join(yticks)}
  <line x1="80" y1="60" x2="80" y2="450" stroke="#111827" stroke-width="1.5"/>
  <line x1="80" y1="450" x2="860" y2="450" stroke="#111827" stroke-width="1.5"/>
{''.join(xticks)}
  <text x="470.0" y="502" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#111827">Context length (tokens, log&#8322; scale)</text>
  <text x="22" y="255.0" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#111827" transform="rotate(-90 22 255.0)">Concurrent requests (log&#8322; scale)</text>
  <line x1="80" y1="60.0" x2="860" y2="60.0" stroke="#b45309" stroke-width="1.8" stroke-dasharray="3,4"/>
  <polyline fill="none" stroke="#6b7280" stroke-width="1.8" stroke-dasharray="7,5" points="{pts_boot}"/>
  <polyline fill="none" stroke="#0069ff" stroke-width="2.4" points="{pts_true}"/>
  {circles}
  <!-- legend -->
  <rect x="112" y="326" width="360" height="72" fill="#ffffff" fill-opacity="0.92" stroke="#e5e7eb"/>
  <line x1="124" y1="344" x2="154" y2="344" stroke="#0069ff" stroke-width="2.4"/>
  <circle cx="139" cy="344" r="3.5" fill="#0069ff"/>
  <text x="164" y="348" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">Measured sustained concurrency (floored)</text>
  <line x1="124" y1="364" x2="154" y2="364" stroke="#6b7280" stroke-width="1.8" stroke-dasharray="7,5"/>
  <text x="164" y="368" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">Continuous pool / context (before flooring)</text>
  <line x1="124" y1="384" x2="154" y2="384" stroke="#b45309" stroke-width="1.8" stroke-dasharray="3,4"/>
  <text x="164" y="388" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">--max-num-seqs pin (512)</text>
</svg>
'''


def cost_svg() -> str:
    xs = [x_of(c) for c in CONTEXTS]
    costs = [cost_per_million(t) for t in TOTAL_TPS]
    ys = [y_cost(c) for c in costs]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#0069ff"/>'
        for x, y in zip(xs, ys)
    )
    y_flat = y_cost(costs[0])
    y_srv = y_cost(0.20)
    xticks = []
    for x, lab in zip(xs, LABELS):
        xticks.append(
            f'<line x1="{x:.1f}" y1="450" x2="{x:.1f}" y2="456" stroke="#374151" stroke-width="1"/>\n'
            f'<text x="{x:.1f}" y="474" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="12" fill="#111827">{lab}</text>'
        )
    yticks = []
    for dollars in (0.05, 0.10, 0.15, 0.20, 0.25):
        y = y_cost(dollars)
        yticks.append(
            f'<line x1="80" y1="{y:.1f}" x2="860" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1"/>\n'
            f'<text x="70" y="{y + 4:.1f}" text-anchor="end" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="11" fill="#374151">${dollars:.2f}</text>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520">
  <rect width="900" height="520" fill="#ffffff"/>
  <text x="450.0" y="28" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="16" font-weight="600" fill="#111827">Effective cost-per-token vs context length</text>
  <text x="450.0" y="48" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#4b5563">Ministral 3 14B Instruct BF16 on H200 · vLLM 0.27.1 · 100% utilization</text>
{''.join(yticks)}
  <line x1="80" y1="60" x2="80" y2="450" stroke="#111827" stroke-width="1.5"/>
  <line x1="80" y1="450" x2="860" y2="450" stroke="#111827" stroke-width="1.5"/>
{''.join(xticks)}
  <text x="470.0" y="502" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#111827">Context length (tokens, log₂ scale)</text>
  <text x="22" y="255.0" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#111827" transform="rotate(-90 22 255.0)">Effective cost per 1M total tokens ($)</text>
  <line x1="80.0" y1="{y_flat:.1f}" x2="860.0" y2="{y_flat:.1f}" stroke="#6b7280" stroke-width="1.8" stroke-dasharray="7,5"/>
  <line x1="80" y1="{y_srv:.1f}" x2="860" y2="{y_srv:.1f}" stroke="#b45309" stroke-width="1.5" stroke-dasharray="3,4"/>
  <polyline fill="none" stroke="#0069ff" stroke-width="2.4" points="{pts}"/>
  {circles}
  <!-- legend -->
  <rect x="92" y="72" width="340" height="72" fill="#ffffff" fill-opacity="0.92" stroke="#e5e7eb"/>
  <line x1="104" y1="90" x2="134" y2="90" stroke="#0069ff" stroke-width="2.4"/>
  <circle cx="119" cy="90" r="3.5" fill="#0069ff"/>
  <text x="144" y="94" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">Measured effective cost/1M (100% util)</text>
  <line x1="104" y1="110" x2="134" y2="110" stroke="#6b7280" stroke-width="1.8" stroke-dasharray="7,5"/>
  <text x="144" y="114" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">Flat reference held at 2K ($0.0650/1M)</text>
  <line x1="104" y1="130" x2="134" y2="130" stroke="#b45309" stroke-width="1.5" stroke-dasharray="3,4"/>
  <text x="144" y="134" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#111827">Serverless $0.20/1M</text>
</svg>
'''


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("charts"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "does-context-length-concurrency-collapse-v5.svg").write_text(concurrency_svg())
    (args.out / "does-context-length-cost-curve-v4.svg").write_text(cost_svg())
    print(f"wrote {args.out / 'does-context-length-concurrency-collapse-v5.svg'}")
    print(f"wrote {args.out / 'does-context-length-cost-curve-v4.svg'}")


if __name__ == "__main__":
    main()

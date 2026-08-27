#!/usr/bin/env python3
"""Peak concurrency from a vLLM --save-detailed JSON.

vLLM bench serve writes max_concurrent_requests as a whole-second bucket
count. That field over-reported by up to 23 requests at 2K in this sweep.
The article uses this interval overlap instead: each request occupies
[start, start + ttft + sum(itls)].

Usage:
  python3 analysis/true_concurrency.py data/run-A-short-context/bench_2048_trial1.json
  python3 analysis/true_concurrency.py data/run-A-short-context/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def peak_concurrency(path: Path) -> tuple[int | None, int | None]:
    d = json.loads(path.read_text())
    reported = d.get("max_concurrent_requests")
    starts = d.get("start_times") or []
    ttfts = d.get("ttfts") or []
    itls = d.get("itls") or []
    if not starts or len(starts) != len(ttfts):
        return None, reported

    events = []
    for i, start in enumerate(starts):
        total_itl = sum(itls[i]) if i < len(itls) and itls[i] else 0.0
        end = start + ttfts[i] + total_itl
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda e: (e[0], e[1]))

    concurrent = 0
    peak = 0
    for _, delta in events:
        concurrent += delta
        peak = max(peak, concurrent)
    return peak, reported


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    target = Path(argv[1])
    files = sorted(target.glob("bench_*_trial*.json")) if target.is_dir() else [target]
    if not files:
        print(f"no bench JSON under {target}", file=sys.stderr)
        return 1
    print("file\ttrue_peak\tvllm_reported")
    for path in files:
        true_peak, reported = peak_concurrency(path)
        print(f"{path}\t{true_peak}\t{reported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

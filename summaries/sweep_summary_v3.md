# MKTG-3270 Sweep Summary v3

> **Superseded.** The published article and the headline tables in this repository use `sweep_summary_v4.md`. This file is kept so the bug history is auditable.


Generated at consolidation after the v3 correction pass (2026-08-26 15:31 UTC). Maps fillable
`[[SLOT: ...]]` values in `does-context-length-affect-inference-cost-linearly.md` to
measured values. **Does not edit the article.** Preserves `sweep_summary.md` (v1) and
`sweep_summary_v2.md` (v2).

Source trees: `run-A-short-context/`, `run-B-long-context/`, `run-C-fp8-sensitivity/`.

---

## What changed vs v2

| Fix | Result in this pass |
| --- | --- |
| **C weight checkpoint** | C now loads `mistralai/Ministral-3-14B-Instruct-2512-BF16` with `--kv-cache-dtype fp8` and `--attention-backend FLASHINFER`. Startup confirms `quantization=None`, `dtype=torch.bfloat16`, `kv_cache_dtype=fp8`, and `Using AttentionBackendEnum.FLASHINFER backend.` **All prior C data (v1 + v2) used the FP8 weight checkpoint and is invalid for the sensitivity arm — not merged here.** |
| **B/128K trial count** | Diagnosis: trial 3 hit the 45-min point deadline mid-bench (`1/50` in stdout). Trials 1–2 valid. Fix: append-only trial 3 via harness → **3/3**. |
| **256K timeout** | Extended to **3.5 h** per point. B/256K append trials 2–3 completed → **3/3**. C/256K full re-run → **3/3**. |
| **Carry-forward** | Droplet A (all points) and B 32K/64K unchanged from v2 (clean 3/3). B 128K/256K and all C points are new v3 work. |

---

## Run metadata

| Field | Value |
| --- | --- |
| Benchmark run date | 2026-08-26 (v3 pass started ~11:00 UTC; consolidation ~15:30 UTC) |
| vLLM | 0.27.1 |
| FlashInfer | 0.6.16.post4 |
| Headline model (A/B) | `mistralai/Ministral-3-14B-Instruct-2512-BF16` (`quantization=None`, `dtype=torch.bfloat16`) |
| FP8-KV sensitivity model (C) | Same BF16 repo + `--kv-cache-dtype fp8` (weights BF16; KV stored fp8) |
| Attention (headline A/B) | `FLASH_ATTN` (auto) |
| Attention (C) | `FLASHINFER` (forced; gate-confirmed in startup log) |
| `--gpu-memory-utilization` | 0.90 |
| Fixed output length | 256 |
| Warm-up | Separate 10-request invocation before each trial; discarded |
| Trials | 3 per point (all cells 3/3 in this summary) |
| 256K point timeout (v3) | 3.5 hours |
| Whole-run backstop (v3) | 8 hours from 2026-08-26 11:00 UTC |
| BF16 weight footprint | ≈26.66 GiB (weights + non-torch), from startup `gpu_worker` line |
| Droplet size / rate | `gpu-h200x1-141gb` @ **$4.47/hr** each |

---

## Droplet A — BF16 headline, 2K–16K (carried from v2, all 3/3)

KV pool **636,976** tokens at every context.

| Context | KV pool | Max concurrency (boot) | Max concurrent observed | Preemptions |
| --- | --- | --- | --- | --- |
| 2K | 636,976 | 311.02x | 91 / 87 / 91 | 0 |
| 4K | 636,976 | 155.51x | 71 / 71 / 71 | 0 |
| 8K | 636,976 | 77.76x | 68 / 68 / 68 | 0 |
| 16K | 636,976 | 38.88x | 40 / 40 / 40 | 0 |

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms | num-prompts |
| --- | --- | --- | --- | --- | --- |
| 2K | 14813.2 ± 10.2 | 1851.7 ± 1.3 | 1350.1 ± 1.0 | 4725.8 ± 21.5 | 141 |
| 4K | 16714.8 ± 20.1 | 1044.7 ± 1.3 | 1414.5 ± 0.3 | 10448.7 ± 25.7 | 139 |
| 8K | 17203.7 ± 13.5 | 537.6 ± 0.4 | 7509.1 ± 12.0 | 23170.0 ± 35.3 | 88 |
| 16K | 15992.3 ± 5.5 | 249.9 ± 0.1 | 1678.4 ± 0.8 | 30586.4 ± 12.8 | 88 |

---

## Droplet B — BF16 headline, 32K–256K

| Context | Status | Trials ok | Notes |
| --- | --- | --- | --- |
| 32K | complete (v2 carry) | 3/3 | |
| 64K | complete (v2 carry) | 3/3 | |
| 128K | complete (v3 top-up) | 3/3 | Trial 3 appended after 45-min deadline kill in v2 |
| 256K | complete (v3 append) | 3/3 | Trials 2–3 appended under 3.5 h budget; trial 1 from v2 retained |

| Context | KV pool | Max concurrency (boot) | Max concurrent observed | Preemptions |
| --- | --- | --- | --- | --- |
| 32K | 636,976 | 19.44x | 20 / 20 / 20 | 0 |
| 64K | 636,976 | 9.72x | 10 / 10 / 10 | 0 |
| 128K | 636,976 | 4.86x | 5 / 5 / 5 | 0 |
| 256K | 636,976 | 2.43x | 3 / 3 / 3 | 0 |

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms | num-prompts |
| --- | --- | --- | --- | --- | --- |
| 32K | 13870.6 ± 1.5 | 108.4 ± 0.0 | 3095.7 ± 0.8 | 35716.5 ± 29.8 | 50 |
| 64K | 11033.8 ± 4.9 | 43.1 ± 0.0 | 8220.8 ± 4.6 | 42838.2 ± 85.3 | 50 |
| 128K | 7988.2 ± 2.8 | 15.6 ± 0.0 | 22721.4 ± 5.1 | 51946.5 ± 56.7 | 50 |
| 256K | 4967.2 ± 1.5 | 4.9 ± 0.0 | 63648.1 ± 51.4 | 92645.2 ± 668.1 | 50 |

---

## Droplet C — BF16 weights + FP8 KV sensitivity (FlashInfer gated, v3 only)

**Invalid for comparison:** all C results from v1 and v2 (FP8 weight checkpoint). This section uses v3 artifacts only.

FP8 KV doubles the KV token pool vs BF16 KV at the same `gpu-memory-utilization`: **1,273,968** vs **636,976** tokens.

| Context | FlashInfer confirmed? | KV pool / max conc (boot) | Trials |
| --- | --- | --- | --- |
| 128K | **Yes** — `Using AttentionBackendEnum.FLASHINFER backend.` | 1,273,968 / 9.72x | 3/3 |
| 256K | **Yes** — `Using AttentionBackendEnum.FLASHINFER backend.` | 1,273,968 / 4.86x | 3/3 |

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms | Max concurrent observed | num-prompts |
| --- | --- | --- | --- | --- | --- | --- |
| 128K | 9436.6 ± 6.4 | 18.4 ± 0.0 | 17970.9 ± 588.3 | 108894.9 ± 181.7 | 10 / 10 / 10 | 50 |
| 256K | 6064.7 ± 1.5 | 5.9 ± 0.0 | 53859.6 ± 24.2 | 143924.9 ± 30.6 | 5 / 5 / 5 | 50 |

---

## Derived cost / break-even slots

Left open: compute from `$4.47/hr ÷ total_token_throughput` once throughput above is reviewed.

---

## Provenance spot-checks (required for v3 consolidation)

Performed before finalizing this file; also recorded in `STATUS.md`.

1. **A / max concurrency 311.02 at 2K** ← `run-A-short-context/vllm_startup_2048.log` line 43: `Maximum concurrency for 2,048 tokens per request: 311.02x`.
2. **B / total throughput ~13870.6 at 32K** ← `run-B-long-context/bench_32768_trial1.json` field `total_token_throughput=13870.598031072039` (v2 carry).
3. **B / 128K trial 3 total ~7990.6** ← `run-B-long-context/bench_131072_trial3.json` field `total_token_throughput=7990.594374774886` (v3 append).
4. **C / BF16 + fp8 KV + FlashInfer at 128K** ← `run-C-fp8-sensitivity/vllm_startup_131072.log` lines 4/7/15/23: model `2512-BF16`, `kv_cache_dtype=fp8`, `quantization=None`, `Using AttentionBackendEnum.FLASHINFER backend.`
5. **C / total throughput ~6066.4 at 256K** ← `run-C-fp8-sensitivity/bench_262144_trial1.json` field `total_token_throughput=6066.376649866082`; trials 2–3 ≈6064–6065 (3/3).

---

## Accumulated Droplet-hours and cost

| Metric | Value |
| --- | --- |
| Droplets provisioned | 3 × H200 (`gpu-h200x1-141gb`) |
| Provision time (UTC) | 2026-08-25 21:46 |
| Consolidation time (UTC) | 2026-08-26 15:31 |
| Elapsed wall time | 17.76 h |
| Accumulated Droplet-hours (3 × elapsed) | **53.27** |
| Rate | $4.47/hr per Droplet |
| Estimated compute cost (3 Droplets, no teardown) | **$238.10** |

---

## File inventory note

`sweep_summary.md` (v1) and `sweep_summary_v2.md` (v2) are preserved. C folders contain **v3-only** sensitivity artifacts; do not merge v1/v2 C JSONs into article slots.


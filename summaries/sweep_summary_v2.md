# MKTG-3270 Sweep Summary v2

> **Superseded.** The published article and the headline tables in this repository use `sweep_summary_v4.md`. This file is kept so the bug history is auditable.


Generated at consolidation after the FIX 1–4 re-run (2026-08-26). Maps fillable
`[[SLOT: ...]]` values in `does-context-length-affect-inference-cost-linearly.md` to
measured values from this re-run. **Does not edit the article. Does not overwrite
`sweep_summary.md` (v1).**

Source trees: `run-A-short-context/`, `run-B-long-context/`, `run-C-fp8-sensitivity/`.

---

## What changed vs v1

| Fix | Result in this run |
| --- | --- |
| FIX 1 BF16 repo | A/B loaded `mistralai/Ministral-3-14B-Instruct-2512-BF16`; startup reports `quantization=None`, weights ≈26.66 GiB (vs v1's FP8 checkpoint ≈15.37 GiB) |
| FIX 2 warm-up | Separate 10-request warm-up before every trial (discarded); real trials use `--save-detailed`; every accepted JSON has per-request `ttfts`/`itls`/`input_lens` lists |
| FIX 3 FlashInfer | C booted with `--attention-backend FLASHINFER`; both points logged `Using AttentionBackendEnum.FLASHINFER backend.` |
| FIX 4 256K timeout | 2-hour budget used; C/256K got 2/3 valid trials; B/256K got 1/3 valid trial then `_TIMEOUT` (trial 1 data retained on disk and reported below with that caveat) |

---

## Run metadata

| Field | Value |
| --- | --- |
| Benchmark run date | 2026-08-26 (v2 re-run started ~07:12 UTC) |
| vLLM | 0.27.1 |
| FlashInfer | 0.6.16.post4 |
| Headline model (A/B) | `mistralai/Ministral-3-14B-Instruct-2512-BF16` (`quantization=None`, `dtype=torch.bfloat16`) |
| FP8 arm model (C) | `mistralai/Ministral-3-14B-Instruct-2512` (`quantization=fp8`, `--kv-cache-dtype fp8`) |
| Attention (headline) | `FLASH_ATTN` (auto) |
| Attention (FP8 arm) | `FLASHINFER` (forced via `--attention-backend FLASHINFER`, gate-confirmed) |
| `--gpu-memory-utilization` | 0.90 |
| Fixed output length | 256 |
| Warm-up | Separate 10-request invocation before each trial; discarded; audit files `warmup_{ctx}_trial{n}.audit` |
| Trials | 3 attempted per point; see per-point notes for 2/3 or 1/3 |
| Driver / CUDA | 580.173.02 / 13.0 |
| BF16 weight footprint | ≈26.66 GiB (weights + non-torch), from startup `gpu_worker` line |

---

## Droplet A — BF16 headline, 2K–16K (all 4/4 complete, 3/3 trials)

KV pool is fixed at **636,976** tokens at every context (lower than v1's 710,992 because BF16 weights leave less free memory for KV).

| Context | KV pool | Max concurrency (boot) | Max concurrent observed | Preemptions | kv_cache_usage_perc |
| --- | --- | --- | --- | --- | --- |
| 2K | 636,976 | 311.02x | 91 / 87 / 91 | 0 | 0.0 |
| 4K | 636,976 | 155.51x | 71 / 71 / 71 | 0 | 0.0 |
| 8K | 636,976 | 77.76x | 68 / 68 / 68 | 0 | 0.0 |
| 16K | 636,976 | 38.88x | 40 / 40 / 40 | 0 | 0.0 |

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms | num-prompts / rate |
| --- | --- | --- | --- | --- | --- |
| 2K | 14813.2 ± 10.2 | 1851.7 ± 1.3 | 1350.1 ± 1.0 | 4725.8 ± 21.5 | 141 / inf |
| 4K | 16714.8 ± 20.1 | 1044.7 ± 1.3 | 1414.5 ± 0.3 | 10448.7 ± 25.7 | 139 / inf |
| 8K | 17203.7 ± 13.5 | 537.6 ± 0.4 | 7509.1 ± 12.0 | 23170.0 ± 35.3 | 88 / inf |
| 16K | 15992.3 ± 5.5 | 249.9 ± 0.1 | 1678.4 ± 0.8 | 30586.4 ± 12.8 | 88 / inf |

---

## Droplet B — BF16 headline, 32K–256K

| Context | Status | Trials ok | Notes |
| --- | --- | --- | --- |
| 32K | complete | 3/3 | |
| 64K | complete | 3/3 | |
| 128K | complete | 2/3 | Trial 3 hit 45-min point deadline mid-run |
| 256K | partial / `_TIMEOUT` | 1/3 | Trial 1 completed with valid `--save-detailed` JSON; trials 2–3 did not finish inside the 2-hour budget. Values below are from trial 1 only. |

| Context | KV pool | Max concurrency (boot) | Max concurrent observed | Preemptions |
| --- | --- | --- | --- | --- |
| 32K | 636,976 | 19.44x | 20 / 20 / 20 | 0 |
| 64K | 636,976 | 9.72x | 10 / 10 / 10 | 0 |
| 128K | 636,976 | 4.86x | 5 / 5 | 0 |
| 256K | 636,976 | 2.43x | 3 (trial 1 only) | 0 |

| Context | Total tok/s | Output tok/s | TTFT p50 ms | TTFT p99 ms | num-prompts |
| --- | --- | --- | --- | --- | --- |
| 32K | 13870.6 ± 1.5 | 108.4 ± 0.0 | 3095.7 ± 0.8 | 35716.5 ± 29.8 | 50 |
| 64K | 11033.8 ± 4.9 | 43.1 ± 0.0 | 8220.8 ± 4.6 | 42838.2 ± 85.3 | 50 |
| 128K | 7986.9 ± 2.7 (n=2) | 15.6 ± 0.0 | 22723.8 ± 4.1 | 51978.9 ± 12.5 | 50 |
| 256K | 4968.4 (n=1) | 4.9 | 63609.4 | 91944.3 | 50 |

---

## Droplet C — FP8 sensitivity (FlashInfer gated)

| Context | FlashInfer confirmed? | KV pool / max conc | Total tok/s | Trials |
| --- | --- | --- | --- | --- |
| 128K | **Yes** — `Using AttentionBackendEnum.FLASHINFER backend.` | 1,421,984 / 10.85x | 10796.9 ± 1.3 | 3/3 |
| 256K | **Yes** (same confirmation at boot) | 1,421,984 / 5.42x | 6605.5 ± 1.9 (n=2) | 2/3 (trial 3 hit 2h deadline) |

FP8 KV pool is ~2.2× the BF16-arm pool at the same `gpu-memory-utilization` (1,421,984 vs 636,976), consistent with FP8 KV storage plus smaller FP8 weight footprint on C.

---

## Derived cost / break-even slots

Left open (same policy as v1): compute from `$4.47/hr ÷ total_token_throughput` once throughput above is reviewed. 256K BF16 has n=1 only — treat break-even at that point as provisional.

---

## Provenance spot-checks (required for v2 consolidation)

Performed before finalizing this file; also recorded in `STATUS.md`.

1. **A / max concurrency 311.02 at 2K** ← `run-A-short-context/vllm_startup_2048.log` line 43: `Maximum concurrency for 2,048 tokens per request: 311.02x` (unique to A folder).
2. **A / BF16 model at 4K** ← `run-A-short-context/vllm_startup_4096.log` line 4 / 7: `model mistralai/Ministral-3-14B-Instruct-2512-BF16` and `quantization=None` in engine init.
3. **B / total throughput ~13870.6 at 32K** ← mean of `run-B-long-context/bench_32768_trial{1,2,3}.json`; trial1 line 1 field `total_token_throughput=13870.598031072039`, with `ttfts` list length 50.
4. **C / FlashInfer at 128K** ← `run-C-fp8-sensitivity/vllm_startup_131072.log` line 27: `Using AttentionBackendEnum.FLASHINFER backend.` (also on C/256K startup line 27; absent from A/B).
5. **C / total throughput ~6604 at 256K** ← `run-C-fp8-sensitivity/bench_262144_trial1.json` field `total_token_throughput=6604.192217855145`, `ttfts` length 50; trial2 = 6606.9.

---

## File inventory note

v1 `sweep_summary.md` is preserved alongside this file for comparison. Local folders for this re-run contain only v2 artifacts (prior v1 point files were wiped at re-run start).

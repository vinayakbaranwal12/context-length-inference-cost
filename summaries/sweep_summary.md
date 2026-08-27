# MKTG-3270 Sweep Summary

> **Superseded.** The published article and the headline tables in this repository use `sweep_summary_v4.md`. This file is kept so the bug history is auditable.


Generated at consolidation (Phase 7), 2026-08-26. Maps every fillable `[[SLOT: ...]]` in
`does-context-length-affect-inference-cost-linearly.md` to a measured value pulled directly
from the logs in this folder. **This file is for review — it does not edit the article.**
Per-context source files: `run-{A,B,C}-*/bench_{ctx}_trial{1,2,3}.json`,
`vllm_startup_{ctx}.log`, `metrics_{ctx}_trial{n}.log`.

---

## ⚠️ Three methodology gaps found during consolidation — read before using this data

These were not caught until the raw logs were assembled, after the run finished. Flagging
them here rather than quietly filling slots as if they weren't issues.

1. **Warm-up discard was never actually applied to the reported numbers.** The article's
   methodology (and every "Point complete" line in `STATUS.md`) states the first 10
   completions per point are discarded before computing throughput/latency. In practice,
   `run_trial` never passed `--save-detailed` to `vllm bench serve`, so no per-request data
   was ever saved — only aggregate stats (mean/median/p99 across *all* completions,
   warm-up included) exist in `bench_{ctx}_trial{n}.json`. **Every number in the tables
   below includes the first 10 requests at that point**, not a warm-up-adjusted figure. At
   the largest point sizes (253 prompts at 2K) this is a ~4% dilution; at the floor (50
   prompts at 65536/131072) it's ~20% of the trial. This should either be re-run with
   `--save-detailed` added, or the article's Methodology section should say warm-up was not
   excluded, rather than implying it was.
2. **FlashInfer was not actually the active attention backend on the FP8 arm.**
   `VLLM_ATTENTION_BACKEND=FLASHINFER` was set explicitly for Droplet C, but both FP8
   startup logs report `Using FLASH_ATTN attention backend out of potential backends:
   ['FLASH_ATTN', 'FLASHINFER', 'TRITON_ATTN']` (confirmed at both 131072 and 262144, see
   quotes in the FP8 section below). FlashInfer *was* active, but only for top-p/top-k
   sampling and kernel autotuning — not for attention itself. Per the article's own stated
   rule ("mark as not run if unconfirmed, don't override for the sake of finishing
   faster"), the honest answer to `[[SLOT: FlashInfer confirmed active ... ]]` is **no**,
   not yes.
3. **The model's weights are not BF16.** Every startup log (headline arm included) reports
   `quantization=fp8` at engine init, and the observed weights+non-torch memory footprint
   (~15.37 GiB) is consistent with FP8-quantized storage for a 14B model, not BF16 (which
   would be closer to ~28 GiB). `dtype=torch.bfloat16` in the same log refers to the
   compute/activation dtype, not weight storage. The "BF16 headline arm" framing in the
   article assumes BF16 weights; the checkpoint itself ships FP8 weights regardless of
   which arm you're on. This doesn't invalidate the KV-cache-pool thesis (that's about KV
   cache dtype, set independently via `--kv-cache-dtype`), but the "BF16 weight footprint"
   slot and any prose calling the headline arm "BF16" should be corrected or caveated.

None of this invalidates the core measured trend (KV pool is fixed regardless of
`--max-model-len`; throughput and TTFT degrade sharply with context length) — see the data
below — but all three should be resolved before publishing exact numbers.

---

## Run metadata

| Field | Value | Source |
| --- | --- | --- |
| Benchmark run date | 2026-08-26 | `date` field in every `bench_*.json` (`20260826-*`) |
| vLLM version | `0.27.1` | startup log, all contexts |
| FlashInfer version | `0.6.16.post4` | autotune cache path, startup log |
| Attention backend, headline (BF16-labeled) arm | `FLASH_ATTN` (chosen automatically from `['FLASH_ATTN', 'FLASHINFER', 'TRITON_ATTN', 'FLEX_ATTENTION']`) | startup log, all A/B contexts |
| Attention backend, FP8 arm | `FLASH_ATTN`, **not** FlashInfer, despite `VLLM_ATTENTION_BACKEND=FLASHINFER` being set — see gap #2 above | startup log, C/131072 and C/262144 |
| `--gpu-memory-utilization` | `0.90` | orchestrator config (matches article's SLOT) |
| Fixed output length | `256` | orchestrator config / every JSON's `total_output_tokens ÷ completed ≈ 256` |
| Warm-up requests "discarded" | `10` per point **as configured, but not actually applied** — see gap #1 above | orchestrator config vs. actual saved data |
| Trials per sweep point | `3` (attempted at every completed point; 262144 on B and C got 0/3 valid trials, see below) | orchestrator config + per-point trial file counts |
| Driver version | `580.173.02` | `nvidia-smi` on live Droplet A |
| CUDA version | `13.0` | `nvidia-smi` on live Droplet A |
| BF16 weight footprint | **Not BF16 — see gap #3.** Observed weights+non-torch footprint ≈ `15.37 GiB` (consistent with FP8-quantized weights), reported the same at every context length | startup log `gpu_worker.py:789` line, all contexts |

---

## Droplet A (`run-A-short-context`) — headline arm, 2K–16K

All 4 assigned points completed with 3/3 valid trials each.

### Capacity table

| Context | KV pool (tokens) | Max concurrency (from boot) | Max concurrent requests observed (mean of 3 trials) | Preemptions | `kv_cache_usage_perc` |
| --- | --- | --- | --- | --- | --- |
| 2K | `710,992` | `347.16x` | `93, 99, 95` (all 3 trials) | `0` (all 3 trials) | `0.0` (all 3 trials) |
| 4K | `710,992` | `173.58x` | `75, 75, 75` | `0` | `0.0` |
| 8K | `710,992` | `86.79x` | `69, 70, 69` | `0` | `0.0` |
| 16K | `710,992` | `43.40x` | `45, 46, 46` | `0` | `0.0` |

Note the KV pool is identical (710,992 tokens) at every context length — it's set by
`--gpu-memory-utilization` against total GPU memory, not by `--max-model-len`. Only "max
concurrency" (pool ÷ context length) falls as context grows. This is the core mechanism the
article's thesis rests on, and it's directly confirmed here.

### Throughput/latency table (mean ± std across 3 trials; see gap #1 re: warm-up)

| Context | Total throughput (tok/s) | Output throughput (tok/s) | TTFT p50 (ms) | TTFT p99 (ms) | num-prompts / request-rate used |
| --- | --- | --- | --- | --- | --- |
| 2K | `23142.3 ± 18.6` | `2892.8 ± 2.3` | `871.3 ± 0.4` | `3021.3 ± 24.9` | `253` / `inf` |
| 4K | `23915.7 ± 27.5` | `1494.7 ± 1.7` | `926.1 ± 0.7` | `6730.0 ± 21.7` | `212` / `inf` |
| 8K | `23968.7 ± 29.4` | `749.0 ± 0.9` | `951.6 ± 2.7` | `15428.0 ± 25.5` | `178` / `inf` |
| 16K | `21893.4 ± 4.9` | `342.1 ± 0.1` | `1228.7 ± 0.9` | `24188.1 ± 22.0` | `119` / `inf` |

---

## Droplet B (`run-B-long-context`) — headline arm, 32K–256K

32768, 65536, 131072 completed with 3/3 valid trials each (131072 required a mid-run
restart after an SSH-transport bug was found and fixed — see `STATUS.md` for detail; the
final 3 trials used post-fix). **262144 hit the 45-minute per-point timeout during trial 2,
with trial 1 itself never completing in time — 0/3 valid trials, no usable throughput/TTFT
data for this point.** Boot itself succeeded (KV pool and max-concurrency below are real),
only the benchmark trials are missing.

### Capacity table

| Context | KV pool (tokens) | Max concurrency (from boot) | Max concurrent requests observed (mean of 3 trials) | Preemptions | `kv_cache_usage_perc` |
| --- | --- | --- | --- | --- | --- |
| 32K | `710,992` | `21.70x` | `23, 23, 23` | `0` | `0.0` |
| 64K | `710,992` | `10.85x` | `11, 11, 11` | `0` | `0.0` |
| 128K | `710,992` | `5.42x` | `6, 6, 6` | `0` | `0.0` |
| 256K | `710,992` | `2.71x` | **`_TIMEOUT` — no trial data** | — | — |

### Throughput/latency table

| Context | Total throughput (tok/s) | Output throughput (tok/s) | TTFT p50 (ms) | TTFT p99 (ms) | num-prompts / request-rate used |
| --- | --- | --- | --- | --- | --- |
| 32K | `17865.2 ± 5.4` | `139.6 ± 0.0` | `2401.5 ± 1.1` | `29210.0 ± 12.0` | `80` / `inf` |
| 64K | `13548.1 ± 8.7` | `52.9 ± 0.0` | `6249.5 ± 5.2` | `38756.3 ± 23.1` | `50` / `inf` |
| 128K | `9187.7 ± 2.9` | `17.9 ± 0.0` | `20184.3 ± 14.2` | `58323.2 ± 19.9` | `50` / `inf` |
| 256K | **`_TIMEOUT` — no trial data** | — | — | — | — |

**On the 256K gap:** at 128K, reported concurrency was already down to 5.42x and TTFT p50
was over 20 seconds; at 256K it drops further to 2.71x. Even a single 50-request trial
(the methodology's request-count floor) could not complete inside the 45-minute point
timeout at that throughput — this is a real tension between the "≥50 requests" floor and
the "45-minute point" safety valve at the sweep's extreme edge, not a bug (see `STATUS.md`
for the full analysis). If 256K data is required for the article, it needs a dedicated
re-run of just that point with either a relaxed timeout or a reduced request floor —
recommend deciding deliberately rather than silently loosening either constraint.

---

## Droplet C (`run-C-fp8-sensitivity`) — FP8 arm, 128K and 256K only

131072 completed with 3/3 valid trials (also required the same mid-run restart as B/131072
for the same SSH-transport bug fix). **262144 hit the same 45-minute timeout as B/262144,
0/3 valid trials.**

| Context | FlashInfer confirmed active? | FP8 KV pool (tokens) / max concurrency | FP8 total throughput (tok/s) |
| --- | --- | --- | --- |
| 128K | **No** — see gap #2 above; log line: `Using FLASH_ATTN attention backend out of potential backends: ['FLASH_ATTN', 'FLASHINFER', 'TRITON_ATTN']` | `1,421,984` tokens / `10.85x` | `9777.4 ± 4.0` |
| 256K | **No** (same log line present at boot before timeout) | `1,421,984` tokens / `5.42x` | `_TIMEOUT` — no trial data |

Compare FP8's KV pool (1,421,984 tokens) against the headline arm's BF16-KV-cache pool at
the same `--gpu-memory-utilization` (710,992 tokens, from A/B tables above): FP8 KV cache
exactly doubles the token capacity in the same reserved memory, as expected from halving
per-token KV cache storage. This holds despite the attention-backend caveat above, since
that's about backend selection for the QK/V compute, not the KV cache dtype itself (which
was confirmed via `--kv-cache-dtype fp8` in the boot command and the doubled pool size is
direct evidence it took effect).

---

## Derived / cost slots — intentionally left open

Per the consolidation instructions, these are not computed by hand. They follow directly
from the formula (`$4.47/hr H200 cost ÷ effective total-token throughput`, compared against
the $0.20/1M serverless rate) once the throughput slots above are reviewed and the three
gaps are resolved or accepted:

- `[[SLOT: effective cost per 1M total tokens at {2K,4K,8K,16K,32K,64K,128K}, at 100% utilization]]` — computable now from the throughput tables above.
- `[[SLOT: effective cost per 1M total tokens at 256K, ...]]` — **not computable, no 256K trial data on either B or C.**
- `[[SLOT: break-even utilization vs $0.20/1M serverless at {context}]]` — computable at every context except 256K, same caveat.
- `[[SLOT: context length at which effective cost-per-token exceeds the $0.20/1M serverless rate]]` — computable from the above once filled in, bounded between 128K (last measured point) and 256K (unmeasured) if the crossover falls in that gap.
- `[[SLOT: ratio of effective cost-per-token at 256K vs 4K]]` — **not computable**, 256K has no throughput data. If needed without a 256K re-run, the closest achievable measured ratio is 128K vs. 4K.
- `[[SLOT: chart — effective cost-per-token vs. context length ...]]` — chart itself not generated by this consolidation pass; data above is sufficient to build it for 2K–128K (BF16) plus 128K (FP8), with 256K absent.

---

## File manifest

Final remote-vs-local file counts, verified matching after consolidation: A 40/40, B 35/35,
C 15/15. Two cleanup items during consolidation are logged in `STATUS.md` in full: an
accidental cross-contamination of `run-A-short-context` with Droplet C files (found and
removed), and a stale background `rsync_loop.sh` process still pointed at the pre-fix
remote path, which was silently failing and leaving debris files (found, stopped, cleaned).
Neither affected the trial JSON data itself, only file-listing hygiene.

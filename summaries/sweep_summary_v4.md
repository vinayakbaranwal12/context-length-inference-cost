# MKTG-3270 Sweep Summary v4

Generated after the Patch A/B/C correction pass (2026-08-26 22:55 UTC). Maps fillable
`[[SLOT: ...]]` values in `does-context-length-affect-inference-cost-linearly.md` to
measured values. **Does not edit the article.** Preserves `sweep_summary.md` (v1),
`sweep_summary_v2.md` (v2), and `sweep_summary_v3.md` (v3).

Source trees: `run-A-short-context/`, `run-B-long-context/`, `run-C-fp8-sensitivity/`.

---

## What changed vs v3

| Patch | What it fixed | Evidence |
| --- | --- | --- |
| **A — concurrency clamp removed** | `probe_and_size` clamped concurrency to `min(x, 64)` at every point, silently overriding the boot-log ceiling at 2K (311→64), 4K (155→64), 8K (78→64). Now uses the full unclamped boot value. | v4 `true_peak` concurrency now matches the boot-derived ceiling exactly at every point (see table below) — it never did in v1–v3 at these three contexts. |
| **A — turnover-floor sizing** | `num_prompts` is now `max(50, rate×200s, concurrency×8)` instead of a fixed-15-request probe with a 50/2000 floor/ceiling. Every point in this pass ran ≥8 full turnovers of its concurrency. | Applies to all 6 re-run points, including 16K/32K/64K whose concurrency was never clamped — their `num_prompts` still grew substantially (e.g. 32K: 50→152) for a more sustained measurement window. |
| **A — input-length safety margin** | Root-caused and fixed a latent bug present since v1: `random-input-len = ctx-256` left zero margin, and vLLM's own random-prompt generator occasionally (~0.2%) lands 1 token over that target due to its documented "imperfect" decode/re-encode correction. At v3's small batch sizes this silently passed a 90%-completion threshold; Patch A's larger batches made it near-certain to trigger. Fixed with `INPUT_LEN_MARGIN=8` (8× the largest drift ever observed, confirmed via direct HTTP capture of the actual 400 response body: server counted exactly 1 token over budget, every time). | Reproduced and root-caused live (see STATUS.md); all 6 v4 points then ran with **zero rejected trials**. |
| **B — acceptance gate** | `validate_trial` rejects any trial with duration below 150s, fewer than 6 turnovers, a `max_concurrency` mismatch against the boot-derived value, or observed concurrency reaching the 512 scheduler pin. All 18 trials in this pass (6 points × 3) passed with zero rejections after the margin fix. | |
| **C — true concurrency** | vLLM's own `max_concurrent_requests` field is a whole-second, both-endpoints-inclusive bucket count, confirmed to over-report during synchronized wave transitions (this was the finding that triggered this whole pass). This summary's "Max concurrent observed" column is computed by millisecond-precision interval sweep over raw per-request timing data, not read from that field. | See per-point comparison below: reported vs true. |
| **Post-hoc addendum — B/128K, B/256K, C/128K, C/256K** | These 4 points were carried forward from v3 unchanged and initially left with vLLM's uncorrected field. A follow-up read-only verification (no re-run, no GPU time) applied the same `true_max_concurrency()` check to their existing trial JSONs. | All 12 trials confirmed clean (zero failures, exact 3/3 trial agreement); true concurrency is 4/2/9/4 respectively, not the native 5/3/10/5. See the B and C sections below for the full comparison and the recomputed FP8 ratio. |

---

## Run metadata

| Field | Value |
| --- | --- |
| Benchmark run date | 2026-08-26 (v4 patch pass ~19:41–22:50 UTC) |
| vLLM | 0.27.1 |
| Headline model (A/B) | `mistralai/Ministral-3-14B-Instruct-2512-BF16` (`quantization=None`, `dtype=torch.bfloat16`) |
| `--gpu-memory-utilization` | 0.90 |
| Fixed output length | 256 |
| `random-input-len` | `ctx - 256 - 8` (8-token safety margin, v4 only; v3 and earlier used `ctx - 256`) |
| Warm-up | Separate 10-request invocation before each trial; discarded |
| Trials | 3 per point, all cells 3/3 in this pass, zero rejections |
| `num_prompts` sizing (v4) | `max(50, probe_rate×200s, concurrency×8)`, deadline-limited to 60% of remaining point budget |
| Trial acceptance gate (v4) | 0 failed requests; duration ≥150s; ≥6 turnovers; `max_concurrency` matches boot value; observed concurrency <512 |
| "Max concurrent observed" methodology (v4 rows only) | Millisecond-precision interval sweep over raw `start_times`/`ttfts`/`itls`, not vLLM's own `max_concurrent_requests` field (confirmed to over-report; see comparison columns below) |

---

## Droplet A — BF16 headline, 2K–16K (fully re-run this pass, Patch A/B/C)

KV pool **636,976** tokens at every context (unchanged from v3 — model/GPU-mem-util unaffected by these patches).

| Context | KV pool | Max conc (boot) | True peak observed (Patch C) | vLLM-reported peak (bucketing artifact) | num_prompts | Turnovers |
| --- | --- | --- | --- | --- | --- | --- |
| 2K | 636,976 | 311.02x | 311/311/311 | 334/333/335 | 2488 | 8.00x |
| 4K | 636,976 | 155.51x | 155/155/155 | 164/164/164 | 1240 | 8.00x |
| 8K | 636,976 | 77.76x | 77/77/77 | 82/82/82 | 616 | 8.00x |
| 16K | 636,976 | 38.88x | 38/38/38 | 41/41/41 | 304 | 8.00x |

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms |
| --- | --- | --- | --- | --- |
| 2K | 19089.8 ± 16.5 | 2395.58 ± 2.07 | 1093.1 ± 0.8 | 22196.2 ± 45.3 |
| 4K | 18812.3 ± 5.4 | 1178.07 ± 0.34 | 1112.3 ± 0.3 | 24170.0 ± 27.9 |
| 8K | 17933.2 ± 6.5 | 560.96 ± 0.20 | 1135.3 ± 0.0 | 26074.7 ± 14.0 |
| 16K | 16214.8 ± 6.7 | 253.48 ± 0.10 | 1685.6 ± 0.5 | 28627.8 ± 13.1 |

**Note:** these throughput figures are substantially higher than v1/v2/v3 at 2K/4K/8K (e.g. 2K: 14,813 → 19,090 tok/s) because those points were genuinely running at a clamped concurrency of 64 in every prior version, not the true memory-bound ceiling (311/155/78). 16K's concurrency was never clamped (boot ceiling 38.88 < 64) — its throughput move is smaller and reflects only the larger, more sustained `num_prompts`.

---

## Droplet B — BF16 headline, 32K–256K

| Context | Status | Trials ok | Notes |
| --- | --- | --- | --- |
| 32K | **re-run this pass** | 3/3 | num_prompts 50→152 (turnover floor); concurrency unchanged (19.44 was never clamped) |
| 64K | **re-run this pass** | 3/3 | num_prompts 50→72; concurrency unchanged (9.72 was never clamped) |
| 128K | **carried from v3, unchanged** | 3/3 | Not re-run — floor-bound (50-prompt floor), not turnover-bound; unaffected by Patch A. Post-hoc Patch C verification (2026-08-26, read-only, no re-run) confirms true concurrency = 4, not the vLLM-reported 5. |
| 256K | **carried from v3, unchanged** | 3/3 | Not re-run — same as 128K. Post-hoc Patch C verification confirms true concurrency = 2, not the vLLM-reported 3. |

| Context | KV pool | Max conc (boot) | True peak observed (Patch C) | vLLM-reported peak | num_prompts | Turnovers |
| --- | --- | --- | --- | --- | --- | --- |
| 32K | 636,976 | 19.44x | 19/19/19 | 21/20/21 | 152 | 8.00x |
| 64K | 636,976 | 9.72x | 9/9/9 | 10/10/10 | 72 | 8.00x |
| 128K | 636,976 | 4.86x | **4/4/4** | 5/5/5 | 50 | *(v3 sizing)* |
| 256K | 636,976 | 2.43x | **2/2/2** | 3/3/3 | 50 | *(v3 sizing)* |

**Addendum (2026-08-26, post-hoc, read-only):** the two rows above were flagged in the original v4 pass as "not yet recomputed by Patch C." A follow-up verification ran `true_max_concurrency()` (identical algorithm already validated against A/B's 2K–64K) directly against the existing trial JSONs — no server boot, no new bench run, no GPU time. All 3 trials per point agree exactly and match `floor(boot ceiling)`: 128K → 4 (4.86x), 256K → 2 (2.43x). vLLM's native field over-reports by exactly +1 at both points, consistent with the same bucketing artifact already documented for every other point in this sweep. Completion/failure fields were also checked directly on all 6 trials: `completed`=`num_prompts`=50 and `failed`=0 in every trial, with zero non-empty entries in any `errors` list — no dropped or silently-errored requests anywhere in these two carried-forward points.

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms |
| --- | --- | --- | --- | --- |
| 32K | 13929.6 ± 12.9 | 108.85 ± 0.10 | 3092.1 ± 2.1 | 33751.9 ± 62.0 |
| 64K | 11048.2 ± 19.5 | 43.16 ± 0.08 | 8205.3 ± 20.3 | 41640.2 ± 30.6 |
| 128K (v3) | 7988.2 ± 2.8 | 15.60 ± 0.01 | 22721.4 ± 5.1 | 51946.5 ± 56.7 |
| 256K (v3) | 4967.2 ± 1.5 | 4.85 ± 0.00 | 63648.1 ± 51.4 | 92645.2 ± 668.1 |

---

## Droplet C — BF16 weights + FP8 KV sensitivity (carried from v3, unchanged)

**Not re-run this pass.** Both C points are floor-bound (50-prompt floor from v3's sizing, not turnover-bound) and were explicitly out of scope for this patch pass. Throughput/latency values below are identical to `sweep_summary_v3.md`.

**Methodology note (updated 2026-08-26, post-hoc, read-only):** the original v4 pass left C's concurrency figures as vLLM's own uncorrected field. A follow-up verification (same read-only pass as B's 128K/256K above, no re-run) ran `true_max_concurrency()` directly against C's existing trial JSONs and confirms true concurrency at both points, now shown alongside the native field below.

| Context | FlashInfer confirmed? | KV pool / max conc (boot) | True peak observed (Patch C) | vLLM-reported peak (bucketing artifact) | Trials |
| --- | --- | --- | --- | --- | --- |
| 128K | **Yes** | 1,273,968 / 9.72x | **9/9/9** | 10/10/10 | 3/3 |
| 256K | **Yes** | 1,273,968 / 4.86x | **4/4/4** | 5/5/5 | 3/3 |

Same verification also checked completion/failure fields directly on all 6 C trials: `completed`=`num_prompts`=50 and `failed`=0 in every trial, zero non-empty `errors` entries anywhere.

### FP8 sensitivity ratio, recomputed with true concurrency

The original v4/v3 passes never stated this ratio numerically; it is added here now that both arms have Patch-C-corrected concurrency figures. Reported per context length, not averaged into one rounded number:

| Context | B (BF16, true concurrency) | C (FP8 KV, true concurrency) | Ratio (C / B) |
| --- | --- | --- | --- |
| 128K | 4 | 9 | **9/4 = 2.25x** |
| 256K | 2 | 4 | **4/2 = 2.0x exactly** |

The two ratios are not identical (2.25x at 128K vs 2.0x at 256K), which is expected: both are small integers produced by flooring a continuous pool-size ratio, and integer flooring does not preserve a ratio exactly at every point along the curve. Do not average these into a single "roughly 2x" figure when this table is used to fill the article's FP8 arm slots.

| Context | Total tok/s (mean±std) | Output tok/s | TTFT p50 ms | TTFT p99 ms |
| --- | --- | --- | --- | --- |
| 128K | 9436.6 ± 6.4 | 18.43 ± 0.01 | 17970.9 ± 588.3 | 108894.9 ± 181.7 |
| 256K | 6064.7 ± 1.5 | 5.92 ± 0.00 | 53859.6 ± 24.2 | 143924.9 ± 30.6 |

---

## Provenance spot-checks (required for v4 consolidation)

Performed before finalizing this file; also recorded in `STATUS.md`.

1. **A/2K true concurrency matches boot ceiling exactly** ← `run-A-short-context/vllm_startup_2048.log`: `Maximum concurrency for 2,048 tokens per request: 311.02x`; independently, `run-A-short-context/bench_2048_trial1.json` interval-sweep over `start_times`/`ttfts`/`itls` yields peak=311 in all 3 trials — the clamp-affected point now genuinely reaches its pool ceiling, which it never did in v1-v3.
2. **A/2K bucketing artifact persists as predicted** ← same trial1 JSON: native `max_concurrent_requests`=334 vs true peak=311, a 23-request overstatement from the whole-second-bucket counting bug identified during the diagnostic that triggered this pass — confirms Patch C's fix is necessary even after Patch A/B.
3. **INPUT_LEN_MARGIN=8 fix verified in the actual bench command** ← `run-A-short-context/bench_stdout_2048_trial1.log` argparse dump shows `random_input_len=1784` (= 2048-256-8), not the old `1792`.
4. **B/32K num_prompts grew via turnover floor, not the clamp** ← boot ceiling 19.44x was never clamped (< 64) in any version; `run-B-long-context/bench_32768_trial1.json` shows `num_prompts` grew from v3's 50 to v4's 152 = 8×19, matching `MIN_TURNOVERS=8` exactly.
5. **Zero rejected trials this pass** ← `orchestrator/orch_A_v4.log` and `orch_B_v4.log` contain zero `_TRIAL_REJECTED` lines across all 18 trials (6 points × 3), versus 4 rejections across the first two attempts before the margin fix.
6. **B/128K true concurrency = 4, not the reported 5** ← `run-B-long-context/bench_131072_trial{1,2,3}.json`, interval-sweep over `start_times`/`ttfts`/`itls` yields peak=4 in all 3 trials against a boot ceiling of 4.86x; native `max_concurrent_requests`=5 in all 3.
7. **C/256K true concurrency = 4, not the reported 5** ← `run-C-fp8-sensitivity/bench_262144_trial{1,2,3}.json`, interval-sweep yields peak=4 in all 3 trials against a boot ceiling of 4.86x; native `max_concurrent_requests`=5 in all 3.

---

## Accumulated Droplet-hours and cost

| Metric | Value |
| --- | --- |
| Droplets provisioned | 3 × H200 (`gpu-h200x1-141gb`) |
| Provision time (UTC) | 2026-08-25 21:46 |
| Consolidation time (UTC) | 2026-08-26 22:55 |
| Elapsed wall time | 25.15 h |
| Accumulated Droplet-hours (3 × elapsed) | **75.46** |
| Rate | $4.47/hr per Droplet |
| Estimated compute cost (3 Droplets, no teardown) | **$337.33** |

---

## File inventory note

`sweep_summary.md` (v1), `sweep_summary_v2.md` (v2), and `sweep_summary_v3.md` (v3) are all preserved.
`run-A-short-context/` and the 32K/64K files in `run-B-long-context/` now contain v4-only artifacts
(overwritten from v3 as part of this pass's explicit re-run scope). B's 128K/256K files and all of
`run-C-fp8-sensitivity/` are unchanged v3 artifacts.


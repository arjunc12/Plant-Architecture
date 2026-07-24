"""
benchmarks/focused_pipeline_test.py

Measures whether pareto_functions_new.py's all-pairs distance cache
(attach_distances) actually speeds up conduction_delay — the only
function that differs between the old and new pipelines.

Why this isn't a full-pipeline timing comparison:

    - evaluate_parameters() / arbor_best_cost(), which dominate a real
      CSV-gen run (~8s per 441 grid points), were NOT changed by
      pareto_functions_new.py. Timing the full pipeline mostly measures
      an unrelated code path and can make a real improvement in
      conduction_delay look negligible just because it's a small slice
      of total runtime — or bury it in noise entirely.

    - The actual change is in how node-to-node distances get resolved:
      many small per-tip nx.shortest_path searches (old) vs one
      nx.all_pairs_dijkstra_path_length call followed by O(1) lookups
      (new). This script times exactly that, with file I/O and CSV
      writing excluded from the timed region.

    - Whether the cache wins depends on graph size and the ratio of
      lateral root tips to total nodes: attach_distances pays a cost
      roughly proportional to nodes^2 up front to serve a number of
      lookups proportional to tip count. One arbor isn't representative
      of that trade-off, so this samples several arbors spanning a
      range of sizes from the real dataset (via get_last_day_files())
      rather than hardcoding one file.

    - Ratios need enough repeats + a warm-up pass + a monotonic clock
      to be trustworthy, and should be averaged with a geometric mean
      (the correct way to aggregate speedup factors), not an arithmetic
      one, which skews toward outlier wins.

    - A correctness guard skips (and flags) any arbor where old and new
      disagree on the computed delay, since a "speedup" from computing
      the wrong thing isn't a speedup.

Run from the project root:
    python benchmarks/speedup_test.py
"""

import time
import os
import sys
import math
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plant_gravitropism as pg_old
import plant_gravitropism_new as pg_new
import read_arbor_reconstruction as rar

# How many candidate arbors (from the full dataset) to size up before picking
# a spread of small/medium/large ones to actually time.
SCAN_LIMIT = 30
# How many arbors (spread across the size range) to run the timed comparison on.
SAMPLE_SIZE = 5
# Repeats per arbor per pipeline version. Increase for noisier/smaller arbors,
# decrease if the sample includes very large graphs and runtime matters.
N_REPEATS = 50
# Warm-up calls before the timed window starts, per arbor per version.
N_WARMUP = 2


def candidate_arbors():
    """Real arbor filenames from the dataset that have reconstructions available."""
    all_files = pg_old.get_last_day_files()
    valid = []
    for fname in all_files:
        try:
            if rar.has_reconstruction(fname):
                valid.append(fname)
        except Exception as e:
            print(f"  skipping {fname}: {e}")
            continue
        if len(valid) >= SCAN_LIMIT:
            break
    return valid


def profile_arbor(fname):
    """Return (fname, n_nodes, n_tips), or None if the file couldn't be read."""
    try:
        arbor = rar.read_arbor_full(fname)
    except Exception as e:
        print(f"  could not read {fname}: {e}")
        return None
    n_nodes = arbor.number_of_nodes()
    n_tips = sum(1 for u in arbor.nodes() if arbor.nodes[u]['label'] == 'lateral root tip')
    return fname, n_nodes, n_tips


def pick_size_spread(profiles, k):
    """Pick k arbors spread evenly across the size range (by node count)."""
    if k <= 1 or len(profiles) <= k:
        return profiles
    ordered = sorted(profiles, key=lambda p: p[1])
    idxs = [round(i * (len(ordered) - 1) / (k - 1)) for i in range(k)]
    seen = set()
    picks = []
    for i in idxs:
        if i not in seen:
            seen.add(i)
            picks.append(ordered[i])
    return picks


def time_conduction_delay(pf_module, arbor, attach_first, n_repeats, n_warmup):
    """
    Time pf_module.conduction_delay(arbor) directly — no file I/O, no CSV
    writing. If attach_first, pf_module.attach_distances(arbor) runs inside
    the timed region each repeat too, since that's the real per-arbor cost
    the new pipeline actually pays (it's not reused across arbors).
    """
    def run_once():
        if attach_first:
            pf_module.attach_distances(arbor)
        return pf_module.conduction_delay(arbor)

    for _ in range(n_warmup):
        run_once()

    samples = []
    result = None
    for _ in range(n_repeats):
        start = time.perf_counter()
        result = run_once()
        samples.append(time.perf_counter() - start)

    return result, samples


def summarize(samples):
    return {
        'mean': statistics.mean(samples),
        'median': statistics.median(samples),
        'stdev': statistics.stdev(samples) if len(samples) > 1 else 0.0,
    }


def geometric_mean(values):
    try:
        return statistics.geometric_mean(values)
    except AttributeError:  # Python < 3.8
        return math.exp(statistics.mean(math.log(v) for v in values))


def main():
    print("Selecting arbors to benchmark...")
    candidates = candidate_arbors()
    if not candidates:
        print("No arbors with reconstructions found — check dataset paths.")
        return

    profiles = [p for p in (profile_arbor(f) for f in candidates) if p is not None]
    if not profiles:
        print("No arbors could be read — check dataset paths.")
        return

    sample = pick_size_spread(profiles, SAMPLE_SIZE)

    print(f"Benchmarking {len(sample)} arbor(s), {N_REPEATS} repeats each "
          f"({N_WARMUP} warm-up calls excluded from timing):\n")

    rows = []
    for fname, n_nodes, n_tips in sample:
        old_arbor = rar.read_arbor_full(fname)
        new_arbor = rar.read_arbor_full(fname)  # separate object per version

        old_delay, old_samples = time_conduction_delay(
            pg_old.pf, old_arbor, attach_first=False, n_repeats=N_REPEATS, n_warmup=N_WARMUP)
        new_delay, new_samples = time_conduction_delay(
            pg_new.pf, new_arbor, attach_first=True, n_repeats=N_REPEATS, n_warmup=N_WARMUP)

        # Correctness guard — a "speedup" from computing the wrong thing isn't a speedup.
        if abs(old_delay - new_delay) > 1e-6:
            print(f"{fname}")
            print(f"  WARNING: delay mismatch (old={old_delay:.6f}, new={new_delay:.6f}) "
                  f"— excluded from results.\n")
            continue

        old_stats = summarize(old_samples)
        new_stats = summarize(new_samples)
        speedup = old_stats['mean'] / new_stats['mean'] if new_stats['mean'] > 0 else float('inf')
        diff_ms = (old_stats['mean'] - new_stats['mean']) * 1000

        rows.append((fname, n_nodes, n_tips, old_stats, new_stats, speedup))

        print(f"{fname}")
        print(f"  nodes={n_nodes}, lateral tips={n_tips}")
        print(f"  old: mean={old_stats['mean']*1000:.3f}ms  median={old_stats['median']*1000:.3f}ms  "
              f"stdev={old_stats['stdev']*1000:.3f}ms")
        print(f"  new: mean={new_stats['mean']*1000:.3f}ms  median={new_stats['median']*1000:.3f}ms  "
              f"stdev={new_stats['stdev']*1000:.3f}ms")
        print(f"  speedup: {speedup:.2f}x ({diff_ms:+.3f}ms/call) "
              f"{'— new faster' if speedup > 1 else '— old faster'}\n")

    if not rows:
        print("No valid comparisons completed.")
        return

    speedups = [r[5] for r in rows]
    faster_count = sum(1 for s in speedups if s > 1)

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  new pipeline faster on {faster_count}/{len(rows)} arbors")
    print(f"  geometric mean speedup: {geometric_mean(speedups):.2f}x  "
          f"(correct way to average ratios)")
    print(f"  arithmetic mean speedup: {statistics.mean(speedups):.2f}x  (reference only — "
          f"skews toward outlier wins)")
    print(f"  speedup range: {min(speedups):.2f}x - {max(speedups):.2f}x")

    print("\n  size vs. speedup (smallest to largest arbor):")
    for fname, n_nodes, n_tips, _, _, speedup in sorted(rows, key=lambda r: r[1]):
        print(f"    nodes={n_nodes:>5}  tips={n_tips:>4}  speedup={speedup:.2f}x")


if __name__ == '__main__':
    main()
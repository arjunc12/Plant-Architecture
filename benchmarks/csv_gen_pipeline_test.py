"""
benchmarks/csv_gen_pipeline_test.py

Compares the CSV generation pipeline using the original
pareto_functions.py / plant_gravitropism.py against the new
pareto_functions_new.py / plant_gravitropism_new.py, which caches
all-pairs shortest path lengths on the observed arbor graph
(pareto_functions_new.attach_distances) so conduction_delay looks up
distances instead of re-running a shortest-path search per lateral
root tip.

What this benchmarks, and why:

    1. initialize_file() in isolation, repeated over several calls.
       This is the ONLY function that differs between the two
       pipelines — it's where attach_distances is called, once per
       arbor, right before conduction_delay runs on the observed
       graph. This isolates the actual effect of the optimization.

    2. The full CSV-gen pipeline (initialize_file + process_arbor over
       the full (G, alpha) grid). Included for completeness, but
       expect old and new to look nearly identical here — the grid
       sweep is dominated by evaluate_parameters, which neither
       version changed.

    3. A correctness check: confirms observed wiring cost and
       conduction delay match between pipelines, so the caching
       change hasn't altered results, only how they're computed.

Whether the cache is actually a net win depends on the ratio of
lateral root tips to total nodes in the arbor — attach_distances
computes distances between EVERY pair of nodes, which only pays off
if enough of those pairs get looked up afterward. This script prints
the arbor's size so that ratio is visible alongside the timing.

Assumes pareto_functions.py, pareto_functions_new.py,
plant_gravitropism.py, and plant_gravitropism_new.py all live in the
project root (one directory up from this benchmarks/ folder), same
as timing_test.py.

Run from the project root:
    python benchmarks/pipeline_comparison_test.py
"""

import time
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plant_gravitropism as pg_old
#import alternate_csv_gen.plant_gravitropism_new_v2 as pg_new
import plant_gravitropism_new as pg_new

# Arbor file to benchmark on — same one used in timing_test.py
FNAME = "pimpi_Big4_D5_set1_day5_20191012_297_103_4_S.csv"

TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_pipeline_benchmark")
OLD_OUT = os.path.join(TMP_DIR, "old_" + FNAME)
NEW_OUT = os.path.join(TMP_DIR, "new_" + FNAME)

N_REPEATS = 20  # repeats for the isolated initialize_file timing


def reset_output(fname):
    if os.path.exists(fname):
        os.remove(fname)


def describe_arbor(pg_module):
    """Print node / lateral-tip counts so the timing results have context."""
    arbor = pg_module.rar.read_arbor_full(FNAME)
    n_nodes = arbor.number_of_nodes()
    n_tips = sum(1 for u in arbor.nodes() if arbor.nodes[u]['label'] == 'lateral root tip')
    print(f"Arbor: {FNAME}")
    print(f"  total nodes: {n_nodes}")
    print(f"  lateral root tips: {n_tips}")
    print(f"  (all-pairs cache computes {n_nodes * n_nodes:,} distances "
          f"to serve ~{n_tips} lookups per arbor)\n")


def time_initialize_file(pg_module, out_fname, n_repeats):
    cost_specs = pg_module.pf.resolve_cost_specs('homogeneous')
    total = 0.0
    last_row = None
    for _ in range(n_repeats):
        reset_output(out_fname)
        start = time.time()
        pg_module.initialize_file(out_fname, FNAME, cost_specs=cost_specs)
        total += time.time() - start
        with open(out_fname) as f:
            last_row = f.readlines()[1]  # header, then the 'observed' row
    return total, last_row


def time_full_pipeline(pg_module, out_fname, params):
    cost_specs = pg_module.pf.resolve_cost_specs('homogeneous')
    reset_output(out_fname)
    start = time.time()
    skip = pg_module.initialize_file(out_fname, FNAME, cost_specs=cost_specs)
    pg_module.process_arbor(FNAME, out_fname, params, skip, cost_specs=cost_specs)
    return time.time() - start


def parse_observed_row(row):
    """Extract (wiring cost, conduction delay) floats from an 'observed' CSV row."""
    fields = [f.strip() for f in row.split(',')]
    # arbor type, cost method, G, alpha, wiring cost, conduction delay, ...
    return float(fields[4]), float(fields[5])


def main():
    os.makedirs(TMP_DIR, exist_ok=True)

    describe_arbor(pg_old)

    # -------------------------
    # 1. Isolated initialize_file timing (the actual optimized code path)
    # -------------------------
    print(f"Timing initialize_file() over {N_REPEATS} repeats (fresh file each time)...")
    old_total, old_row = time_initialize_file(pg_old, OLD_OUT, N_REPEATS)
    new_total, new_row = time_initialize_file(pg_new, NEW_OUT, N_REPEATS)

    print(f"  old (pareto_functions.py):     {old_total:.3f}s total, "
          f"{old_total / N_REPEATS * 1000:.2f}ms/call")
    print(f"  new (pareto_functions_new.py): {new_total:.3f}s total, "
          f"{new_total / N_REPEATS * 1000:.2f}ms/call")
    if new_total > 0:
        print(f"  speedup: {old_total / new_total:.2f}x")
    else:
        print("  new_total was 0s — too fast to measure reliably, try increasing N_REPEATS")

    # -------------------------
    # 2. Correctness check
    # -------------------------
    old_wiring, old_delay = parse_observed_row(old_row)
    new_wiring, new_delay = parse_observed_row(new_row)
    wiring_match = abs(old_wiring - new_wiring) < 1e-6
    delay_match = abs(old_delay - new_delay) < 1e-6

    print("\nCorrectness check (observed wiring cost / conduction delay):")
    print(f"  old: wiring={old_wiring:.6f}, delay={old_delay:.6f}")
    print(f"  new: wiring={new_wiring:.6f}, delay={new_delay:.6f}")
    print(f"  {'PASS' if (wiring_match and delay_match) else 'FAIL — results differ!'}")

    # -------------------------
    # 3. Full pipeline timing (initialize_file + full grid sweep)
    # -------------------------
    params = list(pg_old.generate_grid(0, 1, 0.05, -2, 2, 0.2))
    print(f"\nTiming full pipeline ({len(params)} parameter combinations)...")
    print("(expect old ~= new here — evaluate_parameters wasn't changed by either version)")

    old_pipeline_time = time_full_pipeline(pg_old, OLD_OUT, params)
    new_pipeline_time = time_full_pipeline(pg_new, NEW_OUT, params)

    print(f"  old pipeline: {old_pipeline_time:.1f}s")
    print(f"  new pipeline: {new_pipeline_time:.1f}s")

    # -------------------------
    # Cleanup
    # -------------------------
    shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == '__main__':
    main()
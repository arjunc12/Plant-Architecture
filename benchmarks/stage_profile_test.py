"""
benchmarks/stage_profile_test.py

Stage-by-stage timing profile of the CSV-gen pipeline, for both the old
(plant_gravitropism.py / pareto_functions.py) and new
(plant_gravitropism_new.py / pareto_functions_new.py) versions. Meant to be
re-run every time you change the new pipeline, to see exactly which stage
moved and by how much.

Stages measured:
    - worker setup: rar.has_reconstruction() + initialize_file()
    - grid generation: materializing generate_grid()
    - arbor_best_cost, split into:
        a) setup — get_main_root_segments, compute_main_root_base_distances,
           get_insertion_segment (old pipeline calls these directly inside
           arbor_best_cost; new pipeline calls them from inside
           attach_main_root_cache instead — see note below)
        b) optimize_tip
      (retrieving lateral root tips is a single inline list comprehension in
      both pipelines, not a separate function, so it can't be isolated
      without editing pipeline source — its cost is small and folds into
      whichever of the above it sits next to.)
    - calculate_orthogonal_errors (called from within evaluate_parameters)
    - evaluate_parameters as a whole

Bonus (not explicitly requested, but cheap to add and useful given the
find_best_cost_brute_force / find_best_cost_brent split discussed earlier):
    - find_best_cost_brute_force / find_best_cost_brent / find_best_cost_analytical

HOW THIS WORKS
    Rather than reimplementing each pipeline's internals here (which would
    drift out of sync as you edit the real files), this monkey-patches the
    actual functions in plant_gravitropism / plant_gravitropism_new with
    timing wrappers, then runs the real evaluate_parameters grid sweep
    through the unmodified pipeline code. The wrappers record cumulative
    time and call count as those functions are genuinely invoked — so the
    numbers reflect exactly what the real code is doing, nested calls and
    all. Patched functions are restored afterward.

IMPORTANT — read before interpreting results:
    These are INCLUSIVE (wall-clock) times, not "self time" — e.g.
    "evaluate_parameters" includes "arbor_best_cost" which includes
    "optimize_tip". Don't sum unrelated rows expecting them to add up to
    something new.

    The new pipeline moved segment/distance/insertion-segment setup OUT of
    arbor_best_cost and into a separate attach_main_root_cache() call (run
    once per evaluate_parameters call, before arbor_best_cost). That means
    "arbor_best_cost total" will look dramatically smaller for the new
    pipeline even if that work hasn't actually gotten any cheaper — it just
    moved to a sibling stage. Compare "evaluate_parameters (total)" and the
    overall wall-clock time for the real apples-to-apples comparison; don't
    read a small "arbor_best_cost" number alone as a win.

    Correctness (do old and new agree on wiring/delay?) is validated
    separately in pipeline_comparison_test.py and speedup_test.py. This
    script only does a light summed sanity check, since its job is timing.

Run from the project root:
    python benchmarks/stage_profile_test.py
"""

import time
import os
import sys
import shutil
import functools
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plant_gravitropism as pg_old
import plant_gravitropism_new as pg_new

FNAME = "pimpi_Big4_D5_set1_day5_20191012_297_103_4_S.csv"

TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_stage_profile")
OLD_OUT = os.path.join(TMP_DIR, "old_" + FNAME)
NEW_OUT = os.path.join(TMP_DIR, "new_" + FNAME)

# Standard grid, matching the rest of the pipeline's defaults (441 points).
# Shrink ASTEP/GSTEP below for a faster dev-loop while iterating; restore to
# these values for a final before/after comparison.
AMIN, AMAX, ASTEP = 0, 1, 0.05
GMIN, GMAX, GSTEP = -2, 2, 0.2

COST_METHOD = 'homogeneous'
PROGRESS_EVERY = 50  # print a progress line every N grid points

# (function name to patch, human-readable stage label)
STAGE_TARGETS = [
    ('initialize_file', 'worker setup (initialize_file)'),
    ('get_main_root_segments', 'a) main root segments'),
    ('compute_main_root_base_distances', 'a) main root base distances'),
    ('get_insertion_segment', 'a) insertion/valid segments (per tip)'),
    ('attach_main_root_cache', 'a) main root cache setup [new pipeline only]'),
    ('optimize_tip', 'b) optimize_tip'),
    ('find_best_cost_brute_force', 'c) find_best_cost_brute_force'),
    ('find_best_cost_brent', 'c) find_best_cost_brent'),
    ('find_best_cost_analytical', 'c) find_best_cost_analytical'),
    ('arbor_best_cost', 'arbor_best_cost (total — includes a + b above)'),
    ('calculate_orthogonal_errors', 'orthogonal error calculation'),
    ('evaluate_parameters', 'evaluate_parameters (total — includes everything above)'),
]


class StageStats:
    def __init__(self):
        self.calls = {}
        self.total_time = {}

    def record(self, stage, elapsed):
        self.calls[stage] = self.calls.get(stage, 0) + 1
        self.total_time[stage] = self.total_time.get(stage, 0.0) + elapsed

    def get(self, stage):
        return self.calls.get(stage, 0), self.total_time.get(stage, 0.0)


def _make_wrapper(original, stage_label, stats):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = original(*args, **kwargs)
        stats.record(stage_label, time.perf_counter() - start)
        return result
    return wrapper


@contextmanager
def instrument_pipeline(module, stats):
    """Monkey-patch every function in STAGE_TARGETS that exists on `module`
    with a timing wrapper, and restore the originals on exit (even on error).
    """
    originals = {}
    for func_name, stage_label in STAGE_TARGETS:
        if hasattr(module, func_name):
            original = getattr(module, func_name)
            originals[func_name] = original
            setattr(module, func_name, _make_wrapper(original, stage_label, stats))
    try:
        yield
    finally:
        for func_name, original in originals.items():
            setattr(module, func_name, original)


def reset_output(fname):
    if os.path.exists(fname):
        os.remove(fname)


def run_profiled_pipeline(pg_module, pipeline_label, out_fname):
    stats = StageStats()

    start = time.perf_counter()
    pg_module.rar.has_reconstruction(FNAME)
    reconstruction_check_time = time.perf_counter() - start

    reset_output(out_fname)
    cost_specs = pg_module.pf.resolve_cost_specs(COST_METHOD)
    cost_spec = pg_module.pf.COST_SPECS[COST_METHOD]

    total_wiring = 0.0
    total_delay = 0.0

    overall_start = time.perf_counter()
    with instrument_pipeline(pg_module, stats):
        pg_module.initialize_file(out_fname, FNAME, cost_specs=cost_specs)

        grid_start = time.perf_counter()
        params = list(pg_module.generate_grid(AMIN, AMAX, ASTEP, GMIN, GMAX, GSTEP))
        grid_time = time.perf_counter() - grid_start

        n_points = len(params)
        for i, (g, alpha) in enumerate(params, 1):
            wiring, delay, _, _ = pg_module.evaluate_parameters(FNAME, g, alpha, cost_spec=cost_spec)
            total_wiring += wiring
            total_delay += delay
            if i % PROGRESS_EVERY == 0 or i == n_points:
                print(f"    [{pipeline_label}] {i}/{n_points} grid points evaluated", flush=True)
    overall_time = time.perf_counter() - overall_start

    return {
        'stats': stats,
        'reconstruction_check_time': reconstruction_check_time,
        'grid_generation_time': grid_time,
        'overall_time': overall_time,
        'total_wiring': total_wiring,
        'total_delay': total_delay,
        'n_points': n_points,
    }


def print_stage_report(label, result):
    stats = result['stats']
    print(f"\n{label}")
    print(f"  has_reconstruction check: {result['reconstruction_check_time']*1000:.2f}ms")
    print(f"  grid generation ({result['n_points']} points): {result['grid_generation_time']*1000:.2f}ms")
    print(f"  full simulated run (setup + grid + all evaluate_parameters calls): "
          f"{result['overall_time']:.2f}s")
    print(f"  observed totals — wiring: {result['total_wiring']:.4f}, delay: {result['total_delay']:.4f}")
    print(f"\n  stage breakdown (nested/inclusive):")
    print(f"    {'stage':52s} {'calls':>8s} {'total':>12s} {'avg/call':>12s}")
    for func_name, stage_label in STAGE_TARGETS:
        calls, total = stats.get(stage_label)
        if calls == 0:
            continue
        avg = total / calls
        print(f"    {stage_label:52s} {calls:>8d} {total*1000:>10.2f}ms {avg*1000:>10.3f}ms")


def print_comparison(old_result, new_result):
    print("\n" + "=" * 84)
    print("OLD vs NEW — stage-by-stage comparison")
    print("=" * 84)
    print(f"{'stage':52s} {'old total':>10s} {'new total':>10s} {'speedup':>8s}")

    old_stats = old_result['stats']
    new_stats = new_result['stats']

    for func_name, stage_label in STAGE_TARGETS:
        old_calls, old_total = old_stats.get(stage_label)
        new_calls, new_total = new_stats.get(stage_label)
        if old_calls == 0 and new_calls == 0:
            continue

        old_str = f"{old_total*1000:.1f}ms" if old_calls else "n/a"
        new_str = f"{new_total*1000:.1f}ms" if new_calls else "n/a"
        if old_calls and new_calls and new_total > 0:
            speedup = f"{old_total / new_total:.2f}x"
        else:
            speedup = "n/a"

        note = ""
        if old_calls and not new_calls:
            note = "  (old only — folded elsewhere in new pipeline)"
        elif new_calls and not old_calls:
            note = "  (new only — see architecture note in docstring)"

        print(f"{stage_label:52s} {old_str:>10s} {new_str:>10s} {speedup:>8s}{note}")

    print(f"\n  full run — old: {old_result['overall_time']:.2f}s   "
          f"new: {new_result['overall_time']:.2f}s   "
          f"speedup: {old_result['overall_time']/new_result['overall_time']:.2f}x")
    print("  (this overall number, not the arbor_best_cost row alone, is the fair "
          "before/after comparison — see docstring)")

    wiring_diff = abs(old_result['total_wiring'] - new_result['total_wiring'])
    delay_diff = abs(old_result['total_delay'] - new_result['total_delay'])
    print(f"\n  sanity check — summed wiring/delay across the whole grid "
          f"(full correctness lives in pipeline_comparison_test.py / speedup_test.py):")
    print(f"    wiring diff: {wiring_diff:.6f}   delay diff: {delay_diff:.6f}")


def main():
    os.makedirs(TMP_DIR, exist_ok=True)

    print(f"Profiling arbor: {FNAME}")
    print(f"Grid: amin={AMIN} amax={AMAX} astep={ASTEP}  Gmin={GMIN} Gmax={GMAX} Gstep={GSTEP}")
    print("(shrink astep/Gstep above for a faster dev-loop while iterating)\n")

    print("Running OLD pipeline (plant_gravitropism.py / pareto_functions.py)...")
    old_result = run_profiled_pipeline(pg_old, "OLD", OLD_OUT)

    print("\nRunning NEW pipeline (plant_gravitropism_new.py / pareto_functions_new.py)...")
    new_result = run_profiled_pipeline(pg_new, "NEW", NEW_OUT)

    print_stage_report("OLD pipeline", old_result)
    print_stage_report("NEW pipeline", new_result)
    print_comparison(old_result, new_result)

    shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == '__main__':
    main()
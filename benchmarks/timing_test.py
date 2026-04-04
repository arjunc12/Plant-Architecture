"""
benchmarks/timing_test.py

Benchmarks the three optimization methods (brute_force, brent, analytical)
for finding the optimal branch point on the main root for each lateral tip,
and separately benchmarks the orthogonal distance calculation.

Expected results (as of the optimizations made in 2025):
    - brute_force:  ~8-9s  for 441 parameter combinations
    - brent:        ~8-9s  for 441 parameter combinations  (recommended default)
    - analytical:   ~18s   for 441 parameter combinations  (fsolve, not recommended)
    - orthogonal:   ~0.2s  for 441 parameter combinations  (vectorized numpy)
    - full pipeline (evaluate_parameters, brent): ~8.3s for 441 combinations

Key optimizations that produced these numbers:
    - Closed-form arc length (replaces scipy.integrate.quad)
    - Vectorized numpy orthogonal distance (replaces Python for loop)
    - Single file read per evaluate_parameters call (eliminates duplicate I/O)

Run from the project root:
    python benchmarks/timing_test.py
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plant_gravitropism as pg

# Arbor file to benchmark on — should have a moderate number of lateral roots
FNAME = "pimpi_Big4_D5_set1_day5_20191012_297_103_4_S.csv"

params = list(pg.generate_grid(0, 1, 0.05, -2, 2, 0.2))
print(f"Benchmarking {len(params)} parameter combinations on {FNAME}\n")

# -------------------------
# Optimization methods
# -------------------------
for method in ['brute_force', 'brent', 'analytical']:
    pg.OPTIMIZATION_METHOD = method
    start = time.time()
    for g, alpha in params:
        pg.arbor_best_cost(pg.rar.read_arbor_full(FNAME), g, alpha)
    elapsed = time.time() - start
    print(f"{method}: {elapsed:.1f}s")

# -------------------------
# Orthogonal distance calculation in isolation
# -------------------------
print()
arbor = pg.rar.read_arbor_full(FNAME)
# Use arbitrary G/alpha to get a set of results to compute distances for
results = pg.arbor_best_cost(arbor, 0.0, 0.5)

start = time.time()
for g, alpha in params:
    for result in results:
        main_root_pt = (result[4], result[5])
        lateral_tip = (result[6], result[7])
        pg.calculate_orthogonal_errors(g, arbor, main_root_pt, lateral_tip)
elapsed = time.time() - start
print(f"orthogonal distance only: {elapsed:.1f}s")

# -------------------------
# Full pipeline (recommended method)
# -------------------------
print()
pg.OPTIMIZATION_METHOD = 'brent'
start = time.time()
for g, alpha in params:
    pg.evaluate_parameters(FNAME, g, alpha)
elapsed = time.time() - start
print(f"evaluate_parameters (brent, full pipeline): {elapsed:.1f}s")
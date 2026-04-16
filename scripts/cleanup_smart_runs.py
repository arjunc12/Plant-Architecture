import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pylab
from constants import RESULTS_DIR

# -------------------------
# Define all valid coarse grid points
# -------------------------

# Main coarse grid: G in [-5, 5] step 0.5, alpha in [0, 1] step 0.05
G_vals_coarse = set(round(g, 6) for g in pylab.arange(-5, 5.01, 0.5))
a_vals_coarse = set(round(a, 6) for a in pylab.arange(0, 1.01, 0.05))

coarse_pairs = set(
    (g, a)
    for g in G_vals_coarse
    for a in a_vals_coarse
)

# G=0 fine alpha sweep: G=0, alpha in [0, 1] step 0.01
G0_pairs = set(
    (0.0, round(a, 6))
    for a in pylab.arange(0, 1.01, 0.01)
)

# All valid points to keep
valid_pairs = coarse_pairs | G0_pairs

print(f"Total valid coarse grid points: {len(valid_pairs)}")

# -------------------------
# Clean up each pareto front
# -------------------------
path = f'{RESULTS_DIR}/gravitropism_pareto_fronts'

total_removed = 0
files_cleaned = 0

for fname in sorted(os.listdir(path)):
    if not fname.endswith('.csv'):
        continue
    fpath = f'{path}/{fname}'
    if os.path.getsize(fpath) == 0:
        continue
    print(fpath)

    df = pd.read_csv(fpath, skipinitialspace=True)
    df_obs = df[df['arbor type'] == 'observed']
    df_opt = df[df['arbor type'] == 'optimal'].copy()

    # Keep only rows whose (G, alpha) pair is in the valid set
    mask = df_opt.apply(
        lambda row: (round(float(row['G']), 6), round(float(row['alpha']), 6)) in valid_pairs,
        axis=1
    )
    df_opt_clean = df_opt[mask]

    n_removed = len(df_opt) - len(df_opt_clean)
    total_removed += n_removed
    if n_removed > 0:
        files_cleaned += 1

    df_clean = pd.concat([df_obs, df_opt_clean], ignore_index=True)

    # Sort by G then alpha for readability
    df_obs_out = df_clean[df_clean['arbor type'] == 'observed']
    df_opt_out = df_clean[df_clean['arbor type'] == 'optimal'].sort_values(['G', 'alpha'])
    df_clean = pd.concat([df_obs_out, df_opt_out], ignore_index=True)

    # Write back with spaces after commas
    cols = df_clean.columns.tolist()
    lines = [', '.join(cols)]
    for _, row in df_clean.iterrows():
        parts = []
        for col in cols:
            val = row[col]
            if pd.isna(val):
                parts.append('')
            elif col == 'arbor type':
                parts.append(str(val))
            else:
                parts.append(f'{float(val):.6f}')
        lines.append(', '.join(parts))

    with open(fpath, 'w') as f:
        f.write('\n'.join(lines) + '\n')

print(f'\nRemoved {total_removed} smart grid rows across {files_cleaned} files.')
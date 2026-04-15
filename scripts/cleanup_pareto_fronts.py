"""
scripts/cleanup_pareto_fronts.py

Removes duplicate (G, alpha) rows from each pareto front CSV,
sorts by G then alpha, and rewrites with spaces after commas for readability.

Run from project root:
    python scripts/cleanup_pareto_fronts.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from constants import RESULTS_DIR


def cleanup_pareto_front(fpath):
    """
    Clean up a single pareto front CSV:
    - Remove duplicate (G, alpha) rows
    - Sort by G then alpha
    - Rewrite with spaces after commas
    """
    df = pd.read_csv(fpath, skipinitialspace=True)

    n_before = len(df)

    df_obs = df[df['arbor type'] == 'observed'].copy()
    df_opt = df[df['arbor type'] == 'optimal'].copy()

    # Remove duplicates on (G, alpha) keeping first occurrence
    df_opt = df_opt.drop_duplicates(subset=['G', 'alpha'], keep='first')

    # Sort by G then alpha
    df_opt = df_opt.sort_values(['G', 'alpha']).reset_index(drop=True)

    df_clean = pd.concat([df_obs, df_opt], ignore_index=True)

    n_after = len(df_clean)
    n_removed = n_before - n_after

    # Write back with spaces after commas for readability
    # pandas to_csv doesn't support spaces after commas natively,
    # so we format manually
    cols = df_clean.columns.tolist()
    header = ', '.join(cols)

    lines = [header]
    for _, row in df_clean.iterrows():
        parts = []
        for col in cols:
            val = row[col]
            if pd.isna(val):
                parts.append('')
            elif col in ('G', 'alpha'):
                parts.append(f'{float(val):.6f}')
            elif col == 'arbor type':
                parts.append(str(val))
            else:
                parts.append(f'{float(val):.6f}')
        lines.append(', '.join(parts))

    with open(fpath, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    return n_removed


def main():
    path = f'{RESULTS_DIR}/gravitropism_pareto_fronts'

    total_removed = 0
    files_cleaned = 0

    for fname in sorted(os.listdir(path)):
        if not fname.endswith('.csv'):
            continue

        fpath = f'{path}/{fname}'

        if os.path.getsize(fpath) == 0:
            continue

        n_removed = cleanup_pareto_front(fpath)

        if n_removed > 0:
            print(f"{fname}: removed {n_removed} duplicate rows")
            total_removed += n_removed
            files_cleaned += 1

    print(f"\nDone. Removed {total_removed} duplicate rows across {files_cleaned} files.")


if __name__ == '__main__':
    main()

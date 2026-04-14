import pandas as pd
from scipy.spatial.distance import euclidean
from constants import *
import pareto_functions as pf
import os


# -------------------------
# Output file paths — one per phenotype
# -------------------------
BEST_OF_BEST_DIR = '%s/gravitropism_results' % RESULTS_DIR

OUTPUT_FILES = {
    'orthogonal':       '%s/best_orthogonal.csv'        % BEST_OF_BEST_DIR,
    'sq_orthogonal':    '%s/best_sq_orthogonal.csv'     % BEST_OF_BEST_DIR,
    'G0_orthogonal':    '%s/best_G0_orthogonal.csv'     % BEST_OF_BEST_DIR,
    'G0_sq_orthogonal': '%s/best_G0_sq_orthogonal.csv'  % BEST_OF_BEST_DIR,
    'G0_pareto_dist':   '%s/best_G0_pareto_dist.csv'    % BEST_OF_BEST_DIR,
    'G0_pareto_scale':  '%s/best_G0_pareto_scale.csv'   % BEST_OF_BEST_DIR,
}


def best_rows(df, metric):
    """
    Return all rows tied for the minimum value of metric,
    within floating point tolerance.
    """
    min_val = df[metric].min()
    return df[df[metric] <= min_val * (1 + 1e-9)]


def process_pareto_front(pareto_front_path):
    """
    Process a single pareto front CSV and return a dict of results
    keyed by phenotype name.

    Each value is a list of rows (one per tied best point) rather than
    a single row — ties produce multiple rows in the output files,
    all sharing the same arbor name.

    The observed row contains wiring cost and conduction delay for
    the actual arbor — no need to read the reconstruction.

    Returns
    -------
    dict mapping phenotype name -> list of row dicts, or None if file is invalid
    """
    df = pd.read_csv(pareto_front_path, skipinitialspace=True)

    arbor_name = os.path.basename(pareto_front_path).replace('.csv', '')

    # -------------------------
    # Extract observed wiring/delay from the 'observed' row
    # -------------------------
    df_obs = df[df['arbor type'] == 'observed']
    df_opt = df[df['arbor type'] == 'optimal'].copy()

    if df_opt.empty:
        return None

    obs_wiring = df_obs['wiring cost'].iloc[0] if not df_obs.empty else None
    obs_delay  = df_obs['conduction delay'].iloc[0] if not df_obs.empty else None

    results = {}

    # -------------------------
    # Phenotype 1: best G/alpha by orthogonal distance (all G)
    # One row per tied (G, alpha) combination
    # -------------------------
    best = best_rows(df_opt, 'total orthogonal distance')
    results['orthogonal'] = [
        {
            'arbor name':               arbor_name,
            'best G':                   row['G'],
            'best alpha':               row['alpha'],
            'best orthogonal distance': row['total orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # -------------------------
    # Phenotype 2: best G/alpha by squared orthogonal distance (all G)
    # -------------------------
    best = best_rows(df_opt, 'total squared orthogonal distance')
    results['sq_orthogonal'] = [
        {
            'arbor name':                       arbor_name,
            'best G':                           row['G'],
            'best alpha':                       row['alpha'],
            'best squared orthogonal distance': row['total squared orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # -------------------------
    # G=0 slice — used for phenotypes 3-6
    # -------------------------
    df_G0 = df_opt[df_opt['G'].round(6) == 0.0].copy()

    if df_G0.empty:
        for key in ['G0_orthogonal', 'G0_sq_orthogonal', 'G0_pareto_dist', 'G0_pareto_scale']:
            results[key] = []
        return results

    # -------------------------
    # Phenotype 3: best alpha at G=0 by orthogonal distance
    # -------------------------
    best = best_rows(df_G0, 'total orthogonal distance')
    results['G0_orthogonal'] = [
        {
            'arbor name':               arbor_name,
            'best alpha':               row['alpha'],
            'best orthogonal distance': row['total orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # -------------------------
    # Phenotype 4: best alpha at G=0 by squared orthogonal distance
    # -------------------------
    best = best_rows(df_G0, 'total squared orthogonal distance')
    results['G0_sq_orthogonal'] = [
        {
            'arbor name':                       arbor_name,
            'best alpha':                       row['alpha'],
            'best squared orthogonal distance': row['total squared orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # -------------------------
    # Phenotypes 5 & 6: pareto distance metrics at G=0
    # Only meaningful at G=0, and only if we have observed wiring/delay
    # -------------------------
    if obs_wiring is not None and obs_delay is not None:

        # Compute distance from observed point to each G=0 optimized point
        df_G0['pareto_dist'] = df_G0.apply(
            lambda r: euclidean(
                (obs_wiring, obs_delay),
                (r['wiring cost'], r['conduction delay'])
            ), axis=1
        )

        df_G0['pareto_scale'] = df_G0.apply(
            lambda r: pf.point_dist_scale(
                (r['wiring cost'], r['conduction delay']),
                (obs_wiring, obs_delay)
            ), axis=1
        )

        # Phenotype 5: best alpha at G=0 by pareto distance
        best = best_rows(df_G0, 'pareto_dist')
        results['G0_pareto_dist'] = [
            {
                'arbor name':       arbor_name,
                'best alpha':       row['alpha'],
                'best pareto dist': row['pareto_dist'],
            }
            for _, row in best.iterrows()
        ]

        # Phenotype 6: best alpha at G=0 by scaled pareto distance
        best = best_rows(df_G0, 'pareto_scale')
        results['G0_pareto_scale'] = [
            {
                'arbor name':        arbor_name,
                'best alpha':        row['alpha'],
                'best pareto scale': row['pareto_scale'],
            }
            for _, row in best.iterrows()
        ]

    else:
        results['G0_pareto_dist']  = []
        results['G0_pareto_scale'] = []

    return results


def main():
    path = '%s/gravitropism_pareto_fronts' % RESULTS_DIR

    # Accumulate rows per phenotype
    all_rows = {key: [] for key in OUTPUT_FILES}

    for pareto_front in sorted(os.listdir(path)):
        if not pareto_front.endswith('.csv'):
            continue

        pareto_front_path = '%s/%s' % (path, pareto_front)

        if os.path.getsize(pareto_front_path) == 0:
            continue

        print(f"Processing {pareto_front}")

        results = process_pareto_front(pareto_front_path)
        if results is None:
            continue

        # Each phenotype returns a list of rows — extend rather than append
        for key, rows in results.items():
            all_rows[key].extend(rows)

    # Write one file per phenotype
    for key, rows in all_rows.items():
        df_out = pd.DataFrame(rows)
        df_out.to_csv(OUTPUT_FILES[key], index=False)
        print(f"Wrote {len(rows)} rows to {OUTPUT_FILES[key]}")


if __name__ == '__main__':
    main()

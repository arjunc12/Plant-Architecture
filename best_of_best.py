import pandas as pd
from scipy.spatial.distance import euclidean
from constants import *
import pareto_functions as pf
import os


OUTPUT_FILES = {
    'orthogonal':        '%s/best_orthogonal.csv'        % BEST_OF_BEST_DIR,
    'sq_orthogonal':     '%s/best_sq_orthogonal.csv'     % BEST_OF_BEST_DIR,
    'G0_orthogonal':     '%s/best_G0_orthogonal.csv'     % BEST_OF_BEST_DIR,
    'G0_sq_orthogonal':  '%s/best_G0_sq_orthogonal.csv'  % BEST_OF_BEST_DIR,
    'pareto_dist':       '%s/best_pareto_dist.csv'       % BEST_OF_BEST_DIR,
    'pareto_scale':      '%s/best_pareto_scale.csv'      % BEST_OF_BEST_DIR,
    'G0_pareto_dist':    '%s/best_G0_pareto_dist.csv'    % BEST_OF_BEST_DIR,
    'G0_pareto_scale':   '%s/best_G0_pareto_scale.csv'   % BEST_OF_BEST_DIR,
}


def best_rows(df, metric):
    """Return all rows tied for the minimum value of metric."""
    min_val = df[metric].min()
    return df[df[metric] <= min_val * (1 + 1e-9)]


def best_rows_closest_to_one(df, metric):
    """
    Return all rows whose value of metric is closest to 1.
    Used for pareto_scale where 1 means most similar to observed.
    """
    closest = (df[metric] - 1.0).abs().min()
    return df[(df[metric] - 1.0).abs() <= closest * (1 + 1e-9) + 1e-12]


def compute_pareto_metrics(df_slice, obs_wiring, obs_delay):
    """
    Add pareto_dist and pareto_scale columns to a dataframe slice.
    pareto_dist: Euclidean distance from observed to optimized point
    pareto_scale: ratio of observed to optimized costs (closest to 1 = most similar)
    """
    df_slice = df_slice.copy()
    df_slice['pareto_dist'] = df_slice.apply(
        lambda r: euclidean(
            (obs_wiring, obs_delay),
            (r['wiring cost'], r['conduction delay'])
        ), axis=1
    )
    df_slice['pareto_scale'] = df_slice.apply(
        lambda r: pf.point_dist_scale(
            (r['wiring cost'], r['conduction delay']),
            (obs_wiring, obs_delay)
        ), axis=1
    )
    return df_slice


def process_pareto_front(pareto_front_path):
    df = pd.read_csv(pareto_front_path, skipinitialspace=True)
    arbor_name = os.path.basename(pareto_front_path).replace('.csv', '')

    df_obs = df[df['arbor type'] == 'observed']
    df_opt = df[df['arbor type'] == 'optimal'].copy()

    if df_opt.empty:
        return None

    obs_wiring = df_obs['wiring cost'].iloc[0] if not df_obs.empty else None
    obs_delay  = df_obs['conduction delay'].iloc[0] if not df_obs.empty else None

    results = {}

    # -------------------------
    # Phenotype 1: best G/alpha by orthogonal distance (all G)
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
    # Phenotypes 3 & 4: pareto distance metrics (all G)
    # -------------------------
    if obs_wiring is not None and obs_delay is not None:
        df_opt_pareto = compute_pareto_metrics(df_opt, obs_wiring, obs_delay)

        # Phenotype 3: best (G, alpha) by pareto distance (all G)
        # Tiebreak by orthogonal distance
        best = best_rows(df_opt_pareto, 'pareto_dist')
        if len(best) > 1:
            best = best_rows(best, 'total squared orthogonal distance')
        if len(best) > 1:
            best = best_rows(best, 'total orthogonal distance')
        results['pareto_dist'] = [
            {
                'arbor name':       arbor_name,
                'best G':           row['G'],
                'best alpha':       row['alpha'],
                'best pareto dist': row['pareto_dist'],
            }
            for _, row in best.iterrows()
        ]

        # Phenotype 4: best (G, alpha) by scaled pareto distance (all G)
        # Closest to 1, tiebreak by orthogonal distance
        best = best_rows_closest_to_one(df_opt_pareto, 'pareto_scale')
        if len(best) > 1:
            best = best_rows(best, 'total squared orthogonal distance')
        if len(best) > 1:
            best = best_rows(best, 'total orthogonal distance')
        results['pareto_scale'] = [
            {
                'arbor name':        arbor_name,
                'best G':            row['G'],
                'best alpha':        row['alpha'],
                'best pareto scale': row['pareto_scale'],
            }
            for _, row in best.iterrows()
        ]
    else:
        results['pareto_dist']  = []
        results['pareto_scale'] = []

    # -------------------------
    # G=0 slice — phenotypes 5-8
    # -------------------------
    df_G0 = df_opt[df_opt['G'].round(6) == 0.0].copy()

    if df_G0.empty:
        for key in ['G0_orthogonal', 'G0_sq_orthogonal', 'G0_pareto_dist', 'G0_pareto_scale']:
            results[key] = []
        return results

    # Phenotype 5: best alpha at G=0 by orthogonal distance
    best = best_rows(df_G0, 'total orthogonal distance')
    results['G0_orthogonal'] = [
        {
            'arbor name':               arbor_name,
            'best alpha':               row['alpha'],
            'best orthogonal distance': row['total orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # Phenotype 6: best alpha at G=0 by squared orthogonal distance
    best = best_rows(df_G0, 'total squared orthogonal distance')
    results['G0_sq_orthogonal'] = [
        {
            'arbor name':                       arbor_name,
            'best alpha':                       row['alpha'],
            'best squared orthogonal distance': row['total squared orthogonal distance'],
        }
        for _, row in best.iterrows()
    ]

    # Phenotypes 7 & 8: pareto metrics at G=0
    if obs_wiring is not None and obs_delay is not None:
        df_G0_pareto = compute_pareto_metrics(df_G0, obs_wiring, obs_delay)

        # Phenotype 7: best alpha at G=0 by pareto distance
        best = best_rows(df_G0_pareto, 'pareto_dist')
        if len(best) > 1:
            best = best_rows(best, 'total orthogonal distance')
        results['G0_pareto_dist'] = [
            {
                'arbor name':       arbor_name,
                'best alpha':       row['alpha'],
                'best pareto dist': row['pareto_dist'],
            }
            for _, row in best.iterrows()
        ]

        # Phenotype 8: best alpha at G=0 by scaled pareto distance
        # Closest to 1, tiebreak by orthogonal distance
        best = best_rows_closest_to_one(df_G0_pareto, 'pareto_scale')
        if len(best) > 1:
            best = best_rows(best, 'total orthogonal distance')
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

        for key, rows in results.items():
            all_rows[key].extend(rows)

    for key, rows in all_rows.items():
        df_out = pd.DataFrame(rows)
        df_out.to_csv(OUTPUT_FILES[key], index=False)
        print(f"Wrote {len(rows)} rows to {OUTPUT_FILES[key]}")


if __name__ == '__main__':
    main()
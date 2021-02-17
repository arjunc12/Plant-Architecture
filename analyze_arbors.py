from constants import *
from read_arbor_reconstruction import read_arbor_full
from pareto_functions import pareto_front, pareto_dist, pareto_dist_scale
import numpy as np
import os
import pandas as pd
import argparse

def write_front(G, outdir, alphas, wiring_costs, conduction_delays):
    fname = G.graph['arbor name']
    with open('%s/%s.csv' % (outdir, fname), 'w') as f:
        f.write('alpha, wiring cost, conduction delay\n')
        for alpha, wiring, delay in zip(alphas, wiring_costs, conduction_delays):
            f.write('%f, %f, %f\n' % (alpha, wiring, delay))

def get_pareto_front(G, alphas):
    outdir = PARETO_FRONTS_DIR
    fname = '%s/%s.csv' % (outdir, G.graph['arbor name'])
    if os.path.exists(fname):
        df = pd.read_csv(fname, skipinitialspace=True)
        return list(df['wiring cost']), list(df['conduction delay'])
    else:
        wiring_costs, conduction_delays = pareto_front(G, alphas)
        write_front(G, outdir, alphas, wiring_costs, conduction_delays)
        return wiring_costs, conduction_delays

def analyze_arbors():
    alphas = DEFAULT_ALPHAS
    fname = '%s/arbor_stats.csv' % STATISTICS_DIR
    first_time = not os.path.exists(fname)

    prev_arbors = []
    if not first_time:
        df = pd.read_csv(fname, skipinitialspace=True)
        prev_arbors = list(df['arbor name'])

    with open(fname, 'a') as f:
        if first_time:
            f.write('arbor name, pareto front distance, pareto front location\n')

        for arbor_fname in os.listdir(RECONSTRUCTIONS_DIR):
            if arbor_fname.strip('.csv') in prev_arbors:
                continue
            print(arbor_fname)

            G = read_arbor_full(arbor_fname)
            arbor_name = G.graph['arbor name']

            wiring_costs, conduction_delays = get_pareto_front(G, alphas)

            dist, alpha = pareto_dist(G, alphas, wiring_costs, conduction_delays)
            f.write('%s, %f, %f\n' % (arbor_name, dist, alpha))

def write_scaling_dists():
    alphas = DEFAULT_ALPHAS
    fname = '%s/scaling_distances.csv' % STATISTICS_DIR
    first_time = not os.path.exists(fname)

    prev_arbors = []
    if not first_time:
        df = pd.read_csv(fname, skipinitialspace=True)
        prev_arbors = list(df['arbor name'])

    with open(fname, 'a') as f:
        if first_time:
            f.write('arbor name, pareto front scaling distance, pareto front scaling location')

        for arbor_fname in os.listdir(RECONSTRUCTIONS_DIR):
            if arbor_fname.strip('.csv') in prev_arbors:
                continue

            print(arbor_fname)

            G = read_arbor_full(arbor_fname)
            arbor_name = G.graph['arbor name']

            wiring_costs, conduction_delays = get_pareto_front(G, alphas)

            dist, alpha = pareto_dist_scale(G, alphas, wiring_costs, conduction_delays)
            f.write('%s, %f, %f\n' % (arbor_name, dist, alpha))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze', action='store_true')
    parser.add_argument('--scaling', action='store_true')

    args = parser.parse_args()

    if args.analyze:
        analyze_arbors()
    if args.scaling:
        write_scaling_dists()

if __name__ == '__main__':
    main()

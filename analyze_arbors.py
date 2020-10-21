from constants import *
from read_arbor_reconstruction import read_arbor_full
from pareto_functions import pareto_front, pareto_dist
import numpy as np
import os
import pandas as pd

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
    with open('%s/arbor_stats.csv' % STATISTICS_DIR, 'w') as f:
        f.write('arbor name, pareto front distance, pareto front location\n')
        for arbor_fname in os.listdir(RECONSTRUCTIONS_DIR):
            print(arbor_fname)
            G = read_arbor_full(arbor_fname)
            arbor_name = G.graph['arbor name']

            wiring_costs, conduction_delays = get_pareto_front(G, alphas)

            dist, alpha = pareto_dist(G, alphas, wiring_costs, conduction_delays)
            f.write('%s, %f, %f\n' % (arbor_name, dist, alpha))

def main():
    analyze_arbors()

if __name__ == '__main__':
    main()

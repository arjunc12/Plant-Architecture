from constants import *
from read_arbor_reconstruction import read_arbor
from pareto_functions import pareto_front, pareto_dist
import numpy as np
import os

def write_front(G, outdir, alphas, wiring_costs, conduction_delays):
    fname = G.graph['arbor name']
    with open('%s/%s' % (outdir, fname), 'w') as f:
        f.write('alpha, wiring cost, conduction delay\n')
        for alpha, wiring, delay in zip(alphas, wiring_costs, conduction_delays):
            f.write('%f, %f, %f\n' % (alpha, wiring, delay))

def analyze_arbors():
    alphas = DEFAULT_ALPHAS
    f = open('%s/arbor_stats.csv' % STATISTICS_DIR, 'w')
    f.write('arbor name, pareto front distance, pareto front location\n')
    for arbor_fname in os.listdir(RECONSTRUCTIONS_DIR):
        G = read_arbor(arbor_fname)
        arbor_name = G.graph['arbor name']

        wiring_costs, conduction_delays = pareto_front(G, alphas)
        outdir = PARETO_FRONTS_DIR
        write_front(G, outdir, alphas, wiring_costs, conduction_delays)

        dist, alpha = pareto_dist(G, alphas, wiring_costs, conduction_delays)
        f.write('%s, %f, %f\n' % (arbor_name, dist, alpha))

    f.close()

def main():
    analyze_arbors()

if __name__ == '__main__':
    main()

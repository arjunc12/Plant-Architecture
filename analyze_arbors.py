"""Analyze arbors

This file contains functions for analyzing arbors to create the Pareto 
front.

This file requires `pandas` to be installed.

This file can also be imported as a module and contains the following
functions:
    * write_front - creates a file containing columns of alpha, wiring cost, and conduction delay
    * get_pareto_front - returns a list containing wiring_costs and conduction_delays
    * analyze_arbors -
    * write_scaling_dists - 
    * main - the main function of the file

This file can also be called on its own with arguments `--analyze` 
to run `analyze_arbors()` and `--scaling` to run `write_scaling_dists()`.

"""

from constants import *
from read_arbor_reconstruction import read_arbor_full
import pareto_functions as pf
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
    """Gets the wiring costs and condution delays for the Pareto front.
    If the file already exists it just reads the file. If it does not,
    it will use `pareto_front()` from `pareto_functions.py` to calculate
    the needed information and then write the file using `write_front()` and
    finally returns the wiring costs and conduction delays.

    Parameters
    ----------
    G : graph(?) #TODO: maybe figure out what exactly G is? 
                 #      Could just do type print later for it.
        The graph information of the arbor (maybe)
    alphas : alpha numbers (?)
        Used to create the Pareto front if file doesn't already exist.

    Returns
    -------
    list
        a list of wiring costs and conduction delays
    """
    outdir = PARETO_FRONTS_DIR
    fname = '%s/%s.csv' % (outdir, G.graph['arbor name'])
    if os.path.exists(fname):
        df = pd.read_csv(fname, skipinitialspace=True)
        return list(df['wiring cost']), list(df['conduction delay'])
    else:
        wiring_costs, conduction_delays = pf.pareto_front(G, alphas)
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
            if not arbor_fname.endswith('.csv'):
                continue
            if arbor_fname.strip('.csv') in prev_arbors:
                continue

            print("analyzing arbors from analyze_arbors.py")
            print(arbor_fname)

            G = read_arbor_full(arbor_fname)
            arbor_name = G.graph['arbor name']

            wiring_costs, conduction_delays = get_pareto_front(G, alphas)

            dist, alpha = pf.arbor_dist_loc(G, alphas, wiring_costs, conduction_delays)
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
            f.write('arbor name, pareto front scaling distance, pareto front scaling location\n')

        for arbor_fname in os.listdir(RECONSTRUCTIONS_DIR):
            if not arbor_fname.endswith('.csv'):
                continue

            if arbor_fname.strip('.csv') in prev_arbors:
                continue

            print("writing scaling distances from analyze_arbors.py")
            print(arbor_fname)

            G = read_arbor_full(arbor_fname)
            arbor_name = G.graph['arbor name']

            wiring_costs, conduction_delays = get_pareto_front(G, alphas)

            dist, alpha = pf.arbor_dist_loc_scale(G, alphas, wiring_costs, conduction_delays)
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

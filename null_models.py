import numpy as np
import pareto_functions as pf
from collections import defaultdict
import optimal_midpoint as om
from utils import toy_network, toy_network2, draw_arbor
from constants import *
from read_arbor_reconstruction import read_arbor_full
import pandas as pd
import os
import random

def get_main_root_length(G, main_root_segments):
    total_length = 0
    for u, v in main_root_segments:
        total_length += G[u][v]['length']

    return total_length

def get_random_midpoints(G, main_root_segments, lateral_root_tips, main_root_length):
    ntips = len(lateral_root_tips)
    offsets = sorted(zip(np.random.uniform(0, main_root_length, ntips), lateral_root_tips))

    midpoints = defaultdict(list)
    total_length = 0
    for u, v in main_root_segments:
        length = G[u][v]['length']
        slope = om.slope_vector(u, v)
        total_length += length
        while len(offsets) > 0 and offsets[0][0] <= total_length:
            offset, lateral_root = offsets.pop(0)

            relative_offset = offset - (total_length - length)
            assert relative_offset <= length
            delta = relative_offset / length

            midpoint = om.midpoint(u, slope, delta)

            midpoints[(u, v)].append((delta, midpoint, lateral_root))

    return midpoints

def random_arbor(G):
    R = pf.starting_graph(G)
    R.graph['arbor name'] = '%s-random-arbor' % G.graph['arbor name']

    lateral_root_tips = pf.get_lateral_root_tips(R)

    main_root_segments = pf.get_main_root_segments(R)

    main_root_length = get_main_root_length(R, main_root_segments)

    random_midpoints = get_random_midpoints(R, main_root_segments, lateral_root_tips, main_root_length)

    pf.connect_to_midpoints(R, random_midpoints)

    return R

def get_null_function(method='random'):
    if method == 'random':
        return random_arbor
    else:
        # placeholder for future null models
        pass

def null_comparison(G, methods=None, ntrials=20):
    if methods == None:
        methods = ['random']
    tree_costs_file = '%s/%s.csv' % (NULL_MODELS_DIR, G.graph['arbor name'])
    first_time = not os.path.exists(tree_costs_file)

    with open(tree_costs_file, 'a') as f:
        if first_time:
            # if we've never examined this arbor before, write the header line
            f.write('model, wiring cost, conduction delay\n')

            # since it's the first time, measure the costs of the arbor itself
            wiring, delay = pf.pareto_costs(G)
            f.write('%s, %f, %f\n' % ('arbor', wiring, delay))

        for method in methods:
            null_model_func = get_null_function(method=method)
            for i in range(ntrials):
                N = null_model_func(G)
                wiring, delay = pf.pareto_costs(N)
                f.write('%s, %f, %f\n' % (method, wiring, delay))

def analyze_null_models():
    for reconstruction in os.listdir(RECONSTRUCTIONS_DIR):
        print(reconstruction)
        G = read_arbor_full(reconstruction)
        null_comparison(G)

def write_null_models_file():
    models_fname = '%s/models.csv' % STATISTICS_DIR
    with open(models_fname, 'w') as models_file:
        models_file.write('arbor name, model, pareto front distance, ' +\
                               'pareto front scaling distance\n')

        for arbor_file in os.listdir(NULL_MODELS_DIR):
            arbor_name = arbor_file.strip('.csv')
            print(arbor_name)

            tree_costs_file = '%s/%s' % (NULL_MODELS_DIR, arbor_file)
            pareto_front_file = '%s/%s' % (PARETO_FRONTS_DIR, arbor_file)

            tree_costs = pd.read_csv(tree_costs_file, skipinitialspace=True)
            pareto_front = pd.read_csv(pareto_front_file, skipinitialspace=True)
            opt_wiring = pareto_front['wiring cost']
            opt_delay = pareto_front['conduction delay']

            for model, model_wiring, model_delay in zip(tree_costs['model'],\
                                                        tree_costs['wiring cost'],\
                                                        tree_costs['conduction delay']):
                null_dist = pf.pareto_dist(model_wiring, model_delay, opt_wiring, opt_delay)
                null_dist_scale = pf.pareto_dist_scale(model_wiring, model_delay, opt_wiring, opt_delay)

                models_file.write('%s, %s, %f, %f\n' % (arbor_name, model,\
                                                        null_dist, null_dist_scale))


def main():
    #analyze_null_models()
    write_null_models_file()

if __name__ == '__main__':
    main()


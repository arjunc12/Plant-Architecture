import numpy as np
from pareto_functions import starting_graph, get_lateral_root_tips,\
                             get_main_root_segments, connect_to_midpoints
from collections import defaultdict
import optimal_midpoint as om
from utils import toy_network, draw_arbor
from constants import DRAWINGS_DIR


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
            offset, lateral_root = offsets.pop()

            offset_along_edge = offset - (total_length - length)
            delta = offset_along_edge / length

            midpoint = om.midpoint(u, slope, delta)

            midpoints[(u, v)].append((delta, midpoint, lateral_root))

    return midpoints

def random_arbor(G):
    R = starting_graph(G)
    R.graph['arbor name'] = '%s-random-arbor' % G.graph['arbor name']

    lateral_root_tips = get_lateral_root_tips(R)

    main_root_segments = get_main_root_segments(R)

    main_root_length = get_main_root_length(R, main_root_segments)

    random_midpoints = get_random_midpoints(R, main_root_segments, lateral_root_tips, main_root_length)

    connect_to_midpoints(R, random_midpoints)

    return R

def main():
    T = toy_network()
    R = random_arbor(T)
    draw_arbor(R, DRAWINGS_DIR)

if __name__ == '__main__':
    main()


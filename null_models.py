import numpy as np
from pareto_functions import starting_graph, get_lateral_root_tips,\
                             get_main_root_segments, connect_to_midpoints

def main_root_sequence(G):
    nodelist = []
    for u in G.nodes():
        if 'main root' in G.nodes[u]['label']:
            nodelist.append(u)

    main_root_subgraph = G.subgraph(nodelist)
    sequence = []
    visited = set()
    queue = [G.graph['main root base']]
    while len(queue) > 0:
        curr = queue.pop(0)
        visited.add(curr)
        sequence.append(curr)

        for neighbor in G.nneighbors(curr):
            if curr not in visited:
                queue.append(curr)

    return sequence

def lateral_root_tips(G):
    tips = []
    for u in G.nodes:
        if G.nodes[u]['label'] == 'lateral root tip':
            tips.append(u)

    return tips

def main_root_length(sequence):
    total_length = 0
    for i in xrange(len(sequence) - 1):
        u, v = sequence[i], sequence[i + 1]
        total_length += G[u][v]['length']

    return total_length

def random_connection_point(G):
    root_sequence = main_root_squence(G)
    length = main_root_length(root_sequence)

    tips = lateral_root_tips(G)

    tip_distances = {}
    for tip in tips:
        tip_distances[tip] = np.random.uniform(0, length)

def random_arbor(G):

    P = starting_graph(G)
    P.graph['arbor name'] = '%s random arbor' % G.graph['arbor name']

    lateral_root_tips = get_lateral_root_tips(P)

    main_root_segments = get_main_root_segments(G)

    # sort root segments based on the y-coordinate in the first point of the segment
    main_root_segments = sorted(main_root_segments, key = lambda s: s[0][1])

    connect_to_midpoints(P, best_midpoints)

    return P



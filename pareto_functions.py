from math import sqrt
from utils import *
import networkx as nx
from scipy.spatial.distance import euclidean
import numpy as np
from read_arbor_reconstruction import read_arbor_full
from constants import *
from optimal_midpoint import optimal_midpoint, optimal_midpoint_approx, optimal_midpoint_alpha1
from collections import defaultdict
import seaborn as sns
import os
import pandas as pd

def wiring_cost(G):
    # wiring cost is simply the sum of all edge lengths
    wiring = 0
    for u, v in G.edges():
        wiring += G[u][v]['length']
    return wiring

def conduction_delay(G):
    '''
    use a breadth-first search to compute the distance to from the root to each point

    when we encounter a visit node for the first time, we record its distance to the root
    (which is the sum of its parent's distance, plus the length of the edge from the parent
    to the current node').  We keep a running total of the total distances from the root
    to each node.
    '''
    droot = {}
    queue = []
    curr = None
    visited = set()

    root = G.graph['main root']

    queue.append(root)
    droot[root] = 0

    delay = 0
    while len(queue) > 0:
        curr = queue.pop(0)
        # we should never visit a node twice
        assert curr not in visited
        visited.add(curr)
        # we only measure delay for the lateral root tips
        if G.nodes[curr]['label'] == 'lateral root tip':
            delay += droot[curr]
        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + G[curr][u]['length']

    # make sure we visited every node
    assert len(visited) == G.number_of_nodes()

    return delay

def pareto_costs(G):
    '''
    perform a breadth-first search that simultaneously computers wiring cost and conduction delay
    '''
    droot = {}
    queue = []
    curr = None
    visited = set()

    root = G.graph['main root base']
    queue.append(root)
    droot[root] = 0

    wiring = 0
    delay = 0
    while len(queue) > 0:
        curr = queue.pop(0)
        # we should never visit a node twice
        assert curr not in visited
        visited.add(curr)
        # we only measure delay for the lateral root tips
        if G.nodes[curr]['label'] == 'lateral root tip':
            delay += droot[curr]

        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                length = G[curr][u]['length']
                wiring += length
                droot[u] = droot[curr] + length

    # check that we visited every node
    assert len(visited) == G.number_of_nodes()

    return wiring, delay

def prune_lateral_roots(G):
    for u in list(G.nodes()):
        label = G.nodes[u]['label']
        if label == 'lateral root tip':
            for n in list(G.neighbors(u)):
                G.remove_edge(u, n)
        elif not is_on_main_root(G, u):
            G.remove_node(u)

def starting_graph(G):
    P = G.copy()
    prune_lateral_roots(P)
    return P

def satellite_tree(G):
    S = G.copy()
    prune_lateral_roots(S)

    root = G.graph['main root base']
    for u in G.nodes():
        label = G.nodes[u]['label']
        if label == 'lateral root tip':
            connect_points(S, u, root)

    return S

def get_root_distances(G):
    distances = {}
    root = G.graph['main root base']
    prev = root
    queue = [root]

    while len(queue) > 0:
        curr = queue.pop()

        prev_distance = 0
        if prev in distances:
            prev_distance = distances[prev]
        distances[curr] = euclidean(curr, prev) + prev_distance

        for n in G.neighbors(curr):
            if G.nodes[n]['label'] == 'main root' and n != prev:
                queue.append(n)

        prev = curr

    return distances

def get_lateral_root_tips(G):
    tips = []
    for u in G.nodes():
        if G.nodes[u]['label'] == 'lateral root tip':
            tips.append(u)
    return tips

def get_main_root_segments(G):
    segments = []
    visited = set()
    queue = [G.graph['main root base']]
    while len(queue) > 0:
        curr = queue.pop()
        assert 'main root' in G.nodes[curr]['label']
        visited.add(curr)
        for neighbor in G.neighbors(curr):
            if neighbor not in visited and 'main root' in G.nodes[neighbor]['label']:
                segments.append((curr, neighbor))
                queue.append(neighbor)
    return segments


def get_best_midpoints(G, lateral_root_tips, main_root_segments, root_distances, alpha):
    best_midpoints = defaultdict(list)

    for lateral_root in lateral_root_tips:
        best_cost = float("inf")
        best_midpoint = None
        best_p0 = None
        best_p1 = None
        best_delta = None
        for p0, p1 in main_root_segments:
            droot = root_distances[p0]
            cost, midpoint, delta = None, None, None
            if alpha == 1:
                cost, midpoint, delta = optimal_midpoint_alpha1(p0, p1, lateral_root)
            else:
                cost, midpoint, delta = optimal_midpoint(p0, p1, lateral_root, alpha, droot)
            if cost < best_cost:
                best_cost = cost
                best_midpoint = midpoint
                best_p0 = p0
                best_p1 = p1
                best_delta = delta

        if best_delta == 1:
            assert best_midpoint == best_p1
            connect_points(G, lateral_root, best_p1)
        else:
            best_midpoints[(best_p0, best_p1)].append((best_delta, best_midpoint, lateral_root))

    return best_midpoints

def connect_to_midpoints(G, best_midpoints):
    for (p0, p1), midpoints in best_midpoints.items():
        assert G.has_edge(p0, p1)
        G.remove_edge(p0, p1)
        prev_point = p0
        for best_delta, best_midpoint, lateral_root in sorted(midpoints):
            if best_midpoint != prev_point and not G.has_node(best_midpoint):
                G.add_node(best_midpoint)
                G.nodes[best_midpoint]['label'] = 'main root'
                connect_points(G, prev_point, best_midpoint)
            connect_points(G, best_midpoint, lateral_root)
            prev_point = best_midpoint

        if prev_point != p1:
            connect_points(G, prev_point, p1)

def opt_arbor(G, alpha):
    if alpha == 0:
        return satellite_tree(G)

    root_x, root_y = G.graph['main root base']
    root_distances = get_root_distances(G)

    P = starting_graph(G)
    P.graph['arbor name'] = '%s-alpha=%0.2f' % (G.graph['arbor name'], alpha)

    lateral_root_tips = get_lateral_root_tips(P)

    main_root_segments = get_main_root_segments(P)

    best_midpoints = get_best_midpoints(P, lateral_root_tips, main_root_segments, root_distances, alpha)

    connect_to_midpoints(P, best_midpoints)

    return P

def pareto_front(G, alphas=DEFAULT_ALPHAS):
    wiring_costs = []
    conduction_delays = []

    for alpha in alphas:
        opt = opt_arbor(G, alpha)
        wiring, delay = pareto_costs(opt)
        wiring_costs.append(wiring)
        conduction_delays.append(delay)

    return wiring_costs, conduction_delays

def pareto_dist(wiring, delay, opt_wiring_costs, opt_conduction_delays):
    closest_dist = float("inf")

    for opt_wiring, opt_delay in zip(opt_wiring_costs, opt_conduction_delays):
        pareto_dist = euclidean((wiring, delay), (opt_wiring, opt_delay))
        if pareto_dist < closest_dist:
            closest_dist = pareto_dist

    return closest_dist

def arbor_dist_loc(G, alphas, wiring_costs, conduction_delays):
    arbor_wiring, arbor_delay = pareto_costs(G)

    closest_dist = float("inf")
    closest_alpha = None

    for alpha, wiring, delay in zip(alphas, wiring_costs, conduction_delays):
        pareto_dist = euclidean((arbor_wiring, arbor_delay), (wiring, delay))
        if pareto_dist < closest_dist:
            closest_dist = pareto_dist
            closest_alpha = alpha

    return closest_dist, closest_alpha

def point_dist_scale(p1, p2):
    assert len(p1) == len(p2)

    max_ratio = float("-inf")
    for i in range(len(p1)):
        coord1 = p1[i]
        coord2 = p2[i]
        ratio = coord2 / coord1
        max_ratio = max(ratio, max_ratio)

    return max_ratio

def pareto_dist_scale(wiring, delay, opt_wiring_costs, opt_conduction_delays):
    closest_dist = float("inf")

    for opt_wiring, opt_delay in zip(opt_wiring_costs, opt_conduction_delays):
        pareto_dist = point_dist_scale((opt_wiring, opt_delay), (wiring, delay))
        if pareto_dist < closest_dist:
            closest_dist = pareto_dist

    return closest_dist

def arbor_dist_loc_scale(G, alphas, wiring_costs, conduction_delays):
    arbor_wiring, arbor_delay = pareto_costs(G)

    closest_dist = float("inf")
    closest_alpha = None

    for alpha, wiring, delay in zip(alphas, wiring_costs, conduction_delays):
        pareto_dist = point_dist_scale((wiring, delay), (arbor_wiring, arbor_delay))
        if pareto_dist < closest_dist:
            closest_dist = pareto_dist
            closest_alpha = alpha

    return closest_dist, closest_alpha

def viz_trees(G, alphas=DEFAULT_ALPHAS, outdir=FRONT_DRAWINGS_DIR):
    for alpha in alphas:
        opt = opt_arbor(G, alpha)
        draw_arbor(opt, outdir='%s/%s' % (outdir, G.graph['arbor name']))

def viz_front(G, alphas=DEFAULT_ALPHAS, outdir=FRONT_DRAWINGS_DIR):
    '''
    wiring_costs, conduction_delays = pareto_front(G, alphas=alphas)

    arbor_wiring, arbor_delay = pareto_costs(G)
    sns.set()
    pylab.figure()
    pylab.plot(wiring_costs, conduction_delays, color='b')
    pylab.scatter(wiring_costs, conduction_delays, color='b')
    pylab.scatter(arbor_wiring, arbor_delay, marker='x', color='r')
    pylab.xlabel('wiring cost')
    pylab.ylabel('conduction delay')
    pylab.tight_layout()
    plot_dir = '%s/%s' % (outdir, G.graph['arbor name'])
    os.system('mkdir -p %s' % plot_dir)
    pylab.savefig('%s/%s-pareto-front.pdf' % (plot_dir, G.graph['arbor name']))
    pylab.close()
    '''
    arbor_name = G.graph['arbor name']
    pareto_front = pd.read_csv('%s/%s.csv' % (PARETO_FRONTS_DIR, arbor_name), skipinitialspace=True)
    pareto_front.drop('alpha', axis=1, inplace=True)
    pareto_front['model'] = 'Pareto front'

    tree_costs = pd.read_csv('%s/%s.csv' % (NULL_MODELS_DIR, arbor_name), skipinitialspace=True)

    scatter_df = tree_costs._append(pareto_front)

    pylab.figure()
    sns.scatterplot(x='wiring cost', y='conduction delay', hue='model', data=scatter_df)
    plot_dir = '%s/%s' % (outdir, arbor_name)
    os.system('mkdir -p %s' % plot_dir)
    pylab.savefig('%s/%s-pareto-front.pdf' % (plot_dir, arbor_name))


def main():
    # G = read_arbor_full('091_4_S_day5.csv')
    # 189_3_C_day3
    # 194_1_C_day3
    # G = read_arbor_full('189_3_C_day3.csv') #- produces an image
    # G = read_arbor_full('194_1_C_day3.csv') #- produces an image
    for arbor in os.listdir(RECONSTRUCTIONS_DIR):
        print(arbor)
        G = read_arbor_full(arbor)

        viz_front(G)


if __name__ == '__main__':
    main()



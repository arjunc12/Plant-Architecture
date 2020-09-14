from math import sqrt
from utils import connect_insertions, draw_arbor, toy_network, connect_points
import networkx as nx
from scipy.spatial.distance import euclidean
import numpy as np
from readArborReconstruction import readArbor
from constants import DEFAULT_ALPHAS
from optimal_midpoint import optimal_midpoint_approx

def wiring_cost(G):
    wiring = 0
    for u, v in G.edges():
        if 'lateral root' in [G.node[u]['label'], G.node[v]['label']]:
            wiring += G[u][v]['length']
    return wiring

def conduction_delay(G):
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
        assert curr not in visited
        visited.add(curr)
        if G.node[curr]['label'] == 'lateral root':
            delay += droot[curr]
        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + G[curr][u]['length']

    assert len(visited) == G.number_of_nodes()

    return delay

def pareto_costs(G):
    droot = {}
    queue = []
    curr = None
    visited = set()

    root = G.graph['main root']
    queue.append(root)
    droot[root] = 0

    wiring = 0
    delay = 0
    while len(queue) > 0:
        curr = queue.pop(0)
        assert curr not in visited
        visited.add(curr)
        if G.node[curr]['label'] == 'lateral root':
            delay += droot[curr]

        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                length = G[curr][u]['length']
                if 'lateral root' in [G.node[curr]['label'], G.node[u]['label']]:
                    wiring += length
                droot[u] = droot[curr] + length

    assert len(visited) == G.number_of_nodes()

    return wiring, delay

def satellite_tree(G):
    S = nx.Graph()
    root = G.graph['main root']
    S.add_node(root)
    S.graph['main root'] = root
    S.node[root]['label'] = 'main root'


    for u in G.nodes():
        if G.node[u]['label'] == 'lateral root':
            S.add_node(u)
            S.node[u]['label'] = 'lateral root'
            connect_points(S, u, root)

    return S

def opt_epsilon(x, y, alpha, max_epsilon=None):
    assert alpha > 0
    numerator = x * (1 - alpha)
    denominator = sqrt(1 - ((1 - alpha) ** 2))
    epsilon = numerator / denominator
    epsilon = min(epsilon, max_epsilon)
    return epsilon

def opt_arbor(G, alpha):
    if alpha == 0:
        return satellite_tree(G)

    root_x, root_y = G.graph['main root']

    P = nx.Graph()
    lateral_roots = []
    for u in G.nodes():
        if G.node[u]['label'] == 'main root':
            P.add_node(u)
            P.node[u]['label'] = 'main root'
            P.graph['main root'] = u
        elif G.node[u]['label'] == 'lateral root':
            lateral_roots.append(u)

    for root in lateral_roots:
        x, y = root
        max_epsilon = y - root_y
        epsilon = opt_epsilon(x, y, alpha, max_epsilon=max_epsilon)
        insertion = y - epsilon
        print(G.graph['arbor name'], y, epsilon, insertion, root_y)
        insertion = max(insertion, root_y)
        insertion = min(insertion, y)

        print(insertion, root_y)
        assert insertion >= root_y
        assert insertion <= y

        insertion = (0, insertion)
        P.add_node(root)
        P.node[root]['label'] = 'lateral root'
        P.add_node(insertion)
        P.node[insertion]['label'] = 'insertion point'

        P.add_edge(root, insertion)
        P[root][insertion]['length'] = euclidean(root, insertion)

    connect_insertions(P)
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

def pareto_dist(G, alphas, wiring_costs, conduction_delays):
    arbor_wiring, arbor_delay = pareto_costs(G)

    closest_dist = float("inf")
    closest_alpha = None

    for alpha, wiring, delay in zip(alphas, wiring_costs, conduction_delays):
        pareto_dist = euclidean((arbor_wiring, arbor_delay), (wiring, delay))
        if pareto_dist < closest_dist:
            closest_dist = pareto_dist
            closest_alpha = alpha

    return closest_dist, alpha

def main():
    G = toy_network()

    wiring_costs, conduction_delays = pareto_front(G)
    for wiring, delay in zip(wiring_costs, conduction_delays):
        print(wiring, delay)

if __name__ == '__main__':
    main()



import networkx as nx
from scipy.spatial.distance import euclidean
from utils import connect_insertions, toy_network, draw_arbor
from constants import RECONSTRUCTIONS_DIR, DRAWINGS_DIR
import os
import pandas as pd

def connect_lateral_roots(G, root_points, lateral_starts):
    root_points = sorted(root_points, key = lambda p: p[1])
    for lateral_start in lateral_starts:
        assert G.has_node(lateral_start)
        closest_dist = float("inf")
        closest_point = None
        y_lateral = lateral_start[1]

        for root_point in root_points:
            y_root = root_point[1]
            if y_root > y_lateral:
                assert closest_point != None
                break
            else:
                dist = euclidean(lateral_start, root_point)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_point = root_point

        assert closest_point != None
        assert G.has_node(closest_point)
        assert G.node[closest_point]['label'] == 'main root'
        assert not G.has_edge(closest_point, lateral_start)

        G.add_edge(closest_point, lateral_start)
        G[closest_point][lateral_start]['length'] = closest_dist

def read_arbor_full(fname):
    G = nx.Graph()
    G.graph['arbor name'] = fname.strip('.csv')
    prev_point = None
    curr_root = None
    root_points = []
    lateral_starts = []

    with open('%s/%s' % (RECONSTRUCTIONS_DIR, fname)) as f:
        for line in f:
            line = line.strip('\n')
            line = line.split(',')
            if len(line) == 1:
                curr_root = line[0]
                prev_point = None
            else:
                point = tuple(map(float, line))
                if prev_point == None:
                    G.add_node(point)
                    lateral_starts.append(point)
                    if curr_root == 'lateral root':
                        lateral_starts.append(point)
                else:
                    G.add_edge(prev_point, point)
                    G[prev_point][point]['length'] = euclidean(prev_point, point)
                    print(curr_root, prev_point, point)

                if curr_root == 'main root':
                    G.node[point]['label'] = 'main root'
                    root_points.append(point)
                else:
                    G.node[point]['label'] = 'lateral root'

                prev_point = point

    connect_lateral_roots(G, root_points, lateral_starts)

    for u in G.nodes():
        if G.node[u]['label'] == 'lateral root' and G.degree(u) == 1:
            G.node[u]['label'] = 'lateral root tip'

    return G

def read_arbor_condensed(fname):
    df = pd.read_csv('%s/%s' % (RECONSTRUCTIONS_DIR, fname), skipinitialspace=True)
    root_order = df['root order']
    x_coord = df['x coordinate']
    y_coord = df['y coordinate']
    insertion_point = df['insertion point']

    G = nx.Graph()
    G.graph['arbor name'] = fname.strip('.csv')

    for order, x, y, insertion in zip(root_order, x_coord, y_coord, insertion_point):
        p1 = (x, y)
        p2 = (0, insertion)
        if order == 0:
            G.add_node(p1)
            G.node[p1]['label'] = 'main root'
            G.graph['main root'] = p1

        elif order == 1:
            G.add_edge(p1, p2)
            G.node[p1]['label'] = 'lateral root'
            G.node[p2]['label'] = 'insertion point'

            G[p1][p2]['length'] = euclidean(p1, p2)


    connect_insertions(G)

    return G

def main():
    G =read_arbor_full('272_3_S_day3.csv')
    #G =read_arbor_full('165_3_S_day3.csv')
    draw_arbor(G, DRAWINGS_DIR)

if __name__ == '__main__':
    main()

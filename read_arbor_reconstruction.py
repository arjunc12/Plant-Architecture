import networkx as nx
from scipy.spatial.distance import euclidean
from utils import *
from constants import RECONSTRUCTIONS_DIR, DRAWINGS_DIR
import os
import pandas as pd

def check_root_points(root_points):
    '''
    Checks that the root points are sorted in ascending order by y-coordinate
    '''
    for i in range(1, len(root_points)):
        y0 = root_points[i - 1][1]
        y1 = root_points[i][1]
        assert y1 >= y0

def connect_lateral_roots(G, root_points, lateral_starts):
    '''
    Method for connecting the start of each lateral root to the closest main root point.


    G - the network consisting of disconnected main and lateral roots

    root_points - the (x, y) coordinates for the points on the main root tracing

    lateral_starts - the (x, y) coordinates for the points at the start of every lateral root
    '''

    # loop through each lateral root starting point to find the closest root point
    for lateral_start in lateral_starts:
        assert G.has_node(lateral_start)

        closest_dist = float("inf")
        closest_point = None
        y_lateral = lateral_start[1]

        # variable to track whether lateral_start is already connected to the main root
        is_connected = False

        '''
        loop through the main root points to find the main root point closest to the current
        lateral root
        '''
        for root_point in root_points:
            '''
            If lateral_start already has a path to root_point then it doesn't need to be
            connected to the main root
            '''
            if nx.has_path(G, root_point, lateral_start):
                is_connected = True
                break
            '''
            Otherwise Check if root_point is closer to lateral_start than the the previously
            considered  root points
            '''
            dist = euclidean(lateral_start, root_point)
            if dist < closest_dist:
                closest_dist = dist
                closest_point = root_point

        if is_connected:
            # lateral_start already connected to main root; we don't want to add more edges
            continue

        # we should have found a closest root point, if not something's wrong
        assert closest_point != None
        assert G.has_node(closest_point)
        assert G.nodes[closest_point]['label'] in ['main root', 'main root base']
        assert not G.has_edge(closest_point, lateral_start)

        # connect lateral_start to the closest root point
        G.add_edge(closest_point, lateral_start)
        G[closest_point][lateral_start]['length'] = closest_dist

def read_arbor_full(fname):
    '''
    Read the arbor reconstruction corresponding to a full arbor tracing. First, this
    method individually reconstructs the main root and lateral roots separately. Afterwards,
    each lateral root is connected to the closest main root point
    '''
    G = nx.Graph()
    G.graph['arbor name'] = fname.strip('.csv')

    # keep track of where the previous point was, and which root it is part of
    prev_point = None
    curr_root = None

    # keep track of all points along the main root, and all points where a lateral root started growing
    root_points = []
    lateral_starts = []

    with open('%s/%s' % (RECONSTRUCTIONS_DIR, fname)) as f:
        for line in f:
            line = line.strip('\n')
            line = line.split(',')
            if len(line) == 1:
                # we've found a new main or lateral root
                # reset the root that we are traversing
                curr_root = line[0]
                prev_point = None
            else:
                point = tuple(map(float, line))
                if prev_point == None:
                    # this is the first point on the current root
                    if not G.has_node(point):
                        G.add_node(point)
                        if curr_root != 'main root':
                            lateral_starts.append(point)
                else:
                    if prev_point == point:
                        # don't add a self loop that was probably an error in the data
                        continue
                    # connect this point to the previous point on the same root
                    G.add_edge(prev_point, point)
                    G[prev_point][point]['length'] = euclidean(prev_point, point)

                # label the newly added node
                if curr_root == 'main root':
                    G.nodes[point]['label'] = 'main root'
                    root_points.append(point)
                else:
                    G.nodes[point]['label'] = 'lateral root'

                prev_point = point

    # label the base of the main root
    main_root_base = root_points[0]
    G.nodes[main_root_base]['label'] = 'main root base'
    G.graph['main root base'] = main_root_base

    # connect the first point in each lateral root to the closest point along the main root
    connect_lateral_roots(G, root_points, lateral_starts)

    # re-label the base of the main root and tips of the lateral roots
    relabel_lateral_root_tips(G)

    assert nx.is_tree(G)

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
        # check if order is 0 (main root) or 1 (lateral root)
        if order == 0:
            G.add_node(p1)
            G.nodes[p1]['label'] = 'main root base'
            G.graph['main root base'] = p1

        elif order == 1:
            G.add_edge(p1, p2)
            G.nodes[p1]['label'] = 'lateral root tip'
            G.nodes[p2]['label'] = 'main root'

            G[p1][p2]['length'] = euclidean(p1, p2)

    connect_main_root(G)

    return G

def main():
    G = read_arbor_full('292_1_C_day5.csv')
    draw_arbor(G, outdir=DRAWINGS_DIR)

if __name__ == '__main__':
    main()

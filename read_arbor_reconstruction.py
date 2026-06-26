import networkx as nx
from scipy.spatial.distance import euclidean
from utils import *
from constants import RECONSTRUCTIONS_DIR, DRAWINGS_DIR
import os
import pandas as pd
from sys import argv
import optimal_midpoint
from collections import defaultdict

def check_root_points(root_points):
    '''
    Checks that the root points are sorted in ascending order by y-coordinate
    '''
    for i in range(1, len(root_points)):
        y0 = root_points[i - 1][1]
        y1 = root_points[i][1]
        assert y1 >= y0


def connect_lateral_roots_new(G, root_points, lateral_starts):
    '''
    new version of connect lateral roots, this will need to track the start and 
    end points of each of the lateral root segments in some way (potentially by creating objects)
    '''

    segments = [(root_points[i], root_points[i+1]) for i in range(len(root_points) - 1)]

    connections = []


    # need to continue checking vvv

    lateral_starts_set = set(lateral_starts)

    print("vvvv Currently in connect_lateral_roots, checking if G is connected... vvv") # TODO: REMOVE PRINT STATEMENT

    for lateral_start in lateral_starts:
        assert G.has_node(lateral_start)

        '''
        if a lateral root has multiple neighbors AND can reach another start, then
        it's not actually a start.
        Some starts might be the start of multiple lateral roots. Those roots will have
        degree > 1 but will not have paths to any other starts
        '''
        
        if G.degree(lateral_start) > 1 and any(
            nx.has_path(G, lateral_start, other_start)
            for other_start in lateral_starts_set
            if other_start != lateral_start
        ):
            continue

        is_connected = any(
            nx.has_path(G, root_point, lateral_start)
            for root_point in root_points
        )
        if is_connected:
            continue
        
        '''
        if nx.has_path(G, lateral_start, root_points[0]):
            continue
        '''
            
        # find which main root segment is closest
        best_dist = float("inf")
        best_point = None
        best_seg = None
        best_t = None

        for p0, p1 in segments:
            dist, proj_point, t = optimal_midpoint.optimal_midpoint_alpha1(p0, p1, lateral_start)
            if dist < best_dist:
                best_dist = dist
                best_point = proj_point
                best_seg = (p0, p1)
                best_t = t

        connections.append((lateral_start, best_seg, best_t, best_point))
    
    # assert nx.is_connected(G), " --- [1/3] Graph is not fully connected after phase 1"
    # assert nx.is_tree(G), "--- [1/3] Graph has a cycle after phase 1"
    
    # Phase 2: group connection points by segment
    seg_connections = defaultdict(list)
    for lateral_start, best_seg, best_t, best_point in connections:
        seg_connections[best_seg].append((best_t, best_point, lateral_start))

    # assert nx.is_connected(G), " --- [2/3] Graph is not fully connected after phase 2"
    # assert nx.is_tree(G), "--- [2/3] Graph has a cycle after phase 2"

    # Phase 3: for each segment, sort by t, split into subsegments, connect laterals
    for seg, seg_conns in seg_connections.items():
        p0, p1 = seg
        assert G.has_edge(p0, p1), "No main root edge between %s and %s" % (p0, p1)
        seg_conns_sorted = sorted(seg_conns, key=lambda x: x[0])

        # Only remove the segment edge if there are interior split points
        has_interior = any(0 < t < 1 and proj != p0 and proj != p1
                          for t, proj, _ in seg_conns_sorted)
        if has_interior:
            G.remove_edge(p0, p1)

        # we will go along this segment for each interior point that needs to become its own node
        # track the last node that we connected a lateral root to
        prev_node = p0
        for t, proj_point, lateral_start in seg_conns_sorted:
            # connect to the first part of the segment, no new node needed
            if t == 0 or proj_point == p0:
                connect_point = p0
            # connect to the second endpoint of the segment, no new node needed
            elif t == 1 or proj_point == p1:
                connect_point = p1
            else:
                # creating a new node out of a midpoint
                connect_point = proj_point
                # make the new node into its own point
                if not G.has_node(connect_point):
                    G.add_node(connect_point)
                    G.nodes[connect_point]['label'] = 'main root'
                # connect the new node to the previous node along the line segment
                if not G.has_edge(prev_node, connect_point):
                    G.add_edge(prev_node, connect_point)
                    G[prev_node][connect_point]['length'] = euclidean(prev_node, connect_point)
                # the connection point from this iteration becomes the most recent point
                prev_node = connect_point

            G.add_edge(connect_point, lateral_start)
            G[connect_point][lateral_start]['length'] = euclidean(connect_point, lateral_start)

        # the most recently used connection point should be connected to the segment end to close the segment
        if has_interior and prev_node != p1:
            G.add_edge(prev_node, p1)
            G[prev_node][p1]['length'] = euclidean(prev_node, p1)

        # make sure the original segment still exists
        assert nx.has_path(G, p0, p1), "check #2: no path between main root segment %s and %s" % (p0, p1)

    assert nx.is_connected(G), " --- [3/3] Graph is not fully connected after phase 3"
    assert nx.is_tree(G), "--- [3/3] Graph has a cycle after phase 3"

    # make sure every lateral root start can reach the base
    for start in lateral_starts:
        assert nx.has_path(G, start, G.graph['main root base']), f"no path to root from {start} to base"
    
    assert nx.is_connected(G), " --- [END/3] Graph is not fully connected after connect_lateral_roots"
    assert nx.is_tree(G), "--- [END/3] Graph has a cycle after connect_lateral_roots"

    print("^^^ End of connect_lateral_roots ^^^") # TODO: REMOVE PRINT STATEMENT



def connect_lateral_roots(G, root_points, lateral_starts):
    '''
    Method for connecting the start of each lateral root to the closest point
    on the main root, including points along segments (not just traced nodes).

    For each lateral root start, we find the closest point on any main root segment.
    If the closest point lies strictly between two traced nodes, we split that segment
    by inserting a new node. If the closest point is a traced node, we connect directly.

    G - the network consisting of disconnected main and lateral roots
    root_points - the (x, y) coordinates for the points on the main root tracing
    lateral_starts - the (x, y) coordinates for the points at the start of every lateral root
    '''

    segments = [(root_points[i], root_points[i+1]) for i in range(len(root_points) - 1)]

    # Phase 1: find best connection point for each lateral start
    # Skip any lateral start that is contained within another lateral root
    connections = []
    lateral_starts_set = set(lateral_starts)

    print("vvvv Currently in connect_lateral_roots, checking if G is connected... vvv") # TODO: REMOVE PRINT STATEMENT

    for lateral_start in lateral_starts:
        assert G.has_node(lateral_start)

        '''
        if a lateral root has multiple neighbors AND can reach another start, then
        it's not actually a start.
        Some starts might be the start of multiple lateral roots. Those roots will have
        degree > 1 but will not have paths to any other starts
        '''
        
        if G.degree(lateral_start) > 1 and any(
            nx.has_path(G, lateral_start, other_start)
            for other_start in lateral_starts_set
            if other_start != lateral_start
        ):
            continue

        is_connected = any(
            nx.has_path(G, root_point, lateral_start)
            for root_point in root_points
        )
        if is_connected:
            continue
        
        '''
        if nx.has_path(G, lateral_start, root_points[0]):
            continue
        '''
            
        # find which main root segment is closest
        best_dist = float("inf")
        best_point = None
        best_seg = None
        best_t = None

        for p0, p1 in segments:
            dist, proj_point, t = optimal_midpoint.optimal_midpoint_alpha1(p0, p1, lateral_start)
            if dist < best_dist:
                best_dist = dist
                best_point = proj_point
                best_seg = (p0, p1)
                best_t = t

        connections.append((lateral_start, best_seg, best_t, best_point))
    
    # assert nx.is_connected(G), " --- [1/3] Graph is not fully connected after phase 1"
    # assert nx.is_tree(G), "--- [1/3] Graph has a cycle after phase 1"
    
    # Phase 2: group connection points by segment
    seg_connections = defaultdict(list)
    for lateral_start, best_seg, best_t, best_point in connections:
        seg_connections[best_seg].append((best_t, best_point, lateral_start))

    # assert nx.is_connected(G), " --- [2/3] Graph is not fully connected after phase 2"
    # assert nx.is_tree(G), "--- [2/3] Graph has a cycle after phase 2"

    # Phase 3: for each segment, sort by t, split into subsegments, connect laterals
    for seg, seg_conns in seg_connections.items():
        p0, p1 = seg
        assert G.has_edge(p0, p1), "No main root edge between %s and %s" % (p0, p1)
        seg_conns_sorted = sorted(seg_conns, key=lambda x: x[0])

        # Only remove the segment edge if there are interior split points
        has_interior = any(0 < t < 1 and proj != p0 and proj != p1
                          for t, proj, _ in seg_conns_sorted)
        if has_interior:
            G.remove_edge(p0, p1)

        # we will go along this segment for each interior point that needs to become its own node
        # track the last node that we connected a lateral root to
        prev_node = p0
        for t, proj_point, lateral_start in seg_conns_sorted:
            # connect to the first part of the segment, no new node needed
            if t == 0 or proj_point == p0:
                connect_point = p0
            # connect to the second endpoint of the segment, no new node needed
            elif t == 1 or proj_point == p1:
                connect_point = p1
            else:
                # creating a new node out of a midpoint
                connect_point = proj_point
                # make the new node into its own point
                if not G.has_node(connect_point):
                    G.add_node(connect_point)
                    G.nodes[connect_point]['label'] = 'main root'
                # connect the new node to the previous node along the line segment
                if not G.has_edge(prev_node, connect_point):
                    G.add_edge(prev_node, connect_point)
                    G[prev_node][connect_point]['length'] = euclidean(prev_node, connect_point)
                # the connection point from this iteration becomes the most recent point
                prev_node = connect_point

            G.add_edge(connect_point, lateral_start)
            G[connect_point][lateral_start]['length'] = euclidean(connect_point, lateral_start)

        # the most recently used connection point should be connected to the segment end to close the segment
        if has_interior and prev_node != p1:
            G.add_edge(prev_node, p1)
            G[prev_node][p1]['length'] = euclidean(prev_node, p1)

        # make sure the original segment still exists
        assert nx.has_path(G, p0, p1), "check #2: no path between main root segment %s and %s" % (p0, p1)

    assert nx.is_connected(G), " --- [3/3] Graph is not fully connected after phase 3"
    assert nx.is_tree(G), "--- [3/3] Graph has a cycle after phase 3"

    # make sure every lateral root start can reach the base
    for start in lateral_starts:
        assert nx.has_path(G, start, G.graph['main root base']), f"no path to root from {start} to base"
    
    assert nx.is_connected(G), " --- [END/3] Graph is not fully connected after connect_lateral_roots"
    assert nx.is_tree(G), "--- [END/3] Graph has a cycle after connect_lateral_roots"

    print("^^^ End of connect_lateral_roots ^^^") # TODO: REMOVE PRINT STATEMENT

def has_reconstruction(fname):
    '''
    Function to check if a reconstruction exists and can be read

    fname -- the name of the file where the arbor reconstruction would be located if it exists
    '''
    return os.path.exists('%s/%s' % (RECONSTRUCTIONS_DIR, fname))


def read_arbor_full(fname):
    G = nx.Graph()
    G.graph['arbor name'] = fname.strip('.csv')

    # might change to include lat_beginning
    prev_point = None
    curr_root = None

    # also might change    
    root_points = []
    lateral_starts = []

    with open('%s/%s' % (RECONSTRUCTIONS_DIR, fname)) as f:
        id = 0 # assigning unique ID's to each node in case of duplicate nodes
        for line in f:
            line = line.strip('\n')
            line = line.split(',')

            if len(line) == 1: # reached either the main root base or the beginning of a lateral root
                curr_root = line[0]
                prev_point = None
            else: # reached a root coordinate point
                point = tuple(map(float, line))

                if prev_point == None: # if this is the first point on the current root
                    if not G.has_node(point): # if this point hasn't been included in the graph object yet
                        G.add_node(id, coords=point)
                        if curr_root != 'main root': # if the non-coord. CSV row didn't say 'main root', it means it's a lateral
                            lateral_starts.append(point) # note: might also be appending non-start nodes
                            print(f" --- Appended {point} to lateral_starts. Current status of lateral_starts: {lateral_starts} ---")
                else:
                    if prev_point == point: # continue if they're the same since it's most likely a duplicate (note: might be causing an issue)
                        continue
                    G.add_edge(prev_point, point)
                    G[prev_point][point]['length'] = euclidean(prev_point, point)
                
                if curr_root == 'main root':
                    G.nodes[point]['label'] = 'main root'
                    root_points.append(point)
                else:
                    G.nodes[point]['label'] = 'lateral root'
                
                prev_point = point
            id += 1

        
    # labeling main root base
    main_root_base = root_points[0]
    G.nodes[main_root_base]['label'] = 'main root base'
    G.graph['main root base'] = main_root_base

    # connect the first point in each lateral root to the closest point along the main root
    connect_lateral_roots(G, root_points, lateral_starts) # Note: most likely where the issue stems from, will need to add lat_root_start and lat_root_end labels 

    relabel_lateral_root_tips(G) # just relabeling base of main root and tips of lateral roots <<< note: might show how to access lateral root tips

    return G




def read_arbor_full_initial(fname):
    '''
    Read the arbor reconstruction corresponding to a full arbor tracing. First, this
    method individually reconstructs the main root and lateral roots separately. Afterwards,
    each lateral root is connected to the closest main root point
    '''

    print("vvvvvv Start of read_arbor_full vvvvvv") # TODO: REMOVE PRINT STATEMENT
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
                print(f" [read_arbor_full] () This is curr_root if len(line) == 1: {curr_root}")
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

    assert nx.is_connected(G), "Graph is not fully connected after connect_lateral_roots"
    assert nx.is_tree(G), "Graph has a cycle after connect_lateral_roots"

    # re-label the base of the main root and tips of the lateral roots
    relabel_lateral_root_tips(G)

    print("^^^^^^ End of read_arbor_full ^^^^^^") #TODO: REMOVE PRINT STATEMENT

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
    for arbor in os.listdir(RECONSTRUCTIONS_DIR):
        if len(argv) == 1 or arbor in argv[1]:
            print(arbor)
            G = read_arbor_full(arbor)

if __name__ == '__main__':
    main()

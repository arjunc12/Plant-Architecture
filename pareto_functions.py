from math import sqrt, log
from utils import *
import networkx as nx
from scipy.spatial.distance import euclidean
import numpy as np
from read_arbor_reconstruction import read_arbor_full
from constants import *
from optimal_midpoint import optimal_midpoint, optimal_midpoint_approx, optimal_midpoint_alpha1
from collections import defaultdict, namedtuple
import seaborn as sns
import os
import pandas as pd

CostSpec = namedtuple('CostSpec', ['wiring_transform', 'delay_transform'])

def _homogeneous_wiring(curve, to_root): return curve
def _homogeneous_delay(curve, to_root): return curve + to_root

def _heterogeneous_wiring(curve, to_root): return curve ** 2
def _heterogeneous_delay(curve, to_root): return log(1 + curve) + log(1 + to_root)

HOMOGENEOUS = CostSpec(
    wiring_transform = _homogeneous_wiring,
    delay_transform = _homogeneous_delay,
)

HETEROGENEOUS = CostSpec(
    wiring_transform = _heterogeneous_wiring, 
    delay_transform = _heterogeneous_delay,
)


COST_SPECS = {
    'homogeneous': HOMOGENEOUS,
    'heterogeneous': HETEROGENEOUS,
}

def resolve_cost_specs(cost_method):
    if cost_method == 'both':
        return [
            ('homogeneous', HOMOGENEOUS),
            ('heterogeneous', HETEROGENEOUS),
        ]
    return [(cost_method, COST_SPECS[cost_method])]

def wiring_cost(G, cost_spec=HOMOGENEOUS):
    # wiring cost is simply the sum of all edge lengths
    wiring = 0
    for u, v in G.edges():
        wiring += G[u][v]['length']
    return cost_spec.wiring_transform(wiring, 0) # 0 is a placeholder value that isn't used


# pretty much the same as version 2
def lateral_root_path_length(G, tip):
    """Sum edge lengths from tip of a lateral root back to main root insertion point."""
    # go down the lateral neighbors until you reach the 'main root' node right next to the node labeled 'lateral root start'

    length = 0
    visited = set()
    queue = [tip]

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)

        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                label = G.nodes[neighbor]['label']
                if label in ('lateral root', 'lateral root tip', 'lateral root start'):
                    length += G[node][neighbor]['length']
                    queue.append(neighbor)
                elif label in ('main root', 'main root base'):
                    length += G[node][neighbor]['length']
                    # no more nodes to append since this is the end of the lateral root
                    assert len(queue) == 0, "   << [lateral_root_path_length] Queue is not empty after traversing entire lateral root."
    return length

    

def conduction_delay(G, cost_spec=HOMOGENEOUS): 
    dist_root = {} # to store distances from each node to the main root
    queue = []
    visited = set()
    main_root = G.graph.get('main root base', G.graph.get('main root')) # aka an ID of 0 (first node in CSV always has this ID)
    queue.append(main_root)
    dist_root[main_root] = 0
    delay = 0

    while len(queue) > 0:
        curr = queue.pop(0)

        assert curr not in visited # making sure we haven't visited this node yet
        visited.add(curr)

        if G.nodes[curr]['label'] == 'lateral root tip':
            curve = lateral_root_path_length(G, curr)
            to_root = dist_root[curr] - curve
            
            # making sure to_root isn't negative
            assert to_root > 0, f"[Error] Negative to_root = {to_root:.6f} at tip {G.nodes[curr]['coords']}, \ndist_root = {dist_root[curr]:.6f}, curve = {curve:.6f}"
            delay += cost_spec.delay_transform(curve, to_root)
        
        for curr_neighbor in G.neighbors(curr):
            if curr_neighbor not in visited:
                queue.append(curr_neighbor)
                dist_root[curr_neighbor] = dist_root[curr] + G[curr][curr_neighbor]['length']
    
    assert len(visited) == G.number_of_nodes(), "!!! --- Not all nodes were visited --- !!!"
    return delay
            


# ----- Version 2 of conduction_delay (with lateral_root_path_length as a helper function)


def lateral_root_path_length_v2(G, tip):
    """Sum edge lengths from tip of a lateral root back to main root insertion point."""
    length = 0
    visited = set()
    queue = [tip]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                label = G.nodes[neighbor]['label']
                if label in ('lateral root', 'lateral root tip'):
                    length += G[node][neighbor]['length']
                    queue.append(neighbor)
                elif label in ('main root', 'main root base'):
                    length += G[node][neighbor]['length']
                    # stop here — this is the insertion point
    return length

def conduction_delay_v2(G, cost_spec=HOMOGENEOUS):
    droot = {}
    queue = []
    visited = set()
    root = G.graph.get('main root base', G.graph.get('main root'))
    queue.append(root)
    droot[root] = 0
    delay = 0

    while len(queue) > 0:
        curr = queue.pop(0)
        assert curr not in visited
        visited.add(curr)

        if G.nodes[curr]['label'] == 'lateral root tip':
            curve = lateral_root_path_length(G, curr)
            to_root = droot[curr] - curve   # subtract lateral length to get main root distance
            # troubleshooting
            if to_root < 0:
                print(f"Warning: negative to_root={to_root:.6f} at tip {curr}, "
                      f"droot = {droot[curr]:.6f}, curve = {curve:.6f}")
            to_root = max(0.0, to_root)
            delay += cost_spec.delay_transform(curve, to_root)

        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + G[curr][u]['length']

    assert len(visited) == G.number_of_nodes()
    return delay


# ----------------- Initial version of conduction_delay (prior to change for choice in cost computation methods) ------------- 

def conduction_delay_initial(G):
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

    root = G.graph.get('main root base', G.graph.get('main root')) # root = G.graph['main root']

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


# ------ Version 3 of conduction_delay calc system -----

def lateral_root_path_length_v3(G, tip, droot, main_root_nodes):
    """
    Walk from tip to its main root insertion point by always stepping to the
    lateral-root neighbor with the smallest effective_droot value, then return
    the total edge-length accumulated plus (for disconnected laterals) the
    euclidean distance from the walk's final node to the nearest main root node.
 
    effective_droot(node) is defined as:
        droot[node]                              if node was reached by the BFS
                                                 (i.e. it is connected to the main root)
        min euclidean distance to any main root  otherwise
                                                 (disconnected component fallback)
 
    This resolves both known failure cases:
 
      CASE 1 — BRANCHING LATERALS (shared branch point):
        The old BFS fanned out from the branch point into sibling branches,
        overcounting. The greedy effective_droot walk never turns toward a
        sibling: nodes on the true path back to the insertion point always
        have a smaller droot than nodes on sibling branches.
 
      CASE 2 — DISCONNECTED LATERALS (no connection to main root):
        These nodes have no droot entry. effective_droot falls back to
        euclidean distance to the nearest main root node, so the walk still
        moves in the correct direction (toward the main root). When the walk
        exhausts all lateral neighbors (reaching the end of the disconnected
        component closest to the main root), it adds the euclidean distance
        from that endpoint to the nearest main root node and returns.
 
    Parameters
    ----------
    G               : nx.Graph — the arbor graph
    tip             : node     — lateral root tip to start from
    droot           : dict     — {node: cumulative BFS distance from root}
    main_root_nodes : list     — all nodes whose label is 'main root' or
                                 'main root base', pre-computed by conduction_delay
 
    Returns
    -------
    float — total path length from tip to its insertion point (or to the
            nearest main root node, for disconnected tips)
    """
    def effective_droot(node):
        """
        BFS-based distance if available, otherwise euclidean to nearest main root.
        This lets the greedy walk navigate correctly even when a node has no
        droot entry (i.e. it is not connected to the main root in G).
        """
        if node in droot:
            return droot[node]
        return min(euclidean(node, mr) for mr in main_root_nodes)
 
    length  = 0
    current = tip
    visited = set()
 
    print(f"\n    [lateral_root_path_length] called for tip {tip}")
    print(f"    [lateral_root_path_length] tip droot = {droot.get(tip, 'NOT IN DROOT (disconnected)')}")
    print(f"    [lateral_root_path_length] tip effective_droot = {effective_droot(tip):.6f}")
 
    while True:
        visited.add(current)
        print(f"\n    [lateral_root_path_length] at node {current} "
              f"| length so far = {length:.6f} | visited = {visited}")
 
        best_neighbor    = None
        best_eff_droot   = float('inf')
        best_edge_len    = None
 
        for neighbor in G.neighbors(current):
            if neighbor in visited:
                print(f"    [lateral_root_path_length]   neighbor {neighbor} already visited -- skipping")
                continue
 
            label    = G.nodes[neighbor]['label']
            edge_len = G[current][neighbor]['length']
            eff_d    = effective_droot(neighbor)
            print(f"    [lateral_root_path_length]   neighbor {neighbor} | label = '{label}' "
                  f"| edge = {edge_len:.6f} | effective_droot = {eff_d:.6f}"
                  + (" (from BFS)" if neighbor in droot else " (euclidean fallback — disconnected)"))
 
            # -----------------------------------------------------------------
            # CASE 1 FIX — main root node found: add this final edge and stop
            # immediately. No other neighbors are considered, so sibling
            # branches are never entered.
            # -----------------------------------------------------------------
            if label in ('main root', 'main root base'):
                length += edge_len
                print(f"    [lateral_root_path_length]   -> MAIN ROOT reached at {neighbor}: "
                      f"add edge {edge_len:.6f}, total = {length:.6f}. Stopping.")
                return length
 
            # Among unvisited lateral neighbors, pick the one closest to root.
            if label in ('lateral root', 'lateral root tip'):
                if eff_d < best_eff_droot:
                    best_eff_droot = eff_d
                    best_neighbor  = neighbor
                    best_edge_len  = edge_len
 
        # -----------------------------------------------------------------
        # CASE 2 FIX — walk exhausted without finding a main root node.
        # This is the end of a disconnected lateral component. Add the
        # euclidean distance from the current node to the nearest main root
        # node, so the disconnected tip still contributes a meaningful curve
        # value rather than being skipped or returning None.
        # -----------------------------------------------------------------
        if best_neighbor is None:
            nearest_mr   = min(main_root_nodes, key=lambda mr: euclidean(current, mr))
            gap_dist     = euclidean(current, nearest_mr)
            length      += gap_dist
            print(f"    [lateral_root_path_length]   -> no further lateral neighbors from {current}.")
            print(f"    [lateral_root_path_length]   -> DISCONNECTED: nearest main root node = {nearest_mr}, "
                  f"euclidean gap = {gap_dist:.6f}, adding to length (total = {length:.6f}). Stopping.")
            return length
 
        print(f"    [lateral_root_path_length]   -> stepping to {best_neighbor} "
              f"(effective_droot = {best_eff_droot:.6f}), adding edge {best_edge_len:.6f}")
        length  += best_edge_len
        current  = best_neighbor

def conduction_delay_v3(G, cost_spec=HOMOGENEOUS): # v3
    droot = {}
    queue = []
    visited = set()
    root = G.graph.get('main root base', G.graph.get('main root'))
    queue.append(root)
    droot[root] = 0
    delay = 0

    # Pre-compute the list of main root nodes once; passed into
    # lateral_root_path_length for the disconnected-tip euclidean fallback.
    main_root_nodes = [n for n in G.nodes()
                       if G.nodes[n]['label'] in ('main root', 'main root base')]
 
    print(f"\n========== conduction_delay: starting BFS from root {root} ==========")
    print(f"  main root nodes ({len(main_root_nodes)} total): {main_root_nodes}")

    while len(queue) > 0:
        curr = queue.pop(0)
        assert curr not in visited
        visited.add(curr)

        if G.nodes[curr]['label'] == 'lateral root tip':
            curve = lateral_root_path_length(G, curr, droot, main_root_nodes)
            to_root = droot[curr] - curve   # subtract lateral length to get main root distance
            # troubleshooting
            if to_root < 0:
                print(f"Warning: negative to_root={to_root:.6f} at tip {curr}, "
                      f"droot = {droot[curr]:.6f}, curve = {curve:.6f}")
            to_root   = max(0.0, to_root)
            increment = cost_spec.delay_transform(curve, to_root)
            print(f"  cost_spec.delay_transform({curve:.6f}, {to_root:.6f}) = {increment:.6f}")
            delay += increment
            print(f"  running delay total = {delay:.6f}")

        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + G[curr][u]['length']
    # --- Phase 2: process disconnected lateral tips not reached by BFS ---
    unreached = set(G.nodes()) - visited
    disconnected_tips = [n for n in unreached
                         if G.nodes[n]['label'] == 'lateral root tip']
 
    if disconnected_tips:
        print(f"\n  --- Phase 2: {len(disconnected_tips)} disconnected lateral root tip(s) ---")
        for curr in disconnected_tips:
            print(f"\n--- Disconnected tip {curr} | label = '{G.nodes[curr]['label']}' | NOT IN droot ---")
            print(f"  >>> computing curve via lateral_root_path_length (euclidean fallback active)")
            curve = lateral_root_path_length(G, curr, droot, main_root_nodes)
 
            # For disconnected tips, droot[curr] does not exist.
            # to_root is defined as 0: there is no known main-root path distance,
            # so the entire curve value is treated as the lateral length.
            to_root = 0.0
            print(f"  curve (lateral walk + euclidean gap to nearest main root) = {curve:.6f}")
            print(f"  to_root = 0.0 (tip is disconnected; no BFS distance available)")
            increment = cost_spec.delay_transform(curve, to_root)
            print(f"  cost_spec.delay_transform({curve:.6f}, {to_root:.6f}) = {increment:.6f}")
            delay += increment
            print(f"  running delay total = {delay:.6f}")
    elif unreached:
        print(f"\n  {len(unreached)} non-tip node(s) unreachable from root (not counted in delay):")
        for node in unreached:
            print(f"      {node} | label = '{G.nodes[node]['label']}'")
    else:
        print(f"\n  All {len(visited)} nodes reached by BFS — no disconnected components.")
 
    print(f"\n========== conduction_delay: finished, total delay = {delay:.6f} ==========\n")
    assert len(visited) == G.number_of_nodes()

    return delay



'''
# --------------   VVVV TESTING VERSIONS VVVV   ----------------
def lateral_root_path_length(G, tip):
    """Sum edge lengths from tip of a lateral root back to main root insertion point."""
    length = 0
    visited = set()
    queue = [tip]
    print(f"    [lateral_root_path_length (1/11)] initial queue: {queue}")

    while queue:
        print(f"    [lateral_root_path_length (2/11)] queue state: {queue} | visited so far: {visited}")
        node = queue.pop(0)
        print(f"    [lateral_root_path_length (3/11)] popped node {node}")

        if node in visited:
            print(f"    [lateral_root_path_length (4/11)]   already visited {node} -- skipping")
            continue
        visited.add(node)
        print(f"    [lateral_root_path_length (5/11)]   marking {node} as visited")
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                label = G.nodes[neighbor]['label']

                edge_len = G[node][neighbor]['length'] # --- TODO: REMOVE (this is part of the testing w/ print statements)
                print(f"    [lateral_root_path_length (6/11)]   checking neighbor {neighbor} | label = '{label}' | edge length {node}->{neighbor} = {edge_len:.6f}")

                if label in ('lateral root', 'lateral root tip'):
                    length += G[node][neighbor]['length']
                    queue.append(neighbor)
                    print(f"    [lateral_root_path_length (7/11)]     -> still on the lateral: add {edge_len:.6f} to length (running total = {length:.6f}), enqueue {neighbor}")

                elif label in ('main root', 'main root base'):
                    length += G[node][neighbor]['length']
                    print(f"    [lateral_root_path_length (8/11)]     -> reached main root at {neighbor}: add {edge_len:.6f} to length (running total = {length:.6f}), NOT enqueued (stop here)")
                    # stop here — this is the insertion point
            else: # TODO: REMOVE (this is part of the testing w/ print statements)
                print(f"    [lateral_root_path_length (9/11)]   neighbor {neighbor} already visited -- skipping (potential branch/cycle in lateral)")
                print(f"    [lateral_root_path_length (10/11)] done. visited nodes: {visited}")
                print(f"    [lateral_root_path_length (11/11)] returning total length = {length:.6f}")
    print(f"    [lateral_root_path_length (FINAL/11)] Returning a final length of {length:.6f}\n")
    return length

def conduction_delay(G, cost_spec=HOMOGENEOUS):
    droot = {}
    queue = []
    visited = set()
    root = G.graph.get('main root base', G.graph.get('main root'))
    queue.append(root)
    droot[root] = 0
    delay = 0

    print(f"\n========== START conduction_delay: starting BFS from root {root} START ==========")

    while len(queue) > 0:
        curr = queue.pop(0)
        assert curr not in visited
        visited.add(curr)

        print(f"\n--- [1/12] Popped node {curr} | label = '{G.nodes[curr]['label']}' | droot[{curr}] = {droot[curr]:.6f} ---")
        
        if G.nodes[curr]['label'] == 'lateral root tip':

            print(f"  >>> [2/12] {curr} is a lateral root tip -- computing its contribution to delay")
            
            curve = lateral_root_path_length(G, curr)
            
            print(f"  [3/12] curve (path length along the lateral, tip -> insertion point) = {curve:.6f}....")
            print(f"  [4/12] ....droot[{curr}] (BFS distance from root to {curr}, following the tree) = {droot[curr]:.6f}")
            
            to_root = droot[curr] - curve   # subtract lateral length to get main root distance
            
            print(f"  [5/12] to_root = droot[{curr}] - curve = {droot[curr]:.6f} - {curve:.6f} = {to_root:.6f}")
            
            # troubleshooting
            if to_root < 0:
                print(f"Warning: negative to_root={to_root:.6f} at tip {curr}, "
                      f"droot = {droot[curr]:.6f}, curve = {curve:.6f}")
            to_root = max(0.0, to_root)

            print(f"  [6/12] to_root (clamped to >= 0) = {to_root:.6f}")
            increment = cost_spec.delay_transform(curve, to_root) # TODO: REMOVE (this is part of the testing w/ print statements)
            print(f"  [7/12] cost_spec.delay_transform(curve={curve:.6f}, to_root={to_root:.6f}) = {increment:.6f}")

            delay += cost_spec.delay_transform(curve, to_root)

            print(f"  [8/12] delay so far (running total) = {delay:.6f}")

            print(f"[9/12] Delay at node {curr}: {delay}")

        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                print(f"  [10/12] appending {u} to queue. current queue: {queue}")
                droot[u] = droot[curr] + G[curr][u]['length']
                print(f"  [11/12] droot at {u}: {droot[u]}")

    assert len(visited) == G.number_of_nodes()

    print(f"  [FINAL/12] Returning final delay of --> {delay}")
    return delay

def conduction_delay_initial(G):
    """
    use a breadth-first search to compute the distance to from the root to each point

    when we encounter a visit node for the first time, we record its distance to the root
    (which is the sum of its parent's distance, plus the length of the edge from the parent
    to the current node').  We keep a running total of the total distances from the root
    to each node.
    """
    droot = {}
    queue = []
    curr = None
    visited = set()

    root = G.graph.get('main root base', G.graph.get('main root')) # root = G.graph['main root']

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
            print(f"Delay at node {curr}: {delay}") # ADDED
        for u in G.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + G[curr][u]['length']

    # make sure we visited every node
    assert len(visited) == G.number_of_nodes()

    return delay

# # --------------   ^^^^ TESTING VERSIONS ^^^^   ----------------
'''


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
    scatter_df = scatter_df[scatter_df['model'] != 'random']
    pylab.figure()
    sns.scatterplot(x='wiring cost', y='conduction delay', hue='model', data=scatter_df)
    plot_dir = '%s/%s' % (outdir, arbor_name)
    #print('mkdir -p %s' % plot_dir)
    os.system('mkdir -p %s' % plot_dir) #for some reason my system is saying the syntax of this command is inccorrect
    pylab.savefig('%s/%s-pareto-front.pdf' % (plot_dir, arbor_name))


def main():
    # G = read_arbor_full('091_4_S_day5.csv')
    # 189_3_C_day3
    # 194_1_C_day3
     #G = read_arbor_full('189_3_C_day3.csv') #- produces an image
     #G = read_arbor_full('194_1_C_day3.csv') #- produces an image
     print("hello") #G = read_arbor_full('001_1_C_day5.csv')
     #viz_trees(G)
     #viz_front(G)
    #for arbor in os.listdir(RECONSTRUCTIONS_DIR):
    #    print(arbor)
    #    G = read_arbor_full(arbor)
    #    viz_trees(G)
    #    #viz_front(G)


if __name__ == '__main__':
    main()



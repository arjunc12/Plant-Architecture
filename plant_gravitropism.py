import math
import scipy.integrate as integrate
import pylab
import numpy as np
import sys
import read_arbor_reconstruction as rar
import networkx as nx
import pareto_functions as pf
from constants import *
from scipy.optimize import minimize_scalar, fsolve
from scipy.spatial.distance import euclidean
import os
import argparse
import pandas as pd
import warnings
import optimal_midpoint

# multiprocessing imports
from multiprocessing import Pool
import functools
import argparse

# OPTIMIZATION_METHOD options:
#   'brute_force' - reliable, 101 evaluations per segment
#   'brent'       - faster (~15 evaluations), assumes unimodal cost function
#   'analytical'  - fsolve on costprime derivative, kept for reference but not recommended
OPTIMIZATION_METHOD = 'brent'

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


# -------------------------
# Worker function — must be at module level for multiprocessing to pickle it
# -------------------------
def process_arbor_worker(arbor_fname, path, smart, smart_num, smart_grid_size, smart_grid_mesh,
                          amin, amax, astep, Gmin, Gmax, Gstep, verbose=False):
    """Process a single arbor — called by each worker process."""
    print(f"[START] {arbor_fname}", flush=True)

    fname = '%s/%s' % (path, arbor_fname)

    if not rar.has_reconstruction(arbor_fname):
        print(f"Skipping {arbor_fname}: no reconstruction found")
        return

    skip = initialize_file(fname, arbor_fname)

    if smart:
        df = pd.read_csv(fname, skipinitialspace=True)
        params, smart_skip = generate_smart_grid(df, smart_num, smart_grid_size, smart_grid_mesh)
        skip |= smart_skip
    else:
        params = generate_grid(amin, amax, astep, Gmin, Gmax, Gstep)

    process_arbor(arbor_fname, fname, params, skip, verbose=verbose)

    print(f"[DONE] {arbor_fname}", flush=True)

# -------------------------
# Geometry utilities
# -------------------------

def is_between(a, x, b):
    """Returns True if x is strictly between a and b (in either order)."""
    return a < x < b or b < x < a


def calc_coeff(G, x, y, p, q):
    """
    Returns coefficients b, c of the parabola G*x^2 + b*x + c
    that passes through (x, y) and (p, q).
    """
    b = (q - y - G * (p*p - x*x)) / (p - x)
    c = q - G * p*p - b * p
    return b, c


def curve_length_approx(G, x0, y0, p, q):
    """
    Arc length of the parabola G*x^2 + b*x + c between x0 and p,
    where the parabola passes through (x0, y0) and (p, q).
    """
    b, c = calc_coeff(G, x0, y0, p, q)
    def differential(x):
        return pylab.sqrt(1 + (2 * G * x + b)**2)
    arc, _ = integrate.quad(differential, min(x0, p), max(x0, p))
    return arc

def curve_length(G, x0, y0, p, q):
    """
    Arc length of the parabola G*x^2 + b*x + c between (x0, y0) and (p, q).
    Uses closed-form solution when G != 0, Euclidean distance when G == 0.
    """
    if G == 0:
        # Straight line distance
        return euclidean((x0, y0), (p, q))

    # Shift to local frame: branch point becomes origin
    p_local = p - x0
    q_local = q - y0

    k = (q_local - G * p_local**2) / p_local

    theta_0 = math.atan(k)
    theta_p = math.atan(2 * G * p_local + k)

    def sec(theta):
        return 1.0 / math.cos(theta)

    def F(theta):
        return sec(theta) * math.tan(theta) + math.log(abs(sec(theta) + math.tan(theta)))

    return abs((1.0 / (4 * G)) * (F(theta_p) - F(theta_0)))


def orthogonal_distance_to_curve(G, b, c, obs_x, obs_y, x_start, x_end, num_samples=1000):
    """
    Approximate orthogonal (perpendicular) distance from observed point
    (obs_x, obs_y) to the parabola G*x^2 + b*x + c, sampled over [x_start, x_end].
    """
    xs = np.linspace(x_start, x_end, num_samples)
    ys = G * xs**2 + b * xs + c
    dists = np.sqrt((obs_x - xs)**2 + (obs_y - ys)**2)
    return dists.min()


# -------------------------
# Cost computation
# -------------------------

def compute_cost(alpha, G, seg_base_dist, t, seg_length, branch_x, branch_y, tip_x, tip_y):
    """
    Compute total cost, wiring, and delay for a given branch point.

    Parameters
    ----------
    seg_base_dist : float
        Distance from root base to start of segment (x0, y0).
    t : float
        Position along segment [0, 1].
    seg_length : float
        Length of the main root segment.
    branch_x, branch_y : float
        Coordinates of the branch point on the main root.
    tip_x, tip_y : float
        Coordinates of the lateral root tip.
    """
    curve = curve_length(G, branch_x, branch_y, tip_x, tip_y)
    to_root = seg_base_dist + t * seg_length
    wiring = curve
    delay = curve + to_root
    cost = alpha * wiring + (1 - alpha) * delay
    return cost, wiring, delay


def branch_point_from_t(x0, y0, x1, y1, t):
    """Linearly interpolate a branch point along segment (x0,y0)-(x1,y1) at parameter t."""
    return x0 + t * (x1 - x0), y0 + t * (y1 - y0)


# -------------------------
# Optimization: brute force (used when tip x falls between segment endpoints)
# -------------------------

def find_best_cost_brute_force(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q):
    """
    Find the optimal branch point on segment (x0,y0)-(x1,y1) for lateral tip (p, q)
    by brute-force search over t in [0, 1] with step 0.01.

    Returns
    -------
    tuple : (cost, wiring, delay, best_t, best_x, best_y, p, q)
    """
    seg_length = euclidean((x0, y0), (x1, y1))
    best_cost = math.inf
    best_wiring = math.inf
    best_delay = math.inf
    best_t = None
    best_x = None
    best_y = None

    for t in pylab.arange(0, 1 + 0.01, 0.01):
        branch_x, branch_y = branch_point_from_t(x0, y0, x1, y1, t)
        cost, wiring, delay = compute_cost(
            alpha, G, seg_base_dist, t, seg_length, branch_x, branch_y, p, q
        )
        if cost <= best_cost:
            best_cost = cost
            best_wiring = wiring
            best_delay = delay
            best_t = t
            best_x = branch_x
            best_y = branch_y

    return best_cost, best_wiring, best_delay, best_t, best_x, best_y, p, q

# -------------------------
# Enhanced brute force using Brent's method
# -------------------------

def find_best_cost_brent(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q):
    """
    Find the optimal branch point on segment (x0,y0)-(x1,y1) for lateral tip (p, q)
    using Brent's method to directly minimize the cost function.

    For G=0, falls back to exact analytical solution from optimal_midpoint.py.
    For G!=0, uses minimize_scalar with method='bounded' on [0, 1].

    Returns
    -------
    tuple : (cost, wiring, delay, best_t, best_x, best_y, p, q)
    """
    seg_length = euclidean((x0, y0), (x1, y1))

    # G=0 case: use exact analytical solution from optimal_midpoint.py
    if G == 0:
        if alpha == 1:
            cost_val, (best_x, best_y), best_t = optimal_midpoint.optimal_midpoint_alpha1(
                (x0, y0), (x1, y1), (p, q)
            )
        else:
            cost_val, (best_x, best_y), best_t = optimal_midpoint.optimal_midpoint_exact(
                (x0, y0), (x1, y1), (p, q), alpha, seg_base_dist
            )
        wiring = euclidean((best_x, best_y), (p, q))
        to_root = seg_base_dist + best_t * seg_length
        delay = wiring + to_root
        return cost_val, wiring, delay, best_t, best_x, best_y, p, q

    # G != 0: minimize cost directly using Brent's method
    def cost_at_t(t):
        branch_x, branch_y = branch_point_from_t(x0, y0, x1, y1, t)
        c, _, _ = compute_cost(alpha, G, seg_base_dist, t, seg_length, branch_x, branch_y, p, q)
        return c

    result = minimize_scalar(cost_at_t, bounds=(0, 1), method='bounded')
    best_t = result.x
    best_x, best_y = branch_point_from_t(x0, y0, x1, y1, best_t)
    best_cost, best_wiring, best_delay = compute_cost(
        alpha, G, seg_base_dist, best_t, seg_length, best_x, best_y, p, q
    )

    return best_cost, best_wiring, best_delay, best_t, best_x, best_y, p, q


# -------------------------
# Optimization: analytical (used when tip x does not fall between segment endpoints)
# -------------------------

def make_costprime(G, alpha, l, theta, p, q):
    """
    Returns the derivative of cost w.r.t. t for the analytical case.

    Parameters
    ----------
    G : float
        Gravity parameter.
    alpha : float
        Weighting parameter.
    l : float
        Length of the main root segment.
    theta : float
        Angle of the segment.
    p, q : float
        Coordinates of the lateral root tip (shifted to local frame).
    """
    A1 = G * (l * math.cos(theta))**2
    B1 = -l * math.sin(theta)
    C1 = q - G * p**2
    D1 = -l * math.cos(theta)
    E1 = p

    def b(t):
        return (A1*t**2 + B1*t + C1) / (D1*t + E1)

    def bprime(t):
        num = (D1*t + E1) * (2*A1*t + B1) - D1 * (A1*t**2 + B1*t + C1)
        den = (D1*t + E1)**2
        return num / den

    def costprime(t):
        bt = b(t)
        term1 = (bprime(t) / (2 * G)) * (
            math.sqrt(1 + (2*G*p + bt)**2) -
            math.sqrt(1 + (2*G * t * l * math.cos(theta) + bt)**2)
        )
        term2 = (1 - alpha) * l
        term3 = math.sqrt(1 + (2*G * t * l * math.cos(theta) + bt)**2) * l * math.cos(theta)
        return term1 + term2 - term3

    return costprime


def find_root_in_unit_interval(func, num_guesses=1):
    """
    Find roots of func in [0, 1] using fsolve with evenly spaced initial guesses,
    excluding endpoints.
    """
    roots = []
    guesses = np.linspace(0, 1, num_guesses + 2)[1:-1]
    for guess in guesses:
        try:
            root = fsolve(func, guess)[0]
            if 0 <= root <= 1 and not any(np.isclose(root, r) for r in roots):
                roots.append(root)
        except Exception:
            pass
    return sorted(roots)

def find_best_cost_analytical(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q):
    """
    Find the optimal branch point on segment (x0,y0)-(x1,y1) for lateral tip (p, q)
    using the analytical derivative of the cost function.

    For G=0, uses exact analytical solution from optimal_midpoint.py.
    For alpha=1, minimizes curve length directly via scipy minimize_scalar.
    Otherwise, uses analytical costprime approach with fsolve.

    Returns
    -------
    tuple : (cost, wiring, delay, best_t, best_x, best_y, p, q)
    """

    seg_length = euclidean((x0, y0), (x1, y1))

    # G=0 case: use exact analytical solution from optimal_midpoint.py
    if G == 0:
        if alpha == 1:
            cost_val, (best_x, best_y), best_t = optimal_midpoint.optimal_midpoint_alpha1(
                (x0, y0), (x1, y1), (p, q)
            )
        else:
            cost_val, (best_x, best_y), best_t = optimal_midpoint.optimal_midpoint_exact(
                (x0, y0), (x1, y1), (p, q), alpha, seg_base_dist
            )
        wiring = euclidean((best_x, best_y), (p, q))
        to_root = seg_base_dist + best_t * seg_length
        delay = wiring + to_root
        return cost_val, wiring, delay, best_t, best_x, best_y, p, q
    # G != 0: use analytical costprime with fsolve
    else:
        # theta = math.atan2(abs(y1 - y0), abs(x1 - x0)) if (x1 != x0 and y1 != y0) else 0
        theta = math.atan2(y1 - y0, x1 - x0)
        p_local = p - x0
        q_local = q - y0

        costprime = make_costprime(G, alpha, seg_length, theta, p_local, q_local)

        def cost_at_t(t):
            branch_x, branch_y = branch_point_from_t(x0, y0, x1, y1, t)
            c, _, _ = compute_cost(alpha, G, seg_base_dist, t, seg_length, branch_x, branch_y, p, q)
            return c

        roots = find_root_in_unit_interval(costprime)
        valid_roots = [r for r in roots if 0 <= r <= 1]

        if valid_roots:
            best_t = min(valid_roots, key=cost_at_t)
        else:
            best_t = 0.0 if cost_at_t(0) <= cost_at_t(1) else 1.0

        best_x, best_y = branch_point_from_t(x0, y0, x1, y1, best_t)
        best_cost, best_wiring, best_delay = compute_cost(
            alpha, G, seg_base_dist, best_t, seg_length, best_x, best_y, p, q
        )

        return best_cost, best_wiring, best_delay, best_t, best_x, best_y, p, q

# -------------------------
# Main root utilities
# -------------------------

def get_main_root_segments(arbor):
    """
    BFS from main root base along 'main root' labeled nodes, returning
    an ordered list of segment tuples ((x0, y0), (x1, y1)).
    """
    base = arbor.graph['main root base']

    segments = []
    visited = {base}
    queue = [base]

    while queue:
        curr = queue.pop(0)
        for neighbor in arbor.neighbors(curr):
            if neighbor in visited:
                continue
            if arbor.nodes[neighbor]['label'] in ('main root', 'main root base'):
                segments.append((curr, neighbor))
                visited.add(neighbor)
                queue.append(neighbor)

    return segments


def compute_main_root_base_distances(arbor):
    """
    Returns a dict mapping each main root node to its distance from the main root base,
    using edge 'length' attributes and the ordering from get_main_root_segments.
    """
    base = arbor.graph['main root base']

    base_dist = {base: 0}
    for seg_start, seg_end in get_main_root_segments(arbor):
        base_dist[seg_end] = base_dist[seg_start] + arbor[seg_start][seg_end]['length']

    return base_dist


def main_root_length(arbor):
    """Total length of the main root, using edge 'length' attributes."""
    return sum(
        arbor[u][v]['length']
        for u, v in get_main_root_segments(arbor)
    )


def get_insertion_segment(arbor, lateral_tip, segments):
    """
    For a given lateral root tip, walk up the graph until hitting a main root node,
    then find which segment that insertion point belongs to.
    Returns all segments up to and including the insertion segment.

    Parameters
    ----------
    arbor : networkx.Graph
        Observed arbor graph.
    lateral_tip : tuple
        (x, y) of the lateral root tip.
    segments : list
        Ordered list of main root segments from get_main_root_segments.

    Returns
    -------
    list of segments up to and including the insertion segment
    """
    # BFS up from tip until we hit a main root node
    visited = set()
    queue = [lateral_tip]
    insertion_point = None

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        label = arbor.nodes[node]['label']
        if label in ('main root', 'main root base'):
            insertion_point = node
            break
        for neighbor in arbor.neighbors(node):
            if neighbor not in visited:
                queue.append(neighbor)

    assert insertion_point is not None, f"No main root node found from tip {lateral_tip}"

    # Find the segment that contains the insertion point and return all up to it
    valid_segments = []
    for seg in segments:
        valid_segments.append(seg)
        if insertion_point in seg:
            break

    return valid_segments

def get_closest_and_valid_segments(lat_tips, segments):
    """
    For each lateral tip, finds the closest main root segment and all
    valid segments (those at or before the closest one by y-coordinate).

    Note: currently unused — arbor_best_cost loops over all segments instead.
    """
    all_closest = []
    all_valid_segs = []

    for tip in lat_tips:
        tip_x, tip_y = tip
        best_distance = math.inf
        best_seg = None

        for seg in segments:
            x0, y0 = seg[0]
            x1, y1 = seg[1]

            B = (x1 - x0)**2 + (y1 - y0)**2
            A = (x0 - tip_x) * (x1 - x0) + (y0 - tip_y) * (y1 - y0)
            t = A / B if B != 0 else -1

            if 0 <= t <= 1:
                c = abs((x1 - x0) * (y0 - tip_y) - (y1 - y0) * (x0 - tip_x))
                d = c / math.sqrt(B)
            else:
                d = min(
                    euclidean(tip, seg[0]),
                    euclidean(tip, seg[1])
                )

            if d < best_distance:
                best_distance = d
                best_seg = seg

        all_closest.append(best_seg)
        valid = [seg for seg in segments if seg[1][1] <= best_seg[1][1]]
        all_valid_segs.append(valid)

    return all_closest, all_valid_segs


# -------------------------
# Core optimization
# -------------------------

def optimize_tip(tip, segments, base_dist, alpha, G):
    p, q = tip
    results = []

    for seg in segments:
        x0, y0 = seg[0]
        x1, y1 = seg[1]
        seg_base_dist = base_dist[(x0, y0)]

        if is_between(x0, p, x1) or OPTIMIZATION_METHOD == 'brute_force':
            result = find_best_cost_brute_force(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q)
        elif OPTIMIZATION_METHOD == 'brent':
            result = find_best_cost_brent(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q)
        else:
            result = find_best_cost_analytical(alpha, G, seg_base_dist, x0, y0, x1, y1, p, q)

        results.append(result)

    best = min(results)
    return best


def arbor_best_cost(arbor, G, alpha):
    """
    For each lateral root tip in the arbor, find the optimal branch point
    on the main root under the given (G, alpha) parameters.

    Parameters
    ----------
    arbor : networkx.Graph
        Already-loaded observed arbor graph.
    G : float
        Gravity parameter.
    alpha : float
        Weighting parameter.

    Returns
    -------
    list of tuples : [(cost, wiring, delay, best_t, best_x, best_y, tip_x, tip_y), ...]
    """
    segments = get_main_root_segments(arbor)
    base_dist = compute_main_root_base_distances(arbor)

    lat_tips = [
        node for node in arbor.nodes()
        if arbor.nodes[node]['label'] == 'lateral root tip'
    ]

    final = []
    for tip in lat_tips:
        valid_segments = get_insertion_segment(arbor, tip, segments)
        result = optimize_tip(tip, valid_segments, base_dist, alpha, G)
        if result is not None:
            final.append(result)
        else:
            print(f"Warning: No valid results for lateral tip at {tip}")

    return final


# -------------------------
# Error calculation
# -------------------------

def collect_lateral_root_points(arbor, lateral_tip):
    """
    BFS from lateral_tip through 'lateral root' and 'lateral root tip' nodes
    in the observed arbor graph.

    Returns
    -------
    list of (x, y) tuples belonging to this lateral root
    """
    lateral_points = []
    visited = set()
    queue = [lateral_tip]

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        label = arbor.nodes[node]['label']
        if label in ('lateral root', 'lateral root tip'):
            lateral_points.append(node)
            for neighbor in arbor.neighbors(node):
                if neighbor not in visited and arbor.nodes[neighbor]['label'] in ('lateral root', 'lateral root tip'):
                    queue.append(neighbor)

    return lateral_points


def collect_lateral_root_segments(arbor, lateral_tip):
    """
    Return list of (x0, y0, x1, y1) segments along the lateral root path
    from tip back to the main root insertion point.
    """
    segments = []
    path = collect_lateral_root_points(arbor, lateral_tip)  # existing BFS
    for i in range(len(path) - 1):
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        segments.append((x0, y0, x1, y1))
    return segments


def calculate_orthogonal_errors(gravity, arbor, main_root_pt, lateral_tip,
                                 n_subsample=100):
    """
    Compute total orthogonal distance and total squared orthogonal distance
    between the fitted parabola and the lateral root path.

    Sub-discretizes each lateral root segment into n_subsample points
    so that lightly-traced lateral roots are treated consistently with
    densely-traced ones.
    """
    px, py = main_root_pt
    tip_x, tip_y = lateral_tip

    b, c = calc_coeff(gravity, px, py, tip_x, tip_y)
    x_start, x_end = min(px, tip_x), max(px, tip_x)

    segments = collect_lateral_root_segments(arbor, lateral_tip)

    if not segments:
        return 0.0, 0.0

    # Sub-discretize all segments into sample points — vectorized
    all_xs = []
    all_ys = []
    for x0, y0, x1, y1 in segments:
        ts = np.linspace(0, 1, n_subsample, endpoint=False)
        all_xs.append(x0 + ts * (x1 - x0))
        all_ys.append(y0 + ts * (y1 - y0))

    # Include the final endpoint of the last segment
    all_xs.append(np.array([segments[-1][2]]))
    all_ys.append(np.array([segments[-1][3]]))

    obs_x = np.concatenate(all_xs)
    obs_y = np.concatenate(all_ys)

    # Vectorized orthogonal distance to parabola
    # Find closest point on parabola G*x^2 + b*x + c to each (obs_x, obs_y)
    xs = np.linspace(x_start, x_end, 1000)
    ys = gravity * xs**2 + b * xs + c

    # For each observed point, find minimum distance to any point on the curve
    # Shape: (n_observed, 1) - (1, n_curve) = (n_observed, n_curve)
    dx = obs_x[:, np.newaxis] - xs[np.newaxis, :]
    dy = obs_y[:, np.newaxis] - ys[np.newaxis, :]
    dists = np.sqrt(dx**2 + dy**2).min(axis=1)

    total_orthogonal = dists.sum()
    total_sq_orthogonal = (dists**2).sum()

    return total_orthogonal, total_sq_orthogonal


# -------------------------
# Core evaluation
# -------------------------

def evaluate_parameters(arbor_fname, G, alpha):
    """
    Evaluate a single (G, alpha) combination for a given arbor.

    Returns
    -------
    tuple : (wiring, delay, total_orthogonal, total_sq_orthogonal)
    """
    # Load arbor once and reuse
    G_graph = rar.read_arbor_full(arbor_fname)
    results = arbor_best_cost(G_graph, G, alpha)

    wiring = 0
    delay = 0
    total_orthogonal = 0
    total_sq_orthogonal = 0

    for result in results:
        wiring += result[1]
        delay += result[2]

        main_root_pt = (result[4], result[5])
        lateral_tip = (result[6], result[7])

        orth, sq_orth = calculate_orthogonal_errors(G, G_graph, main_root_pt, lateral_tip)
        total_orthogonal += orth
        total_sq_orthogonal += sq_orth

    wiring += main_root_length(G_graph)

    return wiring, delay, total_orthogonal, total_sq_orthogonal


# -------------------------
# Conduction delay for observed arbor
# -------------------------

def gravitropism_conduction_delay(arbor):
    """
    BFS from main root base to compute total conduction delay for the observed arbor
    (sum of distances from root base to each lateral root tip).
    Uses edge 'length' attributes from the arbor graph.
    """
    root = arbor.graph['main root base']
    droot = {root: 0}
    visited = set()
    queue = [root]
    delay = 0

    while queue:
        curr = queue.pop(0)
        assert curr not in visited
        visited.add(curr)
        if arbor.nodes[curr]['label'] == 'lateral root tip':
            delay += droot[curr]
        for u in arbor.neighbors(curr):
            if u not in visited:
                queue.append(u)
                droot[u] = droot[curr] + arbor[curr][u]['length']

    assert len(visited) == arbor.number_of_nodes()
    return delay


# -------------------------
# Parameter generation
# -------------------------

def generate_grid(amin, amax, astep, Gmin, Gmax, Gstep):
    """Yield (G, alpha) pairs over the full parameter grid."""
    # Use round() with enough precision to avoid float issues
    # but enough to match how values are stored in the CSV (6 decimal places)
    G_vals = [round(g, 6) for g in pylab.arange(Gmin, Gmax + Gstep/2, Gstep)]
    a_vals = [round(a, 6) for a in pylab.arange(amin, amax + astep/2, astep)]

    for g in G_vals:
        for a in a_vals:
            yield g, a


def get_top_n_with_ties(df, col, n):
    """Return all rows tied within the top n values of col."""
    threshold = df[col].nsmallest(n).max()
    return df[df[col] <= threshold * (1 + 1e-9)][['G', 'alpha']]


def local_grid(Gc, ac, df_opt, grid_size, grid_mesh):
    Gc, ac = float(Gc), float(ac)

    # Find neighboring G values in the evaluated grid
    G_vals_evaluated = sorted(df_opt['G'].unique())
    G_idx = G_vals_evaluated.index(min(G_vals_evaluated, key=lambda x: abs(x - Gc)))
    G_left_idx  = max(0, G_idx - grid_size)
    G_right_idx = min(len(G_vals_evaluated) - 1, G_idx + grid_size)
    G_left  = G_vals_evaluated[G_left_idx]
    G_right = G_vals_evaluated[G_right_idx]

    # Find neighboring alpha values in the evaluated grid
    a_vals_evaluated = sorted(df_opt['alpha'].unique())
    a_idx = a_vals_evaluated.index(min(a_vals_evaluated, key=lambda x: abs(x - ac)))
    a_left_idx  = max(0, a_idx - grid_size)
    a_right_idx = min(len(a_vals_evaluated) - 1, a_idx + grid_size)
    a_left  = a_vals_evaluated[a_left_idx]
    a_right = a_vals_evaluated[a_right_idx]

    print(f"Refining around ({Gc:.4f}, {ac:.4f}) | "
          f"G: [{G_left:.4f}, {G_right:.4f}] | "
          f"alpha: [{a_left:.4f}, {a_right:.4f}]")

    # Local neighborhood mesh
    G_grid = np.linspace(G_left, G_right, grid_mesh)
    a_grid = np.linspace(a_left, a_right, grid_mesh)
    neighborhood = {
        (round(g, 6), round(a, 6))
        for g in G_grid for a in a_grid
    }

    # Axial sweeps within the neighborhood box but at finer resolution
    axial_mesh = grid_mesh

    alpha_sweep = {
        (round(Gc, 6), round(a, 6))
        for a in np.linspace(a_left, a_right, axial_mesh)
    }

    G_sweep = {
        (round(g, 6), round(ac, 6))
        for g in np.linspace(G_left, G_right, axial_mesh)
    }

    print(f"  Axial sweeps (mesh={axial_mesh}): "
          f"G={Gc:.4f} x alpha:[{a_left:.4f}, {a_right:.4f}] | "
          f"G:[{G_left:.4f}, {G_right:.4f}] x alpha={ac:.4f}")

    return neighborhood | alpha_sweep | G_sweep


def generate_smart_grid(df, smart_num, grid_size, grid_mesh):
    """
    Generate refined parameter candidates around top-performing points.

    Handles:
    - Ties at any rank boundary
    - Boundary extension when best point is at edge of G search space
    - Alpha strictly constrained to [0, 1] (convex combination requirement)
    - Adaptive step size based on neighborhood density

    Parameters
    ----------
    df : pd.DataFrame
    smart_num : int
        Number of top points per metric to refine around (with ties).
    grid_size : int
        Number of neighbors per dimension in local grid.
    grid_size : int
        How finely to discretize the local search space

    Returns
    -------
    tuple : (set of new (G, alpha) pairs, set of already-evaluated pairs to skip)
    """
    df_opt = df[df['arbor type'] == 'optimal'].copy()
    skip = set(zip(df_opt['G'].round(6).astype(float),
                   df_opt['alpha'].round(6).astype(float)))


    # Get top N with ties for orthogonal metrics
    best_orth = get_top_n_with_ties(df_opt, 'total orthogonal distance', smart_num)
    best_sq   = get_top_n_with_ties(df_opt, 'total squared orthogonal distance', smart_num)
    best = pd.concat([best_orth, best_sq]).drop_duplicates().reset_index(drop=True)

    # Get observed wiring/delay for pareto metrics
    df_obs = df[df['arbor type'] == 'observed']
    obs_wiring = df_obs['wiring cost'].iloc[0] if not df_obs.empty else None
    obs_delay  = df_obs['conduction delay'].iloc[0] if not df_obs.empty else None

    # Add pareto metrics if observed data available
    if obs_wiring is not None and obs_delay is not None:
        df_opt['pareto_dist'] = df_opt.apply(
            lambda r: euclidean(
                (obs_wiring, obs_delay),
                (r['wiring cost'], r['conduction delay'])
            ), axis=1
        )
        df_opt['pareto_scale'] = df_opt.apply(
            lambda r: pf.point_dist_scale(
                (r['wiring cost'], r['conduction delay']),
                (obs_wiring, obs_delay)
            ), axis=1
        )

        best_pd = get_top_n_with_ties(df_opt, 'pareto_dist', smart_num)

        # For pareto scale, closest to 1 rather than smallest
        df_opt['pareto_scale_dist_from_1'] = (df_opt['pareto_scale'] - 1.0).abs()
        best_ps = get_top_n_with_ties(df_opt, 'pareto_scale_dist_from_1', smart_num)

        best = pd.concat([best, best_pd[['G', 'alpha']],
                         best_ps[['G', 'alpha']]]).drop_duplicates().reset_index(drop=True)

    # Deduplicate tied alpha values at the same G — keep lowest alpha per G
    # Ties in alpha are constraint-induced and won't be broken by finer search
    # Ties in G are worth keeping — finer G search may break them
    # Keep lowest alpha per G — sort so keep='first' gives lowest alpha
    best = (best
        .sort_values(['G', 'alpha'])
        .drop_duplicates(subset=['G'], keep='first')
        .reset_index(drop=True))

    params = set()
    for _, row in best.iterrows():
        new_pts = local_grid(row['G'], row['alpha'], df_opt, grid_size, grid_mesh)
        params.update(p for p in new_pts if p not in skip)

    return params, skip

# -------------------------
# File I/O
# -------------------------

def initialize_file(fname, arbor):
    """
    Initialize output CSV and return set of already-evaluated (G, alpha) pairs.
    """
    first_time = not os.path.exists(fname) or os.path.getsize(fname) == 0

    if not first_time:
        df = pd.read_csv(fname, skipinitialspace=True)
        df = df[df['arbor type'] == 'optimal']
        return set(zip(df['G'].round(6), df['alpha'].round(6)))

    with open(fname, 'w') as f:
        f.write(
            'arbor type, G, alpha, wiring cost, conduction delay, '
            'total orthogonal distance, total squared orthogonal distance\n'
        )
        observed = rar.read_arbor_full(arbor)
        f.write('%s, %s, %s, %f, %f, %f, %f\n' % (
            "observed", "", "",
            pf.wiring_cost(observed),
            gravitropism_conduction_delay(observed),
            0, 0
        ))

    return set()


def append_result(fname, g, alpha, wiring, delay, orthogonal, sq_orthogonal):
    with open(fname, 'a') as f:
        f.write('%s, %.6f, %.6f, %f, %f, %f, %f\n' % (
            "optimal", g, alpha, wiring, delay, orthogonal, sq_orthogonal
        ))


# -------------------------
# Processing
# -------------------------

def process_arbor(arbor, fname, params, skip, verbose=False):
    """Evaluate all parameter combinations for a given arbor and save results."""
    for g, alpha in params:
        if (round(g, 6), round(alpha, 6)) in skip:
            continue

        # Only print G/alpha progress if verbose
        if verbose:
            print(f"Processing {arbor}: G={g}, alpha={alpha}")
        wiring, delay, orthogonal, sq_orthogonal = evaluate_parameters(arbor, g, alpha)
        append_result(fname, g, alpha, wiring, delay, orthogonal, sq_orthogonal)


def get_last_day_files():
    df = pd.read_csv("%s/metadata.csv" % METADATA_DIR, skipinitialspace=True)
    df['hormone'] = df['hormone'].fillna('')
    group_cols = ['genotype', 'replicate', 'condition', 'hormone']
    max_days = df.groupby(group_cols)['day'].transform('max')
    latest = df[df['day'] == max_days]
    return (latest['arbor name'] + '.csv').tolist()


# -------------------------
# CLI entry point
# -------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--amin', type=float, default=0)
    parser.add_argument('--amax', type=float, default=1)
    parser.add_argument('--astep', type=float, default=0.05)

    parser.add_argument('--Gmin', type=float, default=-2)
    parser.add_argument('--Gmax', type=float, default=2)
    parser.add_argument('--Gstep', type=float, default=0.2)

    parser.add_argument('--smart', action='store_true')
    parser.add_argument('--smartNumPoints', type=int, default=1)
    parser.add_argument('--smartGridSize', type=int, default=1)
    parser.add_argument('--smartGridMesh', type=int, default=10)

    parser.add_argument('--num_workers',      type=int,   default=1,
                        help='Number of parallel worker processes')

    parser.add_argument(
        '--optimization_method',
        type=str,
        default='brent',
        choices=['brent', 'brute_force', 'analytical'],
        help='Optimization method for finding best branch point (default: brent)'
    )

    parser.add_argument('--verbose', action='store_true', default=False)

    args = parser.parse_args()

    global OPTIMIZATION_METHOD
    OPTIMIZATION_METHOD = args.optimization_method

    path = f"{RESULTS_DIR}/gravitropism_pareto_fronts"
    os.makedirs(path, exist_ok=True)

    arbors = sorted(os.listdir(path)) if args.smart else sorted(get_last_day_files())
    total = len(arbors)

    # Bind all fixed arguments — only arbor_fname varies per worker call
    worker = functools.partial(
        process_arbor_worker,
        path=path,
        smart=args.smart,
        smart_num=args.smartNumPoints,
        smart_grid_size=args.smartGridSize,
        smart_grid_mesh=args.smartGridMesh,
        amin=args.amin,
        amax=args.amax,
        astep=args.astep,
        Gmin=args.Gmin,
        Gmax=args.Gmax,
        Gstep=args.Gstep,
        verbose=args.verbose,
    )

    print(f"Processing {total} arbors with {args.num_workers} workers "
          f"using {args.optimization_method}...")

    with Pool(processes=args.num_workers) as pool:
        for i, _ in enumerate(pool.imap_unordered(worker, arbors), 1):
            print(f"Completed {i}/{total} arbors ({100*i//total}%)",
                  flush=True)

    print("Done.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
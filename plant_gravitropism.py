import math
import point_similarity as ps
import scipy.integrate as integrate
import pylab
import mpmath
from scipy.misc import derivative
import plotly
from plotly import graph_objs as go
import sys
import read_arbor_reconstruction as rar
import networkx as nx
import pareto_functions as pf
from constants import *
import os
import pickle
import argparse
import pandas as pd

## returns the coefficients of the quadratic equation involving gravity
def calc_coeff(G, x, y, p, q):
    b = ((q - y - G*(p*p - x*x))/(p-x))
    c = (q - G*p*p - b*p)

    # assert (G * x * x) + (b * x) + c == y
    # assert (G * p * p) + (b * p) + c == q

    return b, c

## checks if a line has a positive slope given two points
def positive_slope(x0, y0, x1, y1):
    if x0 == x1 or y0 == y1:
        return False
    slope = (y1 - y0)/(x1 - x0)
    if slope >= 0:
        return True
    return False

## simply just a distance function
def length_func(x0, y0, x1, y1):
    length = pylab.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    return length

## a way to calculate theta based on two points
def get_theta(x0, y0, x1, y1):
    if x1 == x0 or y1 == y0:
        return 0
    theta = pylab.arctan((abs(y1 - y0))/(abs(x1 - x0)))
    return theta

## Returns the length of a curve (in this case a lateral root when gravity is not 0)
def curve_length(G, x0, y0, p, q):
    b, c = calc_coeff(G, x0, y0, p, q)
    def differential(x):
        return pylab.sqrt(1 + (2*G*x + b)**2)
    curve, tolerance = integrate.quad(differential, min(x0, p), max(x0, p))
    return curve

## Returns the distance from a point to the base of the plant
def distance_from_base(root_distance, x, y, x1, y1):
    pair1 = [x, y]
    pair2 = [x1, y1]
    distance = math.dist(pair1, pair2)
    if(x,y) == (x1, y1):
        assert distance == 0
    return distance + root_distance

## Returns the total cost along with the wiring and delay used to calculate it
def total_cost(alpha, G, root_distance, x0, y0, x1, y1, p, q):
    curve = curve_length(G, x1, y1, p, q)
    to_root = distance_from_base(root_distance, x0, y0, x1, y1)
    wiring = curve
    delay = (curve + to_root)
    cost = (alpha * wiring) +  ((1 - alpha) * delay)
    #print("curve = ", curve, "to root = " , to_root, "wiring = ", wiring, "delay = ", delay, "total cost = ", cost)
    #cost = curve + (1 - alpha) * distance_from_base(root_distance, x0, y0, x1, y1)
    return cost, wiring, delay

def find_best_cost(alpha, G, root_distance, x0, y0, x1, y1, p, q):
    results = []
    min_t = 0
    delta = 0.01
    max_t = 1
    best_t = math.inf
    best_cost = math.inf
    best_wiring = math.inf
    best_delay = math.inf
    l = length_func(x0, y0, x1, y1)
    theta = get_theta(x0, y0, x1, y1)
    x_opt = None
    y_opt = None
    best_x = None
    best_y = None
    for t in pylab.arange(min_t, max_t + delta, delta):
        is_positive = positive_slope(x0, y0, x1, y1)
        new_x = None
        new_y = None
        if is_positive:
            new_x = x0 + t*l*math.cos(theta)
            new_y = y0 + t*l*math.sin(theta)
        else:
            new_x = x0 - (t*l*math.cos(theta))
            new_y = y0 + (t*l*math.sin(theta))
        x_curr = pylab.linspace(min(p, new_x), max(p, new_x))
        cost, wiring, delay = total_cost(alpha, G, root_distance, x0, y0, new_x, new_y, p, q)
        if cost <= best_cost:
            best_cost = cost
            best_wiring = wiring
            best_delay = delay
            best_t = t
            b, c = calc_coeff(G, new_x, new_y, p, q)
            best_x = new_x
            best_y = new_y
            #x_opt = x_curr
            #y_opt = G * x_opt ** 2 + b * x_opt + c
        '''
        if t % 0.2 == 0:
            b, c = calc_coeff(G, new_x, new_y, p, q)
            y_inter =  G * x_curr ** 2 + b * x_curr + c
            intermediate_line = go.Scatter(x = x_curr,y = y_inter, mode = "lines", name = str(cost))
            fig.add_trace(intermediate_line)
           '''
        results.append(cost)
    ##opt_line = go.Scatter(x = x_opt, y = y_opt, mode = "lines", name = "Optimal: " + str(best_cost))
    ##fig.add_trace(opt_line)
    return best_cost, best_wiring, best_delay, best_t, best_x, best_y, p, q

def arbor_best_cost(fname, alpha, G, root_distance):
    arbor = rar.read_arbor_full(fname)
    main_root = []
    lat_tips = []
    line_segments = {}
    point_drawing = go.Figure()
    for node in arbor.nodes():
        if arbor.nodes[node]["label"] == ("main root") or arbor.nodes[node]["label"] == ("main root base"):
            main_root.append(node)
        if arbor.nodes[node]["label"] == ("lateral root tip"):
            lat_tips.append(node)
    for i in range(1, len(main_root)):
        line_segments[i] = main_root[i - 1], main_root[i]

    # for each lateral root tip iterate through every line segment to find lowest costing point on main root
    final = []
    for tip in lat_tips:
        curr_dist = 0
        results = []
        firstTime = True
        p = tip[0]
        q = tip[1]
        for seg in line_segments:
            x0 = line_segments[seg][0][0]
            y0 = line_segments[seg][0][1]
            x1 = line_segments[seg][1][0]
            y1 = line_segments[seg][1][1]
            if firstTime == True:
                result = find_best_cost(alpha, G, root_distance, x0, y0, x1, y1, p, q)
                curr_dist += length_func(x0, y0, x1, y1)
                firstTime = False
            else:
                result = find_best_cost(alpha, G, root_distance + curr_dist, x0, y0, x1, y1, p, q)
                curr_dist += length_func(x0, y0, x1, y1)
            results.append(result)
        final.append(min(results))

    return final


def graph_opt_lines(graph, final):
    for result in final:
        x0 = result[2]
        y0 = result[3]
        p = result[4]
        q = result[5]
        first_point = x0, y0
        second_point = p, q
        G = graph.graph['Gravity']
        b, c = calc_coeff(G, x0, y0, p, q)
        graph.add_node(first_point, pos=first_point)
        graph.add_node(second_point, pos=second_point)
        graph.add_edge(first_point, second_point, b = b, c = c)
    return graph

def get_line_segments(arbor):
    line_segments = {}
    main_root = []
    for node in arbor.nodes():
        if arbor.nodes[node]["label"] == ("main root") or arbor.nodes[node]["label"] == ("main root base"):
            main_root.append(node)
    for i in range(1, len(main_root)):
        line_segments[i] = main_root[i - 1], main_root[i]
    return line_segments


def graph_main_root(graph, line_segments):
     for seg in line_segments:
        x0 = line_segments[seg][0][0]
        y0 = line_segments[seg][0][1]
        x1 = line_segments[seg][1][0]
        y1 = line_segments[seg][1][1]
        first_point = x0, y0
        second_point = x1, y1


        graph.add_node(first_point, pos=first_point)
        graph.add_node(second_point, pos=second_point)
        graph.add_edge(first_point, second_point)


def modified_line_equation(G, main_root, lateral_tip):
    x, y = main_root
    p, q = lateral_tip
    if G == 0:
        m = (q - y) / (p - x)
        y_int = y - m * x
        return m, y_int
    else:
        b, c = calc_coeff(G, x, y, p, q)
        return b, c

def modified_calculate_distance(gravity, G, G_opt, main_root, lateral_tip):
    opt_y_coords, actual_y_coords = modified_fill_lateral_root(gravity, G, G_opt, main_root, lateral_tip)
    distances = []

    for x in range(len(opt_y_coords)):
        diff_square = (opt_y_coords[x] - actual_y_coords[x]) ** 2
        distances.append(diff_square)

    return sum(distances)


def modified_fill_lateral_root(gravity, G, G_opt, main_root, lateral_tip) :

    ## This method uses the lateral tip and main root to fill in points of the lateral root
    ## in order to perform distance calculation

    # get coefficients
    if gravity == 0:
        m, y_int = modified_line_equation(gravity, main_root, lateral_tip)
    else:
        b, c = modified_line_equation(gravity, main_root, lateral_tip)


    observed = {}
    optimal = {}
    observed, optimal = ps.create_dict(G, G_opt)
    backwards = {}

    ## reverses observed dictionary
    for node in reversed(observed):
        backwards[node] = observed[node]

    tip_found = False
    encountered_observed = []
    index = len(G.nodes) - 2

    ## loop backwards
    for node in backwards :
        if G.nodes[node]['label'] == "lateral root tip" and tip_found:
            break
        if lateral_tip == node:
            tip_found = True
           # print("tip was found")
            continue
        if tip_found == True and (list(G.nodes(data = True))[index][1]["label"] == "lateral root"):
           # print("not a tip")
            encountered_observed.append(node)
        index -= 1

    ## need to calculate points based on observed x-coordinates and line equation
    x_coords = []
    y_coords = []
    count = -1
    for point in encountered_observed:
        for coords in point:
          count += 1
          if count % 2 == 0 :
              x_coords.append(coords)
          else :
              y_coords.append(coords)
    added_nodes = []
    if gravity == 0:
        for x in x_coords:
            added_nodes.append(m * x + y_int)
    else:
        for x in x_coords:
            added_nodes.append(gravity*x*x + b*x + c)

    return added_nodes, y_coords


def calc_pareto_front(fname, amin=0, amax=1, astep=0.05, Gmin=-2, Gmax=2, Gstep=0.2, skip=None):
    G = rar.read_arbor_full(fname)
    if skip == None:
        skip = set()

    values = []
    for alpha in pylab.arange(amin, amax + astep, astep):
        for g in pylab.arange(Gmin, Gmax + Gstep, Gstep):
            if (alpha, g) in skip:
                continue
            G_opt = nx.Graph(Gravity = g)
            line_segs = get_line_segments(G)
            graph_main_root(G_opt, line_segs)
            final = arbor_best_cost(fname, alpha, g, 0) # 0 is the root distance but I figured it doesn't matter as code calculates proper root distance
            graph_opt_lines(G_opt, final)
            point_dist = 0
            #print("Calculating distances for alpha: " + str(alpha) + " and G = " + str(g))
            wiring = 0
            delay = 0
            for result in final:
                wiring += result[1]
                delay += result[2]
                main_root = result[4], result[5]
                lateral_tip = result[6], result[7]
                point_dist += modified_calculate_distance(g, G, G_opt, main_root, lateral_tip)
            wiring += main_root_distance(line_segs) # earlier, did not account for the main root when calculating wiring cost
            values.append((g, alpha, wiring, delay, point_dist))

    return values

def write_new_pareto_front_values(fname, arbor, amin=0, amax=1, astep=0.05, Gmin=-2, Gmax=2, Gstep=0.2):
    first_time = not os.path.exists(fname) or os.path.getsize(fname) == 0
    G = rar.read_arbor_full(arbor)
    print("Writing pareto front values for " + arbor)
    with open(fname, 'a') as f:
        skip = set()
        if first_time:
            f.write('arbor type, G, alpha, wiring cost, conduction delay, point distance\n')
            observed_graph = rar.read_arbor_full(arbor)
            observed_wiring = pf.wiring_cost(observed_graph)
            observed_delay = modified_conduction_delay(observed_graph)
            f.write('%s, %s, %s, %f, %f, %f\n' % ("observed", "", "", observed_wiring, observed_delay, 0.0))
        else:
            df = pd.read_csv(fname, skipinitialspace=True)
            df = df[df['arbor type'] == 'optimal']
            G_skip = list(df['G'])
            alpha_skip = list(df['alpha'])
            skip = set(zip(G_skip, alpha_skip))

        for g in pylab.arange(Gmin, Gmax + Gstep, Gstep):
            g = round(g, 2)
            for alpha in pylab.arange(amin, amax + astep, astep):
                alpha = round(alpha, 2)
                if (g, alpha) in skip:
                    continue
                print(g, alpha)
                G_opt = nx.Graph(Gravity = g)
                line_segs = get_line_segments(G)
                graph_main_root(G_opt, line_segs)
                final = arbor_best_cost(arbor, alpha, g, 0) # 0 is the root distance but I figured it doesn't matter as code calculates proper root distance
                graph_opt_lines(G_opt, final)
                point_dist = 0
                #print("Calculating distances for alpha: " + str(alpha) + " and G = " + str(g))
                wiring = 0
                delay = 0
                for result in final:
                    wiring += result[1]
                    delay += result[2]
                    main_root = result[4], result[5]
                    lateral_tip = result[6], result[7]
                    point_dist += modified_calculate_distance(g, G, G_opt, main_root, lateral_tip)
                wiring += main_root_distance(line_segs) # earlier, did not account for the main root when calculating wiring cost

                f.write('%s, %f, %f, %f, %f, %f\n' % ("optimal", g, alpha, wiring, delay, point_dist))

def main_root_distance(line_segments):
    distance = 0
    for seg in line_segments:
        x0 = line_segments[seg][0][0]
        y0 = line_segments[seg][0][1]
        x1 = line_segments[seg][1][0]
        y1 = line_segments[seg][1][1]
        distance += length_func(x0, y0, x1, y1)
    return distance

def modified_conduction_delay(G):
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

    root = G.graph['main root base']

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

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--amin', default=0, type=float)
    parser.add_argument('--amax', default=1, type=float)
    parser.add_argument('--astep', default=0.05, type=float)

    parser.add_argument('--Gmin', default=-2, type=float)
    parser.add_argument('--Gmax', default=2, type=float)
    parser.add_argument('--Gstep', default=0.2, type=float)

    args = parser.parse_args()
    amin = args.amin
    amax = args.amax
    astep = args.astep

    Gmin = args.Gmin
    Gmax = args.Gmax
    Gstep = args.Gstep

    #fname = '%s/plant_gravitropism.csv' % ARCHITECTURE_DIR
    #first_time = not os.path.exists(fname)
    #G_alpha_file = '%s/G_alpha_combinations.pkl' % RESULTS_DIR
    path = '%s/gravitropism_pareto_fronts' % RESULTS_DIR
    last_day_files = get_last_day_files()
    if not os.path.exists(path):
        os.mkdir(path)
    #processed_arbors = load_processed_arbors()
    #for arbor in os.listdir(RECONSTRUCTIONS_DIR):
    for key, arbor in last_day_files.items():

        #if arbor in processed_arbors:
           #print('%s already processed' % (arbor))
           #continue

        #clear_pickle_file(pickle_file)
        fname = '%s/%s' % (path, arbor)
        write_new_pareto_front_values(fname, arbor, amin=amin, amax=amax, astep=astep, Gmin=Gmin, Gmax=Gmax, Gstep=Gstep)

def load_processed_arbors():
    filename = '%s/processed_arbors.pkl' % RESULTS_DIR
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        return set()

def save_processed_arbors(processed_arbors):
    filename = '%s/processed_arbors.pkl' % RESULTS_DIR
    with open(filename, 'wb') as f:
        pickle.dump(processed_arbors, f)

def load_written_combinations():
    filename = '%s/G_alpha_combinations.pkl' % RESULTS_DIR
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        return set()

def save_written_combinations(written_combinations):
    filename = '%s/G_alpha_combinations.pkl' % RESULTS_DIR
    with open(filename, 'wb') as f:
        pickle.dump(written_combinations, f)

def clear_pickle_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def get_last_day_files():
    files_by_genotype = {}

    for file_name in os.listdir(RECONSTRUCTIONS_DIR):
        parts = file_name.split('_')

        genotype = parts[0]
        replicate = parts[1]
        condition = parts[2]
        hormone = None
        if len(parts) >= 3:
            hormone = parts[3]
        day = parts[-1].replace('.csv', '')
        day = int(day.strip('day'))

        key = (genotype, replicate, condition)
        if key not in files_by_genotype:
            files_by_genotype[key] = {}

        files_by_genotype[key][day] = file_name

    last_day_files = {}
    for key, day_files in files_by_genotype.items():
        last_day = max(day_files.keys())
        if last_day not in [5, 9]:
            continue
        last_day_files[key] = day_files[last_day]
    return last_day_files

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)

    '''
    with open(fname, 'a') as f:
        if first_time:
            f.write('arbor type, G, alpha, wiring cost, conduction delay, point distance\n')
        for arbor in os.listdir(RECONSTRUCTIONS_DIR):
            alpha, g, wiring, delay, point_distance = calc_pareto_front(arbor)
            arbor_name = arbor.strip('.csv')

            print("Calculating values from plant_gravitropism.py")
            print(arbor)
            f.write('%s, %f, %f, %f, %f, %f\n' % (arbor_name, G, alpha, wiring cost, conduction delay, point distance))
    '''

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
import pareto_functions.py as pf
from constants import *

def calc_coeff(G, x, y, p, q):
    b = ((q - y - G*(p*p - x*x))/(p-x))
    c = (q - G*p*p - b*p)

    # assert (G * x * x) + (b * x) + c == y
    # assert (G * p * p) + (b * p) + c == q
    
    return b, c
    
    
def length_func(x0, y0, x1, y1):
    length = pylab.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    return length
    
def get_theta(x0, y0, x1, y1):
    theta = pylab.arctan((abs(y1 - y0))/(abs(x1 - x0)))
    return theta

def curve_length(G, x0, y0, p, q):        
    b, c = calc_coeff(G, x0, y0, p, q)
    def differential(x):
        return pylab.sqrt(1 + (2*G*x + b)**2)
    curve, tolerance = integrate.quad(differential, min(x0, p), max(x0, p))
    return curve
    
        
def distance_from_base(root_distance, x, y, x1, y1):
    pair1 = [x, y]
    pair2 = [x1, y1]
    distance = math.dist(pair1, pair2)
    if(x,y) == (x1, y1):
        assert distance == 0
    return distance + root_distance

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


def calc_pareto_front(fname):
    G = rar.read_arbor_full(fname)
    delta = 0.01
    epsilon = 0.1
    min_alpha = 0.0
    max_alpha = 0.10
    min_gravity = 0
    max_gravity = 0.1
    values = []
    for alpha in pylab.arange(min_alpha, max_alpha + delta, delta):
        for g in pylab.arange(min_gravity, max_gravity + epsilon, epsilon):
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
            values.append((alpha, g, wiring, delay, point_dist))
            
    return values
    
def main():
    #fname = '%s/plant_gravitropism.csv' % ARCHITECTURE_DIR
    #first_time = not os.path.exists(fname)
    path = '%s/plant_gravitropism' $ RESULTS_DIR
    if not os.path.exists(
    for arbor in os.listdir(RECONSTRUCTIONS_DIR):

    
    
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
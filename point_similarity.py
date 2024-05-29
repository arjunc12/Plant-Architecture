import read_arbor_reconstruction as rar
import pareto_functions as pf
import plotly
import matplotlib
import networkx as nx
import plotly.graph_objects as go
import utils as ut
import math
import pylab
import os
from constants import *

def create_graphs(fname, alpha):
    G = rar.read_arbor_full(fname)
    G_opt = pf.opt_arbor(G, alpha)
    return G, G_opt
    
    
def create_dict(G, G_opt) :
    G_dict = {}
    for coordinate in list(G.nodes):
        G_dict[coordinate] = coordinate
        
    G_opt_dict = {}
    for coordinate in list(G_opt.nodes):
        G_opt_dict[coordinate] = coordinate
        
    return G_dict, G_opt_dict


def line_equation(G, G_opt, main_root, lateral_tip) :

    G_dict, G_opt_dict = create_dict(G, G_opt)
    
    pt1 = G_opt_dict[main_root]
    pt2 = G_opt_dict[lateral_tip]

    x1, y1 = pt1
    x2, y2 = pt2
    m = (y2 - y1) / (x2 - x1)
    
    y_int = y1 - m * x1

    return m, y_int

## maybe rename
def fill_lateral_root(G, G_opt, main_root, lateral_tip) :

    ## This method uses the lateral tip and main root to fill in points of the lateral root
    ## in order to perform distance calculation
  
    m, y_int = line_equation(G, G_opt, main_root, lateral_tip)

    observed = {}
    optimal = {}
    observed, optimal = create_dict(G, G_opt)
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
    for x in x_coords:
        added_nodes.append(m * x + y_int)

    return added_nodes, y_coords


def calculate_distance(G, G_opt, lateral_tip):
    
    main_root = modified_closest_main_root_point(G_opt, lateral_tip)
    
    opt_y_coords, actual_y_coords = fill_lateral_root(G, G_opt, main_root, lateral_tip)

    distances = []
    
    for x in range(len(opt_y_coords)):
        diff_square = (opt_y_coords[x] - actual_y_coords[x]) ** 2
        distances.append(diff_square)

    return sum(distances)

def modified_closest_main_root_point(G, lateral_root_tip):
    '''
    Given an arbor and a lateral root tip, find the closest point on the main root
    '''
    curr = lateral_root_tip
    while not ut.is_on_main_root(G, curr):
        curr = list(G.neighbors(curr))[0]
    return curr
    
    
def cumulative_distance(fname, alpha):
    G, G_opt = create_graphs(fname, alpha)
    results = []
    sum_of_distances = 0
    for node in G :
        if (G.nodes[node]['label'] == "lateral root tip"):
            sum_of_distances = calculate_distance(G, G_opt, node)
            results.append(sum_of_distances)
    return sum(results)
    
def find_best_distance(fname):
    results = []
    best_alpha = math.inf
    best_distance = math.inf
    min_alpha = 0
    delta = 0.01
    max_alpha = 1
    for alpha in pylab.arange(min_alpha, max_alpha + delta, delta):
        distance = cumulative_distance(fname, alpha)
        if distance < best_distance:
            best_distance = distance
            best_alpha = alpha
        results.append(distance)
    return min(results), best_alpha

def main():
    fname = '%s/point_similarity.csv' % ARCHITECTURE_DIR
    first_time = not os.path.exists(fname)
    
    with open(fname, 'a') as f:
        if first_time:
            f.write('arbor name, distance squared, alpha\n')
            
        for arbor in os.listdir(RECONSTRUCTIONS_DIR):
            distance, alpha = find_best_distance(arbor)
            arbor_name = arbor.strip('.csv')
            
            print("Calculating distances from point_similarity.py")
            print(arbor)
            f.write('%s, %f, %f\n' % (arbor_name, distance, alpha))
    

if __name__ == '__main__':
    main()

## data/architecture_data/arbor-reconstructions
## data/architecture_data/test_reconstructions
## RECONSTRUCTIONS_DIR
# ARCHITECTURE_DIR


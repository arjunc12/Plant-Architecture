import numpy as np

def main_root_edges(G):
    queue = [G.graph['main root base']

def main_root_length(G):
    total_length = 0
    for u, v in G.edges():
        if 'main root' in G.nodes[u]['label'] and 'main root' in G.nodes[u]['label']:
            total_length += g[u][v]['length']

    return total_length

def random_root_point(G):
    length = main_root_length(G)
    point_distance = np.uniform(0, length)


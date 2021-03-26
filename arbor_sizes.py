from constants import *
from scipy.spatial import ConvexHull
import os
from read_arbor_reconstruction import read_arbor_full

def arbor_volume(G):
    hull_points = []
    for u in G.nodes():
        if G.degree(u) == 1:
            hull_points.append(u)

    if len(hull_points) <= 2:
        return None
    else:
        return ConvexHull(hull_points).volume

def lateral_root_length(G, tip):
    visited = set()
    queue = [tip]
    root_length = 0
    while len(queue) > 0:
        curr = queue.pop()

        assert G.nodes[curr]['label'] in ['lateral root', 'lateral root tip']

        assert curr not in visited
        visited.add(curr)

        for n in G.neighbors(curr):
            if n not in visited:
                root_length += G[curr][n]['length']
                if G.nodes[n]['label'] in ['lateral root', 'lateral root tip']:
                    queue.append(n)

    return root_length

def total_lateral_length(G):
    total = 0
    for u in G.nodes():
        if G.nodes[u]['label'] == 'lateral root tip':
            total += lateral_root_length(G, u) ** 2

    return total

def arbor_exploration(G):
    exploration = 0
    main_root_x = G.graph['main root base'][0]
    
    for u in G.nodes():
        if G.nodes[u]['label'] == 'lateral root tip':
            x = u[0]
            exploration += (x - main_root_x)** 2

    return exploration

def lateral_root_tips(G):
    tips = 0
    for u in G.nodes():
        if G.nodes[u]['label'] == 'lateral root tip':
            tips += 1

    return tips

def arbor_tips(G):
    tips = 0
    for u in G.nodes():
        if G.degree(u) == 1:
            tips += 1
    return tips

def write_arbor_sizes():
    with open('%s/arbor_sizes.csv' % STATISTICS_DIR, 'w') as sizes_file:
        sizes_file.write('arbor name, lateral roots, convex hull volume, total lateral length, exploration factor\n')
        for reconstruction in os.listdir(RECONSTRUCTIONS_DIR):
            print(reconstruction)
            write_items = []
            
            G = read_arbor_full(reconstruction)
            write_items.append(G.graph['arbor name'])
            
            tips = lateral_root_tips(G)
            write_items.append(tips)

            volume = arbor_volume(G)
            if volume == None:
                continue
            write_items.append(volume)

            lateral_length = total_lateral_length(G)
            write_items.append(lateral_length)

            exploration = arbor_exploration(G)
            write_items.append(exploration)

            write_items = map(str, write_items)
            write_items = ', '.join(write_items)

            sizes_file.write('%s\n' % write_items)

def main():
    write_arbor_sizes()

if __name__ == '__main__':
    main()

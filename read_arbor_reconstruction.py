import networkx as nx
from scipy.spatial.distance import euclidean
from utils import connect_insertions
from constants import RECONSTRUCTIONS_DIR, DRAWINGS_DIR
import os
import pylab
import pandas as pd

NODE_SIZE = {'main root' : 50, 'lateral root' : 30, 'insertion point' : 10}

def read_arbor(fname):
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
        G.add_edge(p1, p2)
        if order == 0:
            G.node[p1]['label'] = 'main root'
        elif order == 1:
            G.node[p1]['label'] = 'lateral root'

        G.node[p2]['label'] = 'insertion point'
        G[p1][p2]['length'] = euclidean(p1, p2)


    connect_insertions(G)

    return G

def draw_arbor(G, outdir):
    pos = {}
    nodelist = []
    node_size = []

    xmin = float("inf")
    xmax = float("-inf")
    ymin = float("inf")
    ymax = float("-inf")

    for u in G.nodes():
        x, y = u
        pos[u] = (x, y)

        xmin = min(xmin, x)
        xmax = max(xmax, x)
        ymin = min(ymin, y)
        ymax = max(ymax, y)

        nodelist.append(u)
        node_size.append(NODE_SIZE[G.node[u]['label']])

    pylab.figure()
    nx.draw_networkx_nodes(G, pos=pos, nodelist=nodelist, node_color='k', node_size=node_size)
    nx.draw_networkx_edges(G, pos=pos, width=5, edge_color='g')
    pylab.draw()

    #pylab.xlim(xmin - 0.1, 1, xmax + 0.1)
    #pylab.ylim(xmin - 0.1, xmax + 0.1)
    ax = pylab.gca()
    ax.axis("off")

    os.system('mkdir -p %s' % outdir)
    pylab.savefig('%s/%s.pdf' % (outdir, G.graph['arbor name']), format='pdf')
    pylab.close()

def main():
    fname = '060_1_C_day2.csv'
    G = read_arbor(fname)
    draw_arbor(G, DRAWINGS_DIR)

if __name__ == '__main__':
    main()

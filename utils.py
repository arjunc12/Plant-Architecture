from scipy.spatial.distance import euclidean
import networkx as nx
import pylab
import os

NODE_SIZE = {'main root' : 30, 'lateral root' : 10, 'insertion point' : 10, 'lateral root tip' : 30}
NODE_COLOR = {'main root' : 'm', 'lateral root' : 'b', 'insertion point' : 'r', 'lateral root tip' : 'k'}

def connect_points(G, u, v):
    G.add_edge(u, v)
    G[u][v]['length'] = euclidean(u, v)

def connect_insertions(G):
    insertions = []
    for u in G.nodes():
        if G.node[u]['label'] in ['main root', 'insertion point']:
            insertions.append(u)

    insertions = sorted(insertions)

    for i in range(len(insertions) - 1):
        insertion1 = insertions[i]
        insertion2 = insertions[i + 1]
        assert G.has_node(insertion1)
        assert G.has_node(insertion2)
        assert not G.has_edge(insertion1, insertion2)
        connect_points(G, insertion1, insertion2)

def draw_arbor(G, outdir):
    pos = {}
    nodelist = []
    node_size = []
    node_color = []

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
        node_color.append(NODE_COLOR[G.node[u]['label']])

    pylab.figure()
    nx.draw_networkx_nodes(G, pos=pos, nodelist=nodelist, node_color=node_color, node_size=node_size)
    nx.draw_networkx_edges(G, pos=pos, width=5, edge_color='g')
    pylab.draw()

    #pylab.xlim(xmin - 0.1, 1, xmax + 0.1)
    #pylab.ylim(xmin - 0.1, xmax + 0.1)
    ax = pylab.gca()
    ax.axis("off")

    os.system('mkdir -p %s' % outdir)
    pylab.savefig('%s/%s.pdf' % (outdir, G.graph['arbor name']), format='pdf')
    pylab.close()

def toy_network():
    root = (0, -1)
    insertion1 = (0, 1)
    lateral1 = (1, 1)

    G = nx.Graph()

    for u, label in zip([root, insertion1, lateral1],\
                        ['main root', 'insertion point', 'lateral root']):
        G.add_node(u)
        G.node[u]['label'] = label

    G.graph['main root'] = root

    connect_insertions(G)

    connect_points(G, insertion1, lateral1)

    G.graph['arbor name'] = 'toy-network'

    return G

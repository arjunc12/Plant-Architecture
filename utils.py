from scipy.spatial.distance import euclidean
import networkx as nx
import pylab
import os
import re

NODE_SIZE = {'main root' : 30, 'main root base' : 30, 'lateral root' : 10, 'insertion point' : 10, 'lateral root tip' : 30}
NODE_COLOR = {'main root' : 'm' , 'main root base' : 'k', 'lateral root' : 'b', 'insertion point' : 'r', 'lateral root tip' : 'k'}

def closest_main_root_point(G, lateral_root_tip):
    '''
    Given an arbor and a lateral root tip, find the closest point on the main root
    '''
    curr = lateral_root_tip
    while not is_on_main_root(G, curr):
        neighbors = G.neighbors(curr)
        assert len(neighbors) == 1
        curr = neighbors[0]

    return curr

def relabel_lateral_root_tips(G):
    '''
    relabels all lateral root tips
    '''
    # variables to keep track of the lowest point on the main root
    for u in G.nodes():
        if G.nodes[u]['label'] == 'lateral root' and G.degree(u) == 1:
            # degree 1 lateral root is a tip
            G.nodes[u]['label'] = 'lateral root tip'

def connect_points(G, u, v):
    G.add_edge(u, v)
    G[u][v]['length'] = euclidean(u, v)

def is_on_main_root(G, u):
    return any(re.findall(r'(main root.*)|(insertion point.*)', G.nodes[u]['label']))

def sort_by_y_coord(points):
    return sorted(points, key = lambda p: p[1])

def connect_main_root(G):
    '''
    Method to connect every insertion point to the previous insertion
    '''
    root_points = []
    for u in G.nodes():
        if is_on_main_root(G, u):
            insertions.append(u)

    root_points = sort_by_y_coord(root_points)

    for i in range(len(root_points) - 1):
        root_point1 = root_points[i]
        root_point2 = root_points[i + 1]
        assert G.has_node(root_point1)
        assert G.has_node(root_point2)
        assert not G.has_edge(root_point1, root_point2)
        connect_points(G, root_point1, root_point2)

def draw_arbor(G, outdir):
    pos = {}
    nodelist = []
    node_size = []
    node_color = []

    # variables for setting the bounds of the drawing
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
        node_size.append(NODE_SIZE[G.nodes[u]['label']])
        node_color.append(NODE_COLOR[G.nodes[u]['label']])

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

    root_base = (0, 0)
    root1 = (0, 1)
    root2 = (0, 2)
    lateral = (4, 3)
    lateral2 = (-1, 5)

    G = nx.Graph()

    for u, label in zip([root_base, root1, root2, lateral, lateral2],\
                        ['main root', 'main root', 'main root', 'lateral root', 'lateral root']):
        G.add_node(u)
        G.nodes[u]['label'] = label

    connect_points(G, root_base, root1)
    connect_points(G, root1, root2)
    connect_points(G, root_base, lateral)
    connect_points(G, root_base, lateral2)

    G.nodes[root_base]['label'] = 'main root base'
    relabel_lateral_root_tips(G)

    G.graph['arbor name'] = 'toy-network'

    return G

def image_metadata(image):
    image = image.strip('_')
    image = image.strip('.rsml')

    image_items = image.split('_')

    day = image_items[1]
    day = day.strip('day')

    picture_num = image_items[-1]

    return day, picture_num

def root_name_metadata(root_name):
    root_name_items = root_name.split("_")

    genotype = root_name_items[0]
    replicate = root_name_items[1]
    condition = root_name_items[2]

    return genotype, replicate, condition

def get_day(image):
    image = image.strip('_')
    image_items = image.split('_')
    return image_items[1]

def arbor_name(image, main_root_name):
    day = get_day(image)
    return '%s_%s' % (main_root_name, day)

def get_experiment(fname):
    fname_items = fname.split('_')

    pimpi = fname_items[0]
    big = fname_items[1]

    return '%s_%s' % (pimpi, big)

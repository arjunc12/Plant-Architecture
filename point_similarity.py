## need to compute distances between y values of actual and optimal
## add up those distances

## creates dictionaries for both graphs
'''
def create_dict(G, G_opt) :
    G_dict = {}
    for coordinate in list(G.nodes):
        G_dict[coordinate] = coordinate
        
    G_opt_dict = {}
    for coordinate in list(G_opt.nodes):
        G_opt_dict[coordinate] = coordinate
    
    print(G_opt_dict)
'''

def line_equation(main_root, lateral_tip) :
    G_dict = {}
    for coordinate in list(G.nodes):
        G_dict[coordinate] = coordinate
        
    G_opt_dict = {}
    for coordinate in list(G_opt.nodes):
        G_opt_dict[coordinate] = coordinate
    
    pt1 = G_opt_dict[main_root]
    pt2 = G_opt_dict[lateral_tip]

    x1, y1 = pt1
    x2, y2 = pt2
    print(x1)
    print(y1)
    m = (y2 - y1) / (x2 - x1)
   ## print(m)

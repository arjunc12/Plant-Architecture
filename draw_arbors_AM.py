import math
import networkx as nx
import plotly.graph_objs as go
import pylab
import plant_gravitropism as pg

def get_observed_lateral_segments(arbor):
    """
    Trace all lateral roots from tip to main root.
    Nodes are tuples (x, y).
    """
    segments = []
    tips = [n for n in arbor.nodes if arbor.nodes[n]["label"] == "lateral root tip"]

    for tip in tips:
        curr = tip
        prev = None
        while True:
            neighbors = list(arbor.neighbors(curr))
            if prev is not None:
                neighbors = [n for n in neighbors if n != prev]

            if len(neighbors) == 0:
                break  # end of lateral root

            next_node = neighbors[0]
            segments.append((curr, next_node))
            prev, curr = curr, next_node

            if arbor.nodes[curr]["label"].startswith("main root"):
                break

    return segments

def get_line_segment_drawings(line_segments, color="gray"):
    """Convert line segments into Plotly Scatter objects."""
    traces = []
    for seg in line_segments.values():
        (x0, y0), (x1, y1) = seg  # node IDs are tuples
        traces.append(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=color, width=4),
            showlegend=False
        ))
    return traces

def get_lateral_segment_drawings(lateral_segments, color="lightgray"):
    traces = []
    for seg in lateral_segments:
        (x0, y0), (x1, y1) = seg
        traces.append(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=color, width=2),
            showlegend=False
        ))
    return traces

def get_tip_drawings(lat_tips, color="orange"):
    return [go.Scatter(x=[tip[0]], y=[tip[1]],
                       mode="markers",
                       marker=dict(color=color),
                       showlegend=False)
            for tip in lat_tips]

def get_opt_to_pq_drawings(G, final, color="blue"):
    drawings = []
    for result in final:
        x0, y0 = result[4], result[5]
        p, q = result[6], result[7]
        if G == 0:
            x_coords, y_coords = [p, x0], [q, y0]
        else:
            b, c = pg.calc_coeff(G, x0, y0, p, q)
            x_coords = pylab.linspace(min(p, x0), max(p, x0))
            y_coords = G * x_coords**2 + b*x_coords + c
        drawings.append(go.Scatter(
            x=x_coords, y=y_coords,
            mode="lines",
            line=dict(color=color),
            showlegend=False
        ))
    return drawings

def create_graphs(fname, G, alpha):
    """
    Load observed arbor and compute optimized results for given G and alpha.
    """
    arbor = pg.rar.read_arbor_full(fname)
    results = pg.arbor_best_cost(arbor, G, alpha)
    return arbor, results

def plot_arbors(fname, G, alpha, show_observed=True, show_optimized=True, paper=False, save_fname=None):
    arbor, results = create_graphs(fname, G, alpha)

    wiring, delay, total_orthogonal, total_sq_orthogonal = pg.evaluate_parameters(fname, G, alpha)

    print(f"\n→ G = {G}, alpha = {alpha}")
    print(f"Wiring cost: {wiring:.4f}")
    print(f"Conduction delay: {delay:.4f}\n")
    print(f"Total orthogonal distance: {total_orthogonal:.4f}")
    print(f"Total squared orthogonal distance: {total_sq_orthogonal:.4f}\n")

    fig = go.Figure()

    if show_observed:
        main_segments = pg.get_main_root_segments(arbor)
        # convert list of tuples to dict for get_line_segment_drawings
        main_segments_dict = {i: seg for i, seg in enumerate(main_segments)}
        for trace in get_line_segment_drawings(main_segments_dict, color="black"):
            fig.add_trace(trace)

        lateral_segments = get_observed_lateral_segments(arbor)
        for trace in get_lateral_segment_drawings(lateral_segments, color="green"):
            fig.add_trace(trace)

        lat_tips = [n for n in arbor.nodes if arbor.nodes[n]["label"] == "lateral root tip"]
        for trace in get_tip_drawings(lat_tips, color="orange"):
            fig.add_trace(trace)

        base_node = arbor.graph['main root base']
        fig.add_trace(go.Scatter(
            x=[base_node[0]], y=[base_node[1]],
            mode="markers",
            marker=dict(color="purple", size=30),
            name="Main root base"
        ))

    if show_optimized:
        for trace in get_opt_to_pq_drawings(G, results, color="blue"):
            fig.add_trace(trace)

    fig.update_layout(
        title=f"Arbor: {fname}   |   G={G}, alpha={alpha}",
        annotations=[
            dict(
                text="",
                xref="paper", yref="paper",
                x=0.5, y=-0.1,
                showarrow=False,
                font=dict(size=14)
            )
        ],
        xaxis_title="X",
        yaxis_title="Y",
        yaxis_autorange="reversed",
        width=850,
        height=700,
        margin=dict(t=80, b=80)
    )
    
    if paper:
        fig.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            annotations=[], 
            title_text="", 
            showlegend=False
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)


    fig.show()
    
    if save_fname != None:
        print("saving fig to " + save_fname)
        fig.write_image(save_fname)
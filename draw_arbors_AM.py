"""Draw Arbor reconstructions whose graph nodes are unique numeric IDs.

Geometry is always read from ``arbor.nodes[node_id]["coords"]``. This keeps
separate graph nodes separate even when they occupy the same coordinates.
"""

import numpy as np
import plotly.graph_objs as go
import pylab

import plant_gravitropism as pg


def get_coords(arbor, node_id):
    """Return the coordinates stored for an ID-based graph node."""
    return arbor.nodes[node_id]["coords"]


def get_observed_lateral_segments(arbor):
    """Trace lateral roots from their tips to the main root as node-ID pairs."""
    segments = []
    tips = [node for node in arbor.nodes if arbor.nodes[node]["label"] == "lateral root tip"]

    for tip in tips:
        current = tip
        previous = None
        while True:
            neighbors = list(arbor.neighbors(current))
            if previous is not None:
                neighbors = [node for node in neighbors if node != previous]
            if not neighbors:
                break

            next_node = neighbors[0]
            segments.append((current, next_node))
            previous, current = current, next_node
            if arbor.nodes[current]["label"].startswith("main root"):
                break

    return segments


def get_line_segment_drawings(arbor, line_segments, color="gray"):
    """Convert ID-based main-root segments to Plotly traces."""
    traces = []
    for node_a, node_b in line_segments.values():
        x0, y0 = get_coords(arbor, node_a)
        x1, y1 = get_coords(arbor, node_b)
        traces.append(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(color=color, width=4), showlegend=False,
            )
        )
    return traces


def get_lateral_segment_drawings(arbor, lateral_segments, color="lightgray"):
    """Convert ID-based lateral-root segments to Plotly traces."""
    traces = []
    for node_a, node_b in lateral_segments:
        x0, y0 = get_coords(arbor, node_a)
        x1, y1 = get_coords(arbor, node_b)
        traces.append(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(color=color, width=2), showlegend=False,
            )
        )
    return traces


def get_tip_drawings(arbor, lateral_tips, color="orange"):
    return [
        go.Scatter(
            x=[get_coords(arbor, tip)[0]], y=[get_coords(arbor, tip)[1]],
            mode="markers", marker=dict(color=color), showlegend=False,
        )
        for tip in lateral_tips
    ]


def get_opt_to_pq_drawings(G, final, color="blue"):
    """Draw optimal curves; optimization results already contain coordinates."""
    drawings = []
    for result in final:
        x0, y0 = result[4], result[5]
        p, q = result[6], result[7]
        if G == 0:
            x_coords, y_coords = [p, x0], [q, y0]
        else:
            b, c = pg.calc_coeff(G, x0, y0, p, q)
            x_coords = pylab.linspace(min(p, x0), max(p, x0))
            y_coords = G * x_coords**2 + b * x_coords + c
        drawings.append(
            go.Scatter(
                x=x_coords, y=y_coords, mode="lines",
                line=dict(color=color), showlegend=False,
            )
        )
    return drawings


def get_insertion_point_drawings(arbor, insertion_points, color="blue"):
    return [
        go.Scatter(
            x=[get_coords(arbor, point)[0]], y=[get_coords(arbor, point)[1]],
            mode="markers", marker=dict(color=color, size=8), showlegend=False,
        )
        for point in insertion_points
    ]


def get_lateral_nodes(lateral_segments):
    """Return unique node IDs occurring in lateral-root segments."""
    nodes = set()
    for node_a, node_b in lateral_segments:
        nodes.add(node_a)
        nodes.add(node_b)
    return list(nodes)


def get_lateral_node_drawings(arbor, lateral_nodes, color="white"):
    return [
        go.Scatter(
            x=[get_coords(arbor, node)[0]], y=[get_coords(arbor, node)[1]],
            mode="markers", marker=dict(color=color), showlegend=False,
        )
        for node in lateral_nodes
    ]


def get_lateral_insertion_points(lateral_segments, arbor):
    """Return the unique main-root node IDs reached by lateral roots."""
    insertion_points = set()
    for _, node_b in lateral_segments:
        if arbor.nodes[node_b]["label"].startswith("main root"):
            insertion_points.add(node_b)
    return list(insertion_points)


def get_main_root_segments(arbor):
    """Return ordered main-root segments as pairs of node IDs."""
    return pg.get_main_root_segments(arbor)


def compute_main_root_base_distances(arbor):
    """Map each main-root node ID to its distance from the root base."""
    base = arbor.graph["main root base"]
    distances = {base: 0}
    for node_a, node_b in get_main_root_segments(arbor):
        distances[node_b] = distances[node_a] + arbor[node_a][node_b]["length"]
    return distances


def get_insertion_segment(arbor, lateral_tip, segments):
    """Find the main-root segments available to an ID-based lateral tip."""
    visited = set()
    queue = [lateral_tip]
    insertion_node = None

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        if arbor.nodes[node]["label"] in ("main root", "main root base"):
            insertion_node = node
            break
        queue.extend(neighbor for neighbor in arbor.neighbors(node) if neighbor not in visited)

    if insertion_node is None:
        raise ValueError(f"No main-root node found from lateral tip {lateral_tip}")

    valid_segments = []
    for segment in segments:
        valid_segments.append(segment)
        if insertion_node in segment:
            break
    return valid_segments


def optimize_tip(arbor, tip_id, segments, base_distances, alpha, G):
    """Optimize one ID-based lateral tip after converting it to coordinates."""
    tip_x, tip_y = get_coords(arbor, tip_id)
    results = []

    for node_a, node_b in segments:
        x0, y0 = get_coords(arbor, node_a)
        x1, y1 = get_coords(arbor, node_b)
        base_distance = base_distances[node_a]

        if pg.is_between(x0, tip_x, x1) or pg.OPTIMIZATION_METHOD == "brute_force":
            result = pg.find_best_cost_brute_force(
                alpha, G, base_distance, x0, y0, x1, y1, tip_x, tip_y
            )
        elif pg.OPTIMIZATION_METHOD == "brent":
            result = pg.find_best_cost_brent(
                alpha, G, base_distance, x0, y0, x1, y1, tip_x, tip_y
            )
        else:
            result = pg.find_best_cost_analytical(
                alpha, G, base_distance, x0, y0, x1, y1, tip_x, tip_y
            )
        results.append(result)

    return min(results)


def collect_lateral_root_segments(arbor, lateral_tip):
    """Return coordinate segments along an ID-based lateral root."""
    node_path = pg.collect_lateral_root_points(arbor, lateral_tip)
    return [
        (*get_coords(arbor, node_path[index]), *get_coords(arbor, node_path[index + 1]))
        for index in range(len(node_path) - 1)
    ]


def calculate_orthogonal_errors(gravity, arbor, main_root_point, lateral_tip):
    """Measure lateral-root error using coordinates stored on graph nodes."""
    px, py = main_root_point
    tip_x, tip_y = get_coords(arbor, lateral_tip)
    segments = collect_lateral_root_segments(arbor, lateral_tip)
    if not segments:
        return 0.0, 0.0

    b, c = pg.calc_coeff(gravity, px, py, tip_x, tip_y)
    all_xs = []
    all_ys = []
    for x0, y0, x1, y1 in segments:
        t_values = np.linspace(0, 1, 100, endpoint=False)
        all_xs.append(x0 + t_values * (x1 - x0))
        all_ys.append(y0 + t_values * (y1 - y0))
    all_xs.append(np.array([segments[-1][2]]))
    all_ys.append(np.array([segments[-1][3]]))

    observed_x = np.concatenate(all_xs)
    observed_y = np.concatenate(all_ys)
    curve_x = np.linspace(min(px, tip_x), max(px, tip_x), 1000)
    curve_y = gravity * curve_x**2 + b * curve_x + c
    distances = np.sqrt(
        (observed_x[:, np.newaxis] - curve_x[np.newaxis, :]) ** 2
        + (observed_y[:, np.newaxis] - curve_y[np.newaxis, :]) ** 2
    ).min(axis=1)
    return distances.sum(), (distances**2).sum()


def evaluate_parameters_draw(arbor, G, alpha):
    """Evaluate an already-loaded Arbor graph with ID-based nodes."""
    main_segments = get_main_root_segments(arbor)
    base_distances = compute_main_root_base_distances(arbor)
    lateral_tips = [
        node for node in arbor.nodes if arbor.nodes[node]["label"] == "lateral root tip"
    ]
    results = [
        optimize_tip(
            arbor, tip, get_insertion_segment(arbor, tip, main_segments),
            base_distances, alpha, G,
        )
        for tip in lateral_tips
    ]
    errors = [
        calculate_orthogonal_errors(G, arbor, (result[4], result[5]), tip)
        for result, tip in zip(results, lateral_tips)
    ]
    main_root_wiring = sum(
        arbor[node_a][node_b]["length"] for node_a, node_b in main_segments
    )
    return (
        sum(result[1] for result in results) + main_root_wiring,
        sum(result[2] for result in results),
        sum(error[0] for error in errors),
        sum(error[1] for error in errors),
    )


def plot_arbors(arbor, G, alpha, show_observed=True, show_insertion_points=True, show_lateral_nodes=True, paper=False, save_fname=None):
    """Render an ID-based Arbor graph and report its optimization metrics."""
    arbor_name = arbor.graph.get("arbor name", "toy arbor")
    wiring, delay, total_orthogonal, total_sq_orthogonal = evaluate_parameters_draw(
        arbor, G, alpha
    )

    print(f"\n→ G = {G}, alpha = {alpha}")
    print(f"Wiring cost: {wiring:.4f}")
    print(f"Conduction delay: {delay:.4f}\n")
    print(f"Total orthogonal distance: {total_orthogonal:.4f}")
    print(f"Total squared orthogonal distance: {total_sq_orthogonal:.4f}\n")

    fig = go.Figure()
    if show_observed:
        main_segments = get_main_root_segments(arbor)
        main_segments_dict = {index: segment for index, segment in enumerate(main_segments)}
        for trace in get_line_segment_drawings(arbor, main_segments_dict, color="black"):
            fig.add_trace(trace)

        lateral_segments = get_observed_lateral_segments(arbor)
        for trace in get_lateral_segment_drawings(arbor, lateral_segments, color="green"):
            fig.add_trace(trace)
        
        if show_lateral_nodes:
            lateral_nodes = get_lateral_nodes(lateral_segments)
            for trace in get_lateral_node_drawings(arbor, lateral_nodes, color="white"):
                fig.add_trace(trace)

        lateral_tips = [
            node for node in arbor.nodes if arbor.nodes[node]["label"] == "lateral root tip"
        ]
        for trace in get_tip_drawings(arbor, lateral_tips, color="orange"):
            fig.add_trace(trace)

        insertion_points = get_lateral_insertion_points(lateral_segments, arbor)
        for trace in get_insertion_point_drawings(arbor, insertion_points, color="blue"):
            fig.add_trace(trace)

        base_node = arbor.graph["main root base"]
        base_x, base_y = get_coords(arbor, base_node)
        fig.add_trace(
            go.Scatter(
                x=[base_x], y=[base_y], mode="markers",
                marker=dict(color="purple", size=30), name="Main root base",
            )
        )

    fig.update_layout(
        title=f"Arbor: {arbor_name}   |   G={G}, alpha={alpha}",
        annotations=[dict(text="", xref="paper", yref="paper", x=0.5, y=-0.1,
                          showarrow=False, font=dict(size=14))],
        xaxis_title="X", yaxis_title="Y", yaxis_autorange="reversed",
        width=850, height=700, margin=dict(t=80, b=80),
    )
    if paper:
        fig.update_layout(xaxis_title=None, yaxis_title=None, annotations=[],
                          title_text="", showlegend=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

    fig.show()
    if save_fname is not None:
        print("saving fig to " + save_fname)
        fig.write_image(save_fname)

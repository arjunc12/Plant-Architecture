import os
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import euclidean
from read_arbor_reconstruction import read_arbor_full
from constants import METADATA_DIR, RECONSTRUCTIONS_DIR

OUTPUT_FILE = "%s/lateral_root_sizes.csv" % METADATA_DIR


def compute_lateral_root_stats(G):
    """
    Compute lateral root statistics for a single arbor.

    Returns
    -------
    dict with:
        - lateral_root_tips: number of lateral root tips
        - lateral_root_points: total number of lateral root nodes (including tips)
        - lateral_root_segments: total number of lateral root edges
        - total_lateral_length: sum of all lateral root edge lengths
        - convex_hull_area: area of convex hull of all arbor nodes
    """
    lateral_root_tips = 0
    lateral_root_points = 0
    lateral_root_segments = 0
    total_lateral_length = 0.0

    # Count lateral root nodes
    lateral_nodes = set()
    for node, data in G.nodes(data=True):
        label = data.get('label', '').lower()
        if label == 'lateral root tip':
            lateral_root_tips += 1
            lateral_root_points += 1
            lateral_nodes.add(node)
        elif label == 'lateral root':
            lateral_root_points += 1
            lateral_nodes.add(node)

    # Count lateral root edges and sum lengths
    for u, v, data in G.edges(data=True):
        u_label = G.nodes[u].get('label', '').lower()
        v_label = G.nodes[v].get('label', '').lower()
        # Edge is a lateral root edge if either endpoint is a lateral root node
        if u in lateral_nodes or v in lateral_nodes:
            lateral_root_segments += 1
            length = data.get('length', euclidean(u, v))
            total_lateral_length += length

    # Convex hull area of all arbor nodes
    all_points = np.array(list(G.nodes()))
    if len(all_points) >= 3:
        try:
            hull = ConvexHull(all_points)
            convex_hull_area = hull.volume  # in 2D, volume = area
        except Exception:
            # Degenerate case — all points collinear
            convex_hull_area = 0.0
    else:
        convex_hull_area = 0.0

    return {
        'lateral_root_tips':     lateral_root_tips,
        'lateral_root_points':   lateral_root_points,
        'lateral_root_segments': lateral_root_segments,
        'total_lateral_length':  total_lateral_length,
        'convex_hull_area':      convex_hull_area,
    }


def main():
    results = []

    for filename in sorted(os.listdir(RECONSTRUCTIONS_DIR)):
        filepath = os.path.join(RECONSTRUCTIONS_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        print(f"Processing {filename}")

        try:
            G = read_arbor_full(filename)
            arbor_name = G.graph.get('arbor name', filename)
            stats = compute_lateral_root_stats(G)
            results.append({
                'arbor name':            arbor_name,
                'lateral roots':         stats['lateral_root_tips'],
                'lateral root points':   stats['lateral_root_points'],
                'lateral root segments': stats['lateral_root_segments'],
                'total lateral length':  round(stats['total_lateral_length'], 6),
                'convex hull area':      round(stats['convex_hull_area'], 6),
            })
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    # Write results
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    cols = ['arbor name', 'lateral roots', 'lateral root points',
            'lateral root segments', 'total lateral length', 'convex hull area']

    with open(OUTPUT_FILE, 'w') as f:
        f.write(', '.join(cols) + '\n')
        for row in results:
            f.write(', '.join(str(row[c]) for c in cols) + '\n')

    print(f"\nWrote {len(results)} rows to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
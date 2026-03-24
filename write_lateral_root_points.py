import os
import csv
from read_arbor_reconstruction import read_arbor_full
from constants import METADATA_DIR, RECONSTRUCTIONS_DIR

OUTPUT_FILE = "%s/lateral_root_points.csv" % METADATA_DIR

def count_lateral_root_points(G):
    """
    Given a NetworkX graph G, count:
    - number of lateral root tips
    - number of all lateral root points (including tips)
    """
    lateral_root_tips = 0
    lateral_root_points = 0

    for _, data in G.nodes(data=True):
        label = data.get("label", "").lower()

        if label == "lateral root tip":
            lateral_root_tips += 1
            lateral_root_points += 1
        elif label == "lateral root":
            lateral_root_points += 1

    return lateral_root_tips, lateral_root_points


def main():
    results = []

    for filename in os.listdir(RECONSTRUCTIONS_DIR):
        print(filename)
        filepath = os.path.join(RECONSTRUCTIONS_DIR, filename)

        # Skip non-files (e.g., directories, hidden files)
        if not os.path.isfile(filepath):
            continue

        try:
            G = read_arbor_full(filename)

            arbor_name = G.graph.get("arbor name", filename)

            lateral_root_tips, lateral_root_points = count_lateral_root_points(G)

            results.append([
                arbor_name,
                lateral_root_tips,
                lateral_root_points
            ])

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Write results to CSV
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, mode="w", newline="") as f:
        f.write("arbor name, lateral roots, lateral root points\n")
        for row in results:
            f.write(", ".join(map(str, row)) + "\n")

    print(f"Output written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
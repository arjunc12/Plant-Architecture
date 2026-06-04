import csv
import math
import networkx as nx
import numpy as np
from pathlib import Path
import pareto_functions as pf
import plotly.graph_objs as go
import pylab
import plant_gravitropism as pg
import read_arbor_reconstruction as rar


last_day_files = pg.get_last_day_files()

# Loop to generate arbor_evaluated_parameters array

alphas = np.round(np.arange(0, 1.01, 0.01), 2)
count = 0
output_dir = Path("data") / "results" / "heterogeneous_pareto_fronts"
output_dir.mkdir(parents=True, exist_ok=True)

for arbor in last_day_files:
    if rar.has_reconstruction(arbor):
        count += 1
        arbor_evaluated_parameters = []

        filepath = output_dir / arbor
        with open(filepath, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Model", "Alpha", "Wiring Cost", "Conduction Delay", "Total Orthogonal Distance", "Total Squared Orthogonal Distance"])
            
            for a in alphas:
                output = pg.evaluate_parameters(arbor, 0, a)
                writer.writerow(("optimal", a) + output)
            
            arbor_object = rar.read_arbor_full(arbor)
            writer.writerow(("observed", "") + (pf.wiring_cost(arbor_object), pf.conduction_delay(arbor_object)))
        
        print(f"{arbor} generated (File # {count}).")
    else:
        print(f"Skipped {arbor}")

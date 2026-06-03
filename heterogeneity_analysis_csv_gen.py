import csv
import math
import networkx as nx
import numpy as np
import plotly.graph_objs as go
import pylab
import plant_gravitropism as pg


last_day_files = pg.get_last_day_files()

# Create loop to generate arbor_evaluated_parameters array

for arbor in last_day_files[0:5]:
    alphas = np.round(np.arange(0, 1.01, 0.01), 2)
    arbor_evaluated_parameters = []

    for a in alphas:
        output = pg.evaluate_parameters(arbor, 0, a)

        arbor_values = ("observed", a) + output
        arbor_evaluated_parameters.append(arbor_values)
    
    filepath = r"C:\Users\alyan\Downloads\Research\Summer 2026\Plant-Architecture\heterogeneity_" + "\\" + arbor
    with open(filepath, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Model", "Alpha", "Wiring Cost", "Conduction Delay", "Total Orthogonal Distance", "Total Squared Orthogonal Distance"])
        writer.writerows(arbor_evaluated_parameters)
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
    alphas = np.arange(0, 1.01, 0.01)
    arbor_evaluated_parameters = []

    for a in alphas:
        arbor_values = pg.evaluate_parameters(arbor, 0, a)
        arbor_values.insert(0, "observed")
        arbor_values.insert(1, a)
        arbor_evaluated_parameters.append(arbor_values)
    
    filepath = r"C:\Users\alyan\Downloads\Research\Summer 2026\Plant-Architecture\heterogeneity_" + "\\" + arbor
    with open(filepath, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows([arbor_evaluated_parameters])







# 
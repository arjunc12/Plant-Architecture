import csv
import math
import networkx as nx
import numpy as np
import pareto_functions as pf
import plotly.graph_objs as go
import pylab
import plant_gravitropism as pg
import read_arbor_reconstruction as rar


last_day_files = pg.get_last_day_files()

# Create loop to generate arbor_evaluated_parameters array

# # Version 1

# for arbor in last_day_files[0:5]:
#     alphas = np.round(np.arange(0, 1.01, 0.01), 2)
#     arbor_evaluated_parameters = []

#     for a in alphas:
#         output = pg.evaluate_parameters(arbor, 0, a)

#         arbor_values = ("observed", a) + output
#         arbor_evaluated_parameters.append(arbor_values)
    
#     filepath = r"C:\Users\alyan\Downloads\Research\Summer 2026\Plant-Architecture\heterogeneity-analysis" + "\\" + arbor
#     with open(filepath, "w", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerow(["Model", "Alpha", "Wiring Cost", "Conduction Delay", "Total Orthogonal Distance", "Total Squared Orthogonal Distance"])
#         writer.writerows(arbor_evaluated_parameters)



# Version 2
alphas = np.round(np.arange(0, 1.01, 0.01), 2)
count = 0

for arbor in last_day_files[33:39]:
    if rar.has_reconstruction(arbor):
        count += 1
        arbor_evaluated_parameters = []

        filepath = r"heterogeneity-analysis" + "\\" + arbor
        with open(filepath, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Model", "Alpha", "Wiring Cost", "Conduction Delay", "Total Orthogonal Distance", "Total Squared Orthogonal Distance"])
            
            for a in alphas:
                output = pg.evaluate_parameters(arbor, 0, a)
                writer.writerow(("optimal", a) + output)
        
            writer.writerow(("observed", "") + (pf.wiring_cost(arbor), pf.conduction_delay(arbor)))
        print(f"{arbor} generated (File # {count}).")
    else:
        print(f"Skipped {arbor}")

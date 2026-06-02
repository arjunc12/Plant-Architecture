import math
import networkx as nx
import plotly.graph_objs as go
import pylab
import plant_gravitropism as pg

# VVV might need to delete later VVV
import draw_arbors_AM as draw

# --- Calculate all alpha values ( use evaluate_parameters ) ---
# acquiring last-day-files 
last_day_files = pg.get_last_day_files()
fname = last_day_files[0]
print(fname)

evaluated_arbor = pg.evaluate_parameters(fname, 0, 0)
print(f"Evaluated arbor: Wiring → {evaluated_arbor[0]}, Delay → {evaluated_arbor[1]}, Total Orthogonal → {evaluated_arbor[2]}, Total Squared Orthogonal → {evaluated_arbor[3]}")

# --- Drawing out arbors (for visualization <<< will delete this step in final pipeline) ----


# draw.plot_arbors(fname, 0, 0)


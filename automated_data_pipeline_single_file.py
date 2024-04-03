#This file with be called to automatically run the data through the data pipeline. It is created to work with a single arbor reconstruction file. The example file used is 065_3_S_day2.csv

import analyze_arbors as a_arbors
import null_models as n_m
import pareto_functions as pf
import os
from constants import *
from read_arbor_reconstruction import read_arbor_full

#This file with be called to automatically run the data through the data pipeline. It is created to work with a single arbor reconstruction file. The example file used is 065_3_S_day2.csv

import analyze_arbors as a_arbors
import null_models as n_m
import pareto_functions as pf
import os
from constants import *
from read_arbor_reconstruction import read_arbor_full

def main():
    print("auto_pipeline: analyzing arbors using analyze_arbors.py")
    a_arbors.analyze_arbors()
    a_arbors.write_scaling_dists()
    print("auto_pipeline: creating nulls models files using null_models.py")
    n_m.analyze_null_models()
    n_m.write_null_models_file()
    print("auto_pipeline: creating pareto drawings using pareto_functions.py")
    for arbor in os.listdir(RECONSTRUCTIONS_DIR):   #not sure how to grab file without for loop
        print("auto_pipeline: reconstructing arbor:",arbor)
        G = read_arbor_full(arbor)
        pf.viz_front(G)
        pf.viz_trees(G)

# return True

 
if __name__ == '__main__':
    main()

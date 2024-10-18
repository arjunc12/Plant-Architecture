import plant_gravitropism as pg
import pandas as pd
from constants import *
import os
import math
import csv

def main():
    path = '%s/gravitropism_pareto_fronts' % RESULTS_DIR
    
    fname = '%s/best_of_best.csv' % RESULTS_DIR
    first_time = not os.path.exists(fname)
    
    with open(fname, 'a') as f:
        if first_time: 
            f.write('arbor name, optimal G, optimal alpha, optimal pt distance\n')
        for pareto_front in os.listdir(path):
            min_distance = math.inf
            best_row = None
            with open('%s/%s' % (path, pareto_front)) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                count = 0
                for row in csv_reader:
                    if count != 2:
                        count += 1
                        continue
                    if float(row[5]) < min_distance:
                        min_distance = float(row[5])
                        best_row = row
            if os.path.getsize('%s/%s' % (path, pareto_front)) != 0:
                opt_G, opt_alpha, opt_dist = best_row[1], best_row[2], best_row[5]
                arbor_name = pareto_front.strip('.csv')
                print("Handling %s" % (pareto_front))
                f.write('%s, %s, %s, %s\n' % (arbor_name, opt_G, opt_alpha, opt_dist))
                
             
            
    
if __name__ == '__main__':
    main()